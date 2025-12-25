import json
import os
from collections import defaultdict
from datetime import date, datetime

from dotenv import load_dotenv
from sqlalchemy import DECIMAL, Boolean, Date, Integer, create_engine, func
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.models import Base, LikedItemDetail, Patient, RegenerationHistory, RehabilitationPlan, Staff, SuggestionLike

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

# データベース接続URLを作成
# "mysql+pymysql" の部分で、SQLAlchemyが内部的にPyMySQLを使うことを指定
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset=utf8mb4"

# SQLAlchemyのエンジンを作成
# engine = create_engine(DATABASE_URL, echo=False)
# pool_recycle=3600 を追加し、接続を1時間ごとにリサイクルする
# engine = create_engine(DATABASE_URL, echo=False, pool_recycle=3600)
# 接続が生きてるかを自動確認し、死んでいれば再接続
engine = create_engine(DATABASE_URL, echo=False, pool_recycle=3600, pool_pre_ping=True, pool_size=10, max_overflow=20)

# セッションを作成するためのクラス（ファクトリ）を定義
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# データ操作関数
def get_patient_data_for_plan(patient_id: int, db_session=None):
    """【SQLAlchemy版】患者の基本情報と最新の計画書データ、いいね評価を取得する"""
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
    【修正】計画書は常に新しいレコードとして保存する。
    """
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


def save_new_plan(patient_id: int, staff_id: int, form_data: dict, liked_items: dict = None):
    """
    【最終修正版】
    Webフォームからのデータで新しい計画書を保存する。
    plan_idを無視し、各値を正しい型に変換して堅牢に保存する。
    【改修】いいね情報のスナップショットも一緒に保存する。
    """
    db = SessionLocal()
    try:
        # 新しい計画書オブジェクトを作成
        new_plan = RehabilitationPlan(
            patient_id=patient_id,
            liked_items_json=json.dumps(liked_items)
            if liked_items
            else None,  # 【追加】いいね情報をJSON文字列に変換してセット
            created_by_staff_id=staff_id,
            created_at=datetime.now(),  # 現在時刻を記録
        )

        # RehabilitationPlanモデルの全てのカラム定義を取得
        columns = RehabilitationPlan.__table__.columns
        boolean_columns = {col.name for col in columns if isinstance(col.type, Boolean)}

        # まず、すべてのブール値をFalseに初期化
        for col_name in boolean_columns:
            setattr(new_plan, col_name, False)

        # フォームから送られてきたデータ（form_data）をループ
        for key, value in form_data.items():
            # plan_idやpatient_idなど、自動設定されるキーはスキップ
            if key in ["plan_id", "patient_id", "created_by_staff_id", "created_at"]:
                continue

            # フォームのキーがモデルのカラムに存在する場合のみ処理
            if key in columns:
                column_type = columns[key].type

                # 値を適切な型に変換
                processed_value = None
                if value is not None and value != "":
                    try:
                        if isinstance(column_type, Boolean):
                            processed_value = str(value).lower() in ["true", "on", "1"]
                        elif isinstance(column_type, Integer):
                            processed_value = int(value)
                        elif isinstance(column_type, DECIMAL):
                            processed_value = float(value)
                        elif isinstance(column_type, Date):
                            processed_value = datetime.strptime(value, "%Y-%m-%d").date()
                        else:  # String, Text
                            processed_value = str(value)  # 明示的に文字列に変換
                    except (ValueError, TypeError) as e:
                        print(f"   [警告] 型変換エラー: key='{key}', value='{value}', error='{e}'")
                        processed_value = None

                # 変換した値をオブジェクトに設定 (Noneの場合は設定しないことで、初期化されたFalseを維持)
                if processed_value is not None:
                    setattr(new_plan, key, processed_value)

        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)  # new_planオブジェクトを更新して、DBが自動採番したIDなどを反映させる
        print(f"   [成功] 新しい計画書(plan_id: {new_plan.plan_id})をデータベースに保存しました。")
        return new_plan.plan_id  # 保存したplan_idを返す
    except Exception as e:
        db.rollback()
        print(f"   [エラー] データベース保存中にエラーが発生しました: {e}")
        raise  # エラーを呼び出し元に通知
    finally:
        db.close()


def save_all_suggestion_details(
    rehabilitation_plan_id: int,
    staff_id: int,
    suggestions: dict,
    therapist_notes: str,
    patient_info: dict,
    liked_items: dict,
    editable_keys: list,
):
    """【修正】全てのAI提案といいね情報を liked_item_details テーブルに保存する"""
    db = SessionLocal()
    try:
        details_to_save = []
        patient_info_json = json.dumps(patient_info, ensure_ascii=False, default=str)

        # 全ての編集可能項目についてループ
        for item_key in editable_keys:
            # 【修正】いいねの有無に関わらず、AI提案が存在すればレコードを作成する
            general_suggestion = suggestions.get(f"general_{item_key}")
            specialized_suggestion = suggestions.get(f"specialized_{item_key}")

            # 【修正】意味のある提案（「特記なし」や空文字列以外）が存在する場合のみDBに保存
            has_meaningful_general = (
                general_suggestion and general_suggestion.strip() and general_suggestion.strip() != "特記なし"
            )
            has_meaningful_specialized = (
                specialized_suggestion and specialized_suggestion.strip() and specialized_suggestion.strip() != "特記なし"
            )

            if has_meaningful_general or has_meaningful_specialized:
                # この項目でいいねされたモデルのリストを取得
                liked_models_for_item = liked_items.get(item_key, [])

                detail = LikedItemDetail(
                    rehabilitation_plan_id=rehabilitation_plan_id,
                    staff_id=staff_id,
                    item_key=item_key,
                    # いいねされたモデルをカンマ区切りで保存 (例: "general,specialized")
                    liked_model=",".join(liked_models_for_item) if liked_models_for_item else None,
                    general_suggestion_text=general_suggestion,
                    specialized_suggestion_text=specialized_suggestion,
                    therapist_notes_at_creation=therapist_notes,
                    patient_info_snapshot_json=patient_info_json,
                )
                details_to_save.append(detail)

        if details_to_save:
            db.bulk_save_objects(details_to_save)
            db.commit()
            print(f"   [成功] {len(details_to_save)}件のAI提案詳細を保存しました。")
    except Exception as e:
        db.rollback()
        print(f"   [エラー] いいね詳細情報の保存中にエラーが発生しました: {e}")
        raise
    finally:
        db.close()


def save_liked_item_details(
    rehabilitation_plan_id: int, staff_id: int, liked_items: dict, suggestions: dict, therapist_notes: str, patient_info: dict
):
    """【旧関数・削除予定】いいねされた項目の詳細情報を liked_item_details テーブルに保存する"""
    db = SessionLocal()
    try:
        details_to_save = []
        patient_info_json = json.dumps(patient_info, ensure_ascii=False, default=str)

        for item_key, models in liked_items.items():
            for model in models:
                detail = LikedItemDetail(
                    rehabilitation_plan_id=rehabilitation_plan_id,
                    staff_id=staff_id,
                    item_key=item_key,
                    liked_model=model,
                    general_suggestion_text=suggestions.get(f"general_{item_key}"),
                    specialized_suggestion_text=suggestions.get(f"specialized_{item_key}"),
                    therapist_notes_at_creation=therapist_notes,
                    patient_info_snapshot_json=patient_info_json,
                )
                details_to_save.append(detail)

        if details_to_save:
            db.bulk_save_objects(details_to_save)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"   [エラー] いいね詳細情報の保存中にエラーが発生しました: {e}")
        raise
    finally:
        db.close()


def save_regeneration_history(rehabilitation_plan_id: int, history_data: list):
    """再生成の履歴をデータベースに保存する"""
    if not history_data:
        return

    db = SessionLocal()
    try:
        history_records = []
        for item in history_data:
            # "item_key-model_type" の形式を分割
            parts = item.split("-")
            if len(parts) >= 2:
                item_key = parts[0]
                model_type = "-".join(parts[1:])  # model_typeにハイフンが含まれる可能性を考慮
                record = RegenerationHistory(
                    rehabilitation_plan_id=rehabilitation_plan_id, item_key=item_key, model_type=model_type
                )
                history_records.append(record)

        if history_records:
            db.bulk_save_objects(history_records)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"   [エラー] 再生成履歴の保存中にエラーが発生しました: {e}")
        raise
    finally:
        db.close()


def save_suggestion_like(patient_id: int, item_key: str, liked_model: str, staff_id: int):
    """
    AI提案への「いいね」評価を保存または削除する。
    - liked_modelがnullでなければ、その評価を保存（UPSERT）。
    - liked_modelがnullであれば、その評価を削除。
    """
    db = SessionLocal()
    try:
        # いいねを追加または更新 (UPSERT)
        stmt = mysql_insert(SuggestionLike).values(
            patient_id=patient_id,
            item_key=item_key,
            liked_model=liked_model,
            staff_id=staff_id,
        )
        on_duplicate_stmt = stmt.on_duplicate_key_update(staff_id=stmt.inserted.staff_id, updated_at=func.now())
        db.execute(on_duplicate_stmt)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"   [エラー] いいね評価の保存中にエラーが発生しました: {e}")
        raise
    finally:
        db.close()


def delete_suggestion_like(patient_id: int, item_key: str, liked_model: str):
    # いいね評価の削除
    db = SessionLocal()
    try:
        db.query(SuggestionLike).filter_by(patient_id=patient_id, item_key=item_key, liked_model=liked_model).delete(
            synchronize_session=False
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def delete_all_likes_for_patient(patient_id: int):
    """【新規】特定の患者に紐づく全ての一時的な「いいね」情報を削除する"""
    db = SessionLocal()
    try:
        db.query(SuggestionLike).filter(SuggestionLike.patient_id == patient_id).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_likes_by_patient_id(patient_id: int) -> dict:
    """【新規】特定の患者に紐づく全ての「いいね」情報を取得する"""
    db = SessionLocal()
    try:
        likes = db.query(SuggestionLike).filter(SuggestionLike.patient_id == patient_id).all()
        if not likes:
            return {}

        # {item_key: [liked_model1, liked_model2]} の形式の辞書を作成する
        liked_items = defaultdict(list)
        for like in likes:
            liked_items[like.item_key].append(like.liked_model)
        return liked_items
    except Exception as e:
        print(f"   [エラー] いいね情報の取得中にエラーが発生しました: {e}")
        return {}  # エラー時も空の辞書を返す
    finally:
        db.close()


def get_all_regeneration_history():
    """【新規】すべての再生成履歴を取得する"""
    db = SessionLocal()
    try:
        results = db.query(RegenerationHistory.item_key, RegenerationHistory.model_type).all()
        # SQLAlchemyの結果オブジェクトを辞書のリストに変換して返す
        return [{"item_key": r.item_key, "model_type": r.model_type} for r in results]
    finally:
        db.close()


def get_plan_by_id(plan_id: int):
    """【新規追加】plan_idを使って単一の計画書データを取得する"""
    db = SessionLocal()
    try:
        plan = db.query(RehabilitationPlan).filter(RehabilitationPlan.plan_id == plan_id).first()
        if not plan:
            return None

        # 計画データを辞書に変換
        plan_data = {c.name: getattr(plan, c.name) for c in plan.__table__.columns}

        # 関連する患者情報も取得してマージ
        patient = plan.patient
        # 【変更】Patientモデルの全カラムを動的に取得して辞書化
        patient_data = {c.name: getattr(patient, c.name) for c in patient.__table__.columns}
        patient_data["age"] = patient.age # @property の age も追加

        # patient_data を先に置き、plan_data で上書きする形で結合
        # (patient_id などが両方に含まれるため)
        final_data = {**patient_data, **plan_data}

        # 【追加】JSON形式で保存されたいいね情報を辞書に復元して追加
        if plan.liked_items_json:
            try:
                final_data["liked_items"] = json.loads(plan.liked_items_json)
            except json.JSONDecodeError:
                final_data["liked_items"] = {}  # パース失敗時は空の辞書
        else:
            final_data["liked_items"] = {}  # いいね情報がない場合は空の辞書をセット

        return final_data
    finally:
        db.close()


def get_staff_by_username(username: str):
    db = SessionLocal()
    try:
        staff = db.query(Staff).filter(Staff.username == username).first()
        if staff:
            return {c.name: getattr(staff, c.name) for c in staff.__table__.columns}
        return None
    finally:
        db.close()


def get_staff_by_id(staff_id: int):
    db = SessionLocal()
    try:
        staff = db.query(Staff).filter(Staff.id == staff_id).first()
        if staff:
            return {c.name: getattr(staff, c.name) for c in staff.__table__.columns}
        return None
    finally:
        db.close()


def create_staff(username: str, hashed_password: str, occupation: str, role: str = "general"):
    db = SessionLocal()
    try:
        new_staff = Staff(username=username, password=hashed_password, occupation=occupation, role=role)
        db.add(new_staff)
        db.commit()
    finally:
        db.close()


def get_assigned_patients(staff_id: int):
    db = SessionLocal()
    try:
        staff = db.query(Staff).filter(Staff.id == staff_id).first()
        if staff:
            return [{"patient_id": p.patient_id, "name": p.name} for p in staff.assigned_patients]
        return []
    finally:
        db.close()


def assign_patient_to_staff(staff_id: int, patient_id: int):
    db = SessionLocal()
    try:
        staff = db.query(Staff).filter(Staff.id == staff_id).first()
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if staff and patient:
            staff.assigned_patients.append(patient)
            db.commit()
    except IntegrityError:
        db.rollback()
        raise
    finally:
        db.close()


def unassign_patient_from_staff(staff_id: int, patient_id: int):
    db = SessionLocal()
    try:
        staff = db.query(Staff).filter(Staff.id == staff_id).first()
        patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
        if staff and patient and patient in staff.assigned_patients:
            staff.assigned_patients.remove(patient)
            db.commit()
    finally:
        db.close()


def get_all_staff():
    db = SessionLocal()
    try:
        staff_list = db.query(Staff.id, Staff.username, Staff.occupation, Staff.role).order_by(Staff.id).all()
        return [{"id": s.id, "username": s.username, "occupation": s.occupation, "role": s.role} for s in staff_list]
    finally:
        db.close()


def get_all_patients():
    db = SessionLocal()
    try:
        patient_list = db.query(Patient.patient_id, Patient.name).order_by(Patient.patient_id).all()
        return [{"patient_id": p.patient_id, "name": p.name} for p in patient_list]
    finally:
        db.close()


def delete_staff_by_id(staff_id: int):
    db = SessionLocal()
    try:
        staff_to_delete = db.query(Staff).filter(Staff.id == staff_id).first()
        if staff_to_delete:
            db.delete(staff_to_delete)
            db.commit()
    finally:
        db.close()


def init_db():
    # モデルの定義をデータベースに反映（テーブル作成）
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    import sys

    # コマンドライン引数をチェック
    if len(sys.argv) > 1 and sys.argv[1] == "--init":
        print("データベースのテーブルを初期化（作成）します...")
        init_db()
        print("完了しました。")
    else:
        print("使い方:")
        print("  python database.py --init     # データベースを初期化します")


def get_all_liked_item_details():
    """【新規】すべてのいいね詳細情報を取得する (集計用)"""
    db = SessionLocal()
    try:
        details = db.query(LikedItemDetail).all()
        return [{c.name: getattr(d, c.name) for c in d.__table__.columns} for d in details]
    finally:
        db.close()


# いいね詳細閲覧システム用の関数群

# def get_staff_with_liked_items():
#     """いいねをしたことがある職員のリストを取得する"""
#     db = SessionLocal()
#     try:
#         # Patient(患者)ではなく、Staff(職員)を検索するように変更します
#         staff_members = (
#             db.query(Staff)
#             # LikedItemDetailテーブルと結合して、いいね履歴がある職員を絞り込む
#             .join(LikedItemDetail, Staff.id == LikedItemDetail.staff_id)
#             .distinct() # 重複を除外（同じ人が何度もいいねしていても1件として扱う）
#             .all()
#         )
#         # 職員用の辞書リストとして返す
#         return [{"id": s.id, "username": s.username, "occupation": s.occupation} for s in staff_members]
#     finally:
#         db.close()


def get_patients_for_staff_with_liked_items(staff_id: int):
    """指定された職員がいいねをしたことがある患者のリストを取得する"""
    db = SessionLocal()
    try:
        # LikedItemDetail と RehabilitationPlan を経由して Patient を取得
        patients = (
            db.query(Patient)
            .join(RehabilitationPlan, Patient.patient_id == RehabilitationPlan.patient_id)
            .join(LikedItemDetail, RehabilitationPlan.plan_id == LikedItemDetail.rehabilitation_plan_id)
            .filter(LikedItemDetail.staff_id == staff_id)
            .distinct()
            .all()
        )
        return [{"patient_id": p.patient_id, "name": p.name} for p in patients]
    finally:
        db.close()


def get_plans_with_liked_details_for_patient(patient_id: int):
    """【新規】指定された患者の、いいね詳細情報が含まれる計画書のリストを取得する"""
    db = SessionLocal()
    try:
        plans = (
            db.query(RehabilitationPlan.plan_id, RehabilitationPlan.created_at)
            .join(LikedItemDetail, RehabilitationPlan.plan_id == LikedItemDetail.rehabilitation_plan_id)
            .filter(RehabilitationPlan.patient_id == patient_id)
            .distinct()
            .order_by(RehabilitationPlan.created_at.desc())
            .all()
        )
        return [{"plan_id": p.plan_id, "created_at": p.created_at} for p in plans]
    finally:
        db.close()


def get_liked_item_details_by_plan_id(plan_id: int):
    """指定されたplan_idに紐づく、すべてのいいね詳細情報を取得する"""
    db = SessionLocal()
    try:
        details = db.query(LikedItemDetail).filter(LikedItemDetail.rehabilitation_plan_id == plan_id).all()
        # SQLAlchemyオブジェクトを辞書のリストに変換して返す
        return [{c.name: getattr(detail, c.name) for c in detail.__table__.columns} for detail in details]
    finally:
        db.close()
