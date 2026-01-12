import json
import logging

from app.core.database import SessionLocal
from app.crud import patient as patient_crud
from app.models import Patient, RehabilitationPlan

logger = logging.getLogger(__name__)

def normalize_form_data(form_data: dict) -> dict:
    """
    フォームデータ（特にラジオボタンの選択値）をDB保存用の形式（チェックボックス on/off）に変換する
    """
    RADIO_GROUP_MAP = {
        "func_basic_rolling_level": "func_basic_rolling_",
        "func_basic_sitting_balance_level": "func_basic_sitting_balance_",
        "func_basic_getting_up_level": "func_basic_getting_up_",
        "func_basic_standing_balance_level": "func_basic_standing_balance_",
        "func_basic_standing_up_level": "func_basic_standing_up_",
        "social_care_level_support_num_slct": "social_care_level_support_num",
        "social_care_level_care_num_slct": "social_care_level_care_num",
        "goal_p_schooling_status_slct": "goal_p_schooling_status_",
        "goal_a_bed_mobility_level": "goal_a_bed_mobility_",
        "goal_a_indoor_mobility_level": "goal_a_indoor_mobility_",
        "goal_a_outdoor_mobility_level": "goal_a_outdoor_mobility_",
        "goal_a_driving_level": "goal_a_driving_",
        "goal_a_transport_level": "goal_a_public_transport_",
        "goal_a_toileting_level": "goal_a_toileting_",
        "goal_a_eating_level": "goal_a_eating_",
        "goal_a_grooming_level": "goal_a_grooming_",
        "goal_a_dressing_level": "goal_a_dressing_",
        "goal_a_bathing_level": "goal_a_bathing_",
        "goal_a_housework_level": "goal_a_housework_meal_",
        "goal_a_writing_level": "goal_a_writing_",
        "goal_a_ict_level": "goal_a_ict_",
        "goal_a_communication_level": "goal_a_communication_",
        "goal_p_return_to_work_status_slct": "goal_p_return_to_work_status_",
        "func_circulatory_arrhythmia_status_slct": "func_circulatory_arrhythmia_status_",
    }
    # フォームデータを直接変更するのではなく、追加のデータを保持する辞書を作成
    additional_data = {}

    for group_name, prefix in RADIO_GROUP_MAP.items():
        if group_name in form_data and form_data[group_name]:
            value = form_data[group_name]

            # 例: social_care_level_support_num_slct の値が '1' の場合
            if group_name in ["social_care_level_support_num_slct", "social_care_level_care_num_slct"]:
                # social_care_level_support_num1_slct = 'on' を生成
                target_key = f"{prefix}{value}_slct"
            # 例: goal_a_writing_level の値が 'independent_after_hand_change' の場合
            elif value == "independent_after_hand_change":
                # goal_a_writing_independent_after_hand_change_chk = 'on' を生成
                target_key = f"{prefix}independent_after_hand_change_chk"
            # 例: func_basic_rolling_level の値が 'partial_assist' の場合
            elif value == "partial_assist":
                # func_basic_rolling_partial_assistance_chk = 'on' を生成
                target_key = f"{prefix}partial_assistance_chk"
            # 例: goal_a_toileting_level の値が 'assist' の場合
            elif value == "assist":
                # goal_a_toileting_assistance_chk = 'on' を生成
                target_key = f"{prefix}assistance_chk"
            # 'yes'/'no' のような新しい形式に対応
            elif value in ["yes", "no"]:
                # func_circulatory_arrhythmia_status_yes_chk のようなキーは存在しないため、この場合は何もしない
                continue
            # その他の一般的な値 (independent, not_performed など)
            else:
                # func_basic_rolling_independent_chk = 'on' などを生成
                target_key = f"{prefix}{value}_chk"

            additional_data[target_key] = "on"

    # 元のフォームデータに、変換して生成したデータを追加
    normalized_data = form_data.copy()
    normalized_data.update(additional_data)

    return normalized_data

def prepare_edit_page_data(patient_id: int = None) -> dict:
    """
    編集ページ表示用のデータを取得・整形する
    """
    result = {
        "patient_data": {},
        "plan_history": [],
        "fim_history_json": None,
        "all_patients": [],
        "error_message": None
    }

    session = SessionLocal()
    try:
        # プルダウン用に全患者のリストを取得
        result["all_patients"] = patient_crud.get_all_patients()

        if patient_id:
            # 1. 最新7件の計画書データを取得
            latest_plans = (
                session.query(RehabilitationPlan)
                .filter(RehabilitationPlan.patient_id == patient_id)
                .order_by(RehabilitationPlan.created_at.desc())
                .limit(7)
                .all()
            )

            # 2. 取得したデータを使ってフォーム表示とグラフ表示のデータを準備
            if latest_plans:
                # フォーム表示用に、最新の1件の計画書から患者データを構築
                latest_plan_obj = latest_plans[0]
                patient_obj = latest_plan_obj.patient

                # PatientオブジェクトとRehabilitationPlanオブジェクトから辞書を作成して結合
                patient_dict = {c.name: getattr(patient_obj, c.name) for c in patient_obj.__table__.columns}
                patient_dict["age"] = patient_obj.age
                plan_dict = {c.name: getattr(latest_plan_obj, c.name) for c in latest_plan_obj.__table__.columns}
                result["patient_data"] = {**patient_dict, **plan_dict}

                # グラフ用に、古い→新しい順に並べ替えてJSON化
                fim_history_for_chart = [
                    {c.name: getattr(p, c.name) for c in p.__table__.columns}
                    for p in reversed(latest_plans)  # 古い順に並べ替え
                ]
                result["fim_history_json"] = json.dumps(fim_history_for_chart, default=str)

                # 履歴ドロップダウン用に、全計画書のIDと作成日時を準備
                all_plans_query = (
                    session.query(RehabilitationPlan.plan_id, RehabilitationPlan.created_at)
                    .filter(RehabilitationPlan.patient_id == patient_id)
                    .order_by(RehabilitationPlan.created_at.desc())
                    .all()
                )
                result["plan_history"] = [{"plan_id": p.plan_id, "created_at": p.created_at} for p in all_plans_query if p.created_at]

            else:
                # 計画書が1件もない場合
                patient_obj = session.query(Patient).filter(Patient.patient_id == patient_id).first()
                if patient_obj:
                    result["patient_data"] = {c.name: getattr(patient_obj, c.name) for c in patient_obj.__table__.columns}
                    result["patient_data"]["age"] = patient_obj.age
                else:
                    result["error_message"] = f"ID:{patient_id}の患者データが見つかりません。"

    except Exception as e:
        logger.error(f"prepare_edit_page_data error: {e}")
        result["error_message"] = "無効な患者IDです。"
    finally:
        session.close()

    return result
