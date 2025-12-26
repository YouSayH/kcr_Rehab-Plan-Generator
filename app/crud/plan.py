import json
from collections import defaultdict
from datetime import datetime

from sqlalchemy import DECIMAL, Boolean, Date, Integer, func
from sqlalchemy.dialects.mysql import insert as mysql_insert

import app.core.database as database
from app.models import LikedItemDetail, RegenerationHistory, RehabilitationPlan, SuggestionLike


def save_new_plan(patient_id: int, staff_id: int, form_data: dict, liked_items: dict = None):
    """
    Webフォームからのデータで新しい計画書を保存する。
    plan_idを無視し、各値を正しい型に変換して堅牢に保存する。
    いいね情報のスナップショットも一緒に保存する。
    """
    db = database.SessionLocal()
    try:
        # 新しい計画書オブジェクトを作成
        new_plan = RehabilitationPlan(
            patient_id=patient_id,
            liked_items_json=json.dumps(liked_items) if liked_items else None,
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

def get_plan_by_id(plan_id: int):
    """plan_idを使って単一の計画書データを取得する"""
    db = database.SessionLocal()
    try:
        plan = db.query(RehabilitationPlan).filter(RehabilitationPlan.plan_id == plan_id).first()
        if not plan:
            return None

        # 計画データを辞書に変換
        plan_data = {c.name: getattr(plan, c.name) for c in plan.__table__.columns}

        # 関連する患者情報も取得してマージ
        patient = plan.patient
        # Patientモデルの全カラムを動的に取得して辞書化
        patient_data = {c.name: getattr(patient, c.name) for c in patient.__table__.columns}
        patient_data["age"] = patient.age # @property の age も追加

        # patient_data を先に置き、plan_data で上書きする形で結合
        # (patient_id などが両方に含まれるため)
        final_data = {**patient_data, **plan_data}

        # JSON形式で保存されたいいね情報を辞書に復元して追加
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

# --- いいね (SuggestionLike) 関連 ---

def save_suggestion_like(patient_id: int, item_key: str, liked_model: str, staff_id: int):
    """
    AI提案への「いいね」評価を保存または削除する。
    - liked_modelがnullでなければ、その評価を保存（UPSERT）。
    - liked_modelがnullであれば、その評価を削除。
    """
    db = database.SessionLocal()
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
    db = database.SessionLocal()
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
    """特定の患者に紐づく全ての一時的な「いいね」情報を削除する"""
    db = database.SessionLocal()
    try:
        db.query(SuggestionLike).filter(SuggestionLike.patient_id == patient_id).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_likes_by_patient_id(patient_id: int) -> dict:
    """特定の患者に紐づく全ての「いいね」情報を取得する"""
    db = database.SessionLocal()
    try:
        likes = db.query(SuggestionLike).filter(SuggestionLike.patient_id == patient_id).all()
        if not likes:
            return {}

        # {item_key: [liked_model1, liked_model2]} の形式の辞書を作成する
        liked_items = defaultdict(list)
        for like in likes:
            liked_items[like.item_key].append(like.liked_model)
        return dict(liked_items)
    except Exception as e:
        print(f"   [エラー] いいね情報の取得中にエラーが発生しました: {e}")
        return {}  # エラー時も空の辞書を返す
    finally:
        db.close()

# --- いいね詳細 (LikedItemDetail) 関連 ---

def save_all_suggestion_details(rehabilitation_plan_id: int, staff_id: int, suggestions: dict, therapist_notes: str, patient_info: dict, liked_items: dict, editable_keys: list):
    """全てのAI提案といいね情報を liked_item_details テーブルに保存する"""
    db = database.SessionLocal()
    try:
        details_to_save = []
        patient_info_json = json.dumps(patient_info, ensure_ascii=False, default=str)

        # 全ての編集可能項目についてループ
        for item_key in editable_keys:
            # いいねの有無に関わらず、AI提案が存在すればレコードを作成する
            general_suggestion = suggestions.get(f"general_{item_key}")
            specialized_suggestion = suggestions.get(f"specialized_{item_key}")
            # 意味のある提案（「特記なし」や空文字列以外）が存在する場合のみDBに保存
            has_meaningful_general = (general_suggestion and general_suggestion.strip() and general_suggestion.strip() != "特記なし")
            has_meaningful_specialized = (specialized_suggestion and specialized_suggestion.strip() and specialized_suggestion.strip() != "特記なし")

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


def get_all_liked_item_details():
    """すべてのいいね詳細情報を取得する (集計用)"""
    db = database.SessionLocal()
    try:
        details = db.query(LikedItemDetail).all()
        return [{c.name: getattr(d, c.name) for c in d.__table__.columns} for d in details]
    finally:
        db.close()

def get_plans_with_liked_details_for_patient(patient_id: int):
    """指定された患者の、いいね詳細情報が含まれる計画書のリストを取得する"""
    db = database.SessionLocal()
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
    db = database.SessionLocal()
    try:
        details = db.query(LikedItemDetail).filter(LikedItemDetail.rehabilitation_plan_id == plan_id).all()
        # SQLAlchemyオブジェクトを辞書のリストに変換して返す
        return [{c.name: getattr(detail, c.name) for c in detail.__table__.columns} for detail in details]
    finally:
        db.close()

# --- 再生成履歴 (RegenerationHistory) ---

def save_regeneration_history(rehabilitation_plan_id: int, history_data: list):
    """再生成の履歴をデータベースに保存する"""
    if not history_data:
        return

    db = database.SessionLocal()
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

def get_all_regeneration_history():
    """すべての再生成履歴を取得する"""
    db = database.SessionLocal()
    try:
        results = db.query(RegenerationHistory.item_key, RegenerationHistory.model_type).all()
        # SQLAlchemyの結果オブジェクトを辞書のリストに変換して返す
        return [{"item_key": r.item_key, "model_type": r.model_type} for r in results]
    finally:
        db.close()

def save_liked_item_details(
    rehabilitation_plan_id: int, staff_id: int, liked_items: dict, suggestions: dict, therapist_notes: str, patient_info: dict
):
    """【旧関数・削除予定】いいねされた項目の詳細情報を liked_item_details テーブルに保存する"""
    db = database.SessionLocal()
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
