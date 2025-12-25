from collections import defaultdict
from datetime import date

from app.core.database import SessionLocal
from app.models import Patient, RehabilitationPlan, SuggestionLike


def get_all_patients():
    """全患者のIDと名前のリストを取得"""
    db = SessionLocal()
    try:
        patient_list = db.query(Patient.patient_id, Patient.name).order_by(Patient.patient_id).all()
        return [{"patient_id": p.patient_id, "name": p.name} for p in patient_list]
    finally:
        db.close()
# データ操作関数
def get_patient_data_for_plan(patient_id: int, db_session=None):
    """患者の基本情報と最新の計画書データ、いいね評価を取得する"""
    db = db_session if db_session else SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).one_or_none()
        if not patient:
            return None

        # 患者の基本情報を辞書に変換
        patient_data = {c.name: getattr(patient, c.name) for c in patient.__table__.columns}
        patient_data["age"] = patient.age

        # 最新の計画を取得
        latest_plan = (
            db.query(RehabilitationPlan)
            .filter(RehabilitationPlan.patient_id == patient_id)
            .order_by(RehabilitationPlan.created_at.desc())
            .first()
        )

        if latest_plan:
            # 計画データを辞書に変換してマージ
            plan_data = {c.name: getattr(latest_plan, c.name) for c in latest_plan.__table__.columns}
            patient_data.update(plan_data)
        else:
            # 計画書がない場合でも、テンプレートでエラーにならないように
            # RehabilitationPlanの全カラムをキーとして持ち、値をNoneにしたデータをマージする
            for c in RehabilitationPlan.__table__.columns:
                # patient_id など既存のキーは上書きしない
                if c.name not in patient_data:
                    patient_data[c.name] = None

        # いいね情報を取得
        likes = db.query(SuggestionLike).filter(SuggestionLike.patient_id == patient_id).all()
        # {item_key: [liked_model1, liked_model2], ...} の形式で辞書を作成
        liked_items = defaultdict(list)
        for like in likes:
            liked_items[like.item_key].append(like.liked_model)
        patient_data["liked_items"] = dict(liked_items)

        return patient_data
    finally:
        if not db_session:
            db.close()


def save_patient_master_data(form_data: dict):
    """
    患者の事実情報（マスターデータ）を保存する。
    patient_idが存在すれば更新、なければ新規作成する。
    計画書は常に新しいレコードとして作成される仕様。
    """
    from datetime import datetime

    from sqlalchemy import DECIMAL, Boolean, Date, Integer

    db = SessionLocal()
    try:
        # --- 1. 患者情報の保存 (Patientテーブル) ---
        patient_id_str = form_data.get("patient_id")
        patient = None
        if patient_id_str:
            patient_id = int(patient_id_str)
            patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
            if not patient:
                raise Exception(f"更新対象の患者ID: {patient_id} が見つかりません。")
        else:
            patient = Patient()

        patient.name = form_data.get("name")
        patient.gender = form_data.get("gender")
        if form_data.get("age"):
            try:
                birth_year = date.today().year - int(form_data.get("age"))
                patient.date_of_birth = date(birth_year, 1, 1)
            except (ValueError, TypeError):
                pass

        if not patient.patient_id:
            db.add(patient)
        db.commit()
        saved_patient_id = patient.patient_id

        # --- 2. 新しい計画書レコードの準備 (RehabilitationPlanテーブル) ---
        new_plan = RehabilitationPlan(patient_id=saved_patient_id, created_at=datetime.now())
        db.add(new_plan)

        columns = RehabilitationPlan.__table__.columns
        boolean_columns = {col.name for col in columns if isinstance(col.type, Boolean)}

        # --- 3. データの型ごとに処理を分離して安全に値を設定 ---

        # 3-1. 日付フィールドの処理
        processed_date_keys = set()
        for key in list(form_data.keys()):
            if key.endswith(("_year", "_month", "_day")):
                base_key = key.rsplit("_", 1)[0]
                if base_key in processed_date_keys:
                    continue
                processed_date_keys.add(base_key)

                year = form_data.get(f"{base_key}_year")
                month = form_data.get(f"{base_key}_month")
                day = form_data.get(f"{base_key}_day")

                if year and month and day:
                    try:
                        date_value = date(int(year), int(month), int(day))
                        if hasattr(new_plan, base_key):
                            setattr(new_plan, base_key, date_value)
                    except (ValueError, TypeError):
                        print(f"   [警告] 無効な日付: {base_key}")
                        pass

        # 3-2. チェックボックス (Boolean) の処理
        for col_name in boolean_columns:
            # フォームにキーが存在し、値が 'on' などであれば True
            is_checked = str(form_data.get(col_name)).lower() in ["true", "on", "1"]
            setattr(new_plan, col_name, is_checked)

        # 3-3. それ以外のフィールド (数値、テキストなど) の処理
        for key, value in form_data.items():
            # 既に処理済みのキーはスキップ
            if key in boolean_columns or key.rsplit("_", 1)[0] in processed_date_keys:
                continue

            # patient_id はオブジェクト作成時に設定済みのため、フォームの値で上書きしない
            if key == "patient_id":
                continue

            if key not in columns:
                continue

            column_type = columns[key].type
            processed_value = None
            if value is not None and value != "":
                try:
                    if isinstance(column_type, Integer):
                        processed_value = int(value)
                    elif isinstance(column_type, DECIMAL):
                        processed_value = float(value)
                    elif isinstance(column_type, Date):
                        processed_value = datetime.strptime(value, "%Y-%m-%d").date()
                    else:  # String, Text
                        processed_value = str(value)
                except (ValueError, TypeError) as e:
                    print(f"   [警告] 型変換エラー: key='{key}', value='{value}', error='{e}'")
                    pass

            setattr(new_plan, key, processed_value)

        # 最後に計画書の変更をコミット
        db.commit()

        return saved_patient_id

    except Exception as e:
        db.rollback()
        print(f"   [エラー] データベース保存中にエラーが発生しました: {e}")
        raise
    finally:
        db.close()
