import json
import logging
import os

import app.core.database as database
import app.services.excel_writer as excel_writer

logger = logging.getLogger(__name__)

# 編集可能な項目の定義
EDITABLE_KEYS = [
    "main_risks_txt",
    "main_contraindications_txt",
    "func_pain_txt",
    "func_rom_limitation_txt",
    "func_muscle_weakness_txt",
    "func_swallowing_disorder_txt",
    "func_behavioral_psychiatric_disorder_txt",
    "cs_motor_details",
    "func_nutritional_disorder_txt",
    "func_excretory_disorder_txt",
    "func_pressure_ulcer_txt",
    "func_contracture_deformity_txt",
    "func_motor_muscle_tone_abnormality_txt",
    "func_disorientation_txt",
    "func_memory_disorder_txt",
    "adl_equipment_and_assistance_details_txt",
    "goals_1_month_txt",
    "goals_at_discharge_txt",
    "policy_treatment_txt",
    "policy_content_txt",
    "goal_p_action_plan_txt",
    "goal_a_action_plan_txt",
    "goal_s_psychological_action_plan_txt",
    "goal_s_env_action_plan_txt",
    "goal_s_3rd_party_action_plan_txt",
]

def execute_save_workflow(staff_id, patient_id, form_data):
    """
    計画書の保存処理ワークフローを実行する。
    DBへの保存、詳細情報の保存、Excelの生成、一時データのクリーンアップを行う。

    Args:
        staff_id (int): 実行するスタッフのID
        patient_id (int): 患者ID
        form_data (dict): フォームから送信されたデータ

    Returns:
        str: 生成されたExcelファイルのファイル名

    Raises:
        ValueError: 計画データの再取得に失敗した場合
        Exception: その他DB保存やファイル生成中にエラーが発生した場合
    """
    # 所感、AI提案テキスト、再生成履歴をフォームデータから分離
    therapist_notes = form_data.get("therapist_notes", "")
    suggestions = {k.replace("suggestion_", ""): v for k, v in form_data.items() if k.startswith("suggestion_")}
    regeneration_history_json = form_data.get("regeneration_history", "[]")

    # この患者の現在の「いいね」情報を取得（計画書のスナップショット用）
    liked_items = database.get_likes_by_patient_id(patient_id)

    # データベースに新しい計画として保存し、そのIDを取得
    new_plan_id = database.save_new_plan(patient_id, staff_id, form_data, liked_items)

    # 全てのAI提案詳細情報を保存
    # 患者情報スナップショット用に、再度患者データを取得
    patient_info_snapshot = database.get_patient_data_for_plan(patient_id)

    database.save_all_suggestion_details(
        rehabilitation_plan_id=new_plan_id,
        staff_id=staff_id,
        suggestions=suggestions,
        therapist_notes=therapist_notes,
        patient_info=patient_info_snapshot,
        liked_items=liked_items,
        editable_keys=EDITABLE_KEYS,
    )

    # 再生成履歴を保存
    try:
        regeneration_history = json.loads(regeneration_history_json)
        database.save_regeneration_history(new_plan_id, regeneration_history)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"再生成履歴の処理中にエラーが発生しました: {e}")

    # Excel出力用に、DBに保存されたばかりの計画データをIDで再取得
    plan_data_for_excel = database.get_plan_by_id(new_plan_id)
    if not plan_data_for_excel:
        # このエラーは通常発生しないはず
        raise ValueError("保存した計画データの再取得に失敗しました。")

    # Excelファイルを作成
    # Excel出力関数にもいいね情報を渡す
    output_filepath = excel_writer.create_plan_sheet(plan_data_for_excel)
    output_filename = os.path.basename(output_filepath)

    # 一時的ないいね情報を削除
    database.delete_all_likes_for_patient(patient_id)

    return output_filename
