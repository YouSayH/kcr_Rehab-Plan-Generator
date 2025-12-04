import json
import logging
import os
import re
import pprint
import textwrap
import time
from datetime import date

# RAGExecutorは循環参照を避けるため、型ヒントのみに使用します
from typing import TYPE_CHECKING, Dict, Optional, Type

# Ollamaライブラリをインポート
import ollama
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, create_model

if TYPE_CHECKING:
    from rag_executor import RAGExecutor

# 共通のスキーマ定義をインポート
from schemas import (
    GENERATION_GROUPS,
    RehabPlanSchema,
)

# 初期設定
load_dotenv()

OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "qwen3:8b")

# 構造的出力（JSONモード）を使用するかどうかのフラグ
# .envで OLLAMA_USE_STRUCTURED_OUTPUT=false と設定すれば無効化できる
OLLAMA_USE_STRUCTURED_OUTPUT = os.getenv("OLLAMA_USE_STRUCTURED_OUTPUT", "true").lower() == "true"

# ロガー設定 (gemini_client.pyと共通のファイルに出力)
log_directory = "logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)
log_file_path = os.path.join(log_directory, "gemini_prompts.log")

# ロガーの重複設定を避ける
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


# プロトタイプ開発用の設定 (Trueにするとダミーデータを返す)
USE_DUMMY_DATA = False


# --- ヘルパー関数群 (gemini_client.pyと共通) ---


def _format_value(value):
    """値を人間が読みやすい形に整形する"""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return "あり" if value else "なし"
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value)

def extract_and_parse_json(text: str) -> dict:
    """
    LLMの出力テキストからJSON部分を抽出してパースする関数。
    CoT（<think>タグ）やMarkdownコードブロックに対応。
    """
    # 1. <think>タグの除去 (思考プロセスが含まれる場合)
    text_cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    
    # 2. Markdownコードブロック ```json ... ``` の抽出
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', text_cleaned, re.DOTALL)
    if not json_match:
        # コードブロックがない場合、単なる ``` ... ``` を探す
        json_match = re.search(r'```\s*(\{.*?\})\s*```', text_cleaned, re.DOTALL)
    
    if json_match:
        json_str = json_match.group(1)
    else:
        # 3. コードブロックがない場合、最初と最後の {} を探す
        start = text_cleaned.find('{')
        end = text_cleaned.rfind('}')
        if start != -1 and end != -1 and end > start:
            json_str = text_cleaned[start : end + 1]
        else:
            # 見つからない場合は元のテキスト全体を試す
            json_str = text_cleaned

    # 4. JSONパース
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # エラー時のログ出力用に、抽出した文字列を少し含める
        raise ValueError(f"JSON extraction/parsing failed: {e}. Target str: {json_str[:100]}...")


# DBカラム名と日本語名のマッピング
# DBカラム名と日本語名のマッピング
CELL_NAME_MAPPING = {
    # 1枚目
    # ヘッダー・基本情報
    "header_disease_name_txt": "算定病名",
    "header_treatment_details_txt": "治療内容",
    "header_onset_date": "発症日・手術日",
    "header_rehab_start_date": "リハ開始日",
    "main_comorbidities_txt": "併存疾患・合併症",
    "header_therapy_pt_chk": "実施療法(PT)",
    "header_therapy_ot_chk": "実施療法(OT)",
    "header_therapy_st_chk": "実施療法(ST)",
    # 心身機能・構造 (全般)
    "func_consciousness_disorder_chk": "意識障害",
    "func_consciousness_disorder_jcs_gcs_txt": "意識障害(JCS/GCS)",
    "func_respiratory_disorder_chk": "呼吸機能障害",
    "func_respiratory_o2_therapy_chk": "酸素療法",
    "func_respiratory_o2_therapy_l_min_txt": "酸素流量(L/min)",
    "func_respiratory_tracheostomy_chk": "気管切開",
    "func_respiratory_ventilator_chk": "人工呼吸器",
    "func_circulatory_disorder_chk": "循環障害",
    "func_circulatory_ef_chk": "心駆出率(EF)測定",
    "func_circulatory_ef_val": "心駆出率(EF)値",
    "func_circulatory_arrhythmia_chk": "不整脈",
    # "func_circulatory_arrhythmia_status_slct": "不整脈の状態",
    "func_risk_factors_chk": "危険因子",
    "func_risk_hypertension_chk": "高血圧症",
    "func_risk_dyslipidemia_chk": "脂質異常症",
    "func_risk_diabetes_chk": "糖尿病",
    "func_risk_smoking_chk": "喫煙",
    "func_risk_obesity_chk": "肥満",
    "func_risk_hyperuricemia_chk": "高尿酸血症",
    "func_risk_ckd_chk": "慢性腎臓病(CKD)",
    "func_risk_family_history_chk": "家族歴",
    "func_risk_angina_chk": "狭心症",
    "func_risk_omi_chk": "陳旧性心筋梗塞",
    "func_risk_other_chk": "危険因子(その他)",
    # "func_risk_other_txt": "危険因子(その他詳細)",
    # 心身機能詳細（CHECK_TO_TEXT_MAPで処理されるもの + α）
    "func_swallowing_disorder_chk": "摂食嚥下障害",
    "func_swallowing_disorder_txt": "摂食嚥下障害(詳細)",
    "func_nutritional_disorder_chk": "栄養障害",
    "func_nutritional_disorder_txt": "栄養障害(詳細)",
    "func_excretory_disorder_chk": "排泄機能障害",
    "func_excretory_disorder_txt": "排泄機能障害(詳細)",
    "func_pressure_ulcer_chk": "褥瘡",
    "func_pressure_ulcer_txt": "褥瘡(詳細)",
    "func_pain_chk": "疼痛",
    "func_pain_txt": "疼痛(詳細)",
    "func_other_chk": "心身機能(その他)",
    "func_other_txt": "心身機能(その他詳細)",
    "func_rom_limitation_chk": "関節可動域制限",
    "func_rom_limitation_txt": "関節可動域制限(詳細)",
    "func_contracture_deformity_chk": "拘縮・変形",
    "func_contracture_deformity_txt": "拘縮・変形(詳細)",
    "func_muscle_weakness_chk": "筋力低下",
    "func_muscle_weakness_txt": "筋力低下(詳細)",
    # 心身機能・構造 (運動・感覚・高次脳など)
    "func_motor_dysfunction_chk": "運動機能障害",
    "func_motor_paralysis_chk": "麻痺",
    "func_motor_involuntary_movement_chk": "不随意運動",
    "func_motor_ataxia_chk": "運動失調",
    "func_motor_parkinsonism_chk": "パーキンソニズム",
    "func_motor_muscle_tone_abnormality_chk": "筋緊張異常",
    "func_motor_muscle_tone_abnormality_txt": "筋緊張異常(詳細)",
    "func_sensory_dysfunction_chk": "感覚機能障害",
    "func_sensory_hearing_chk": "聴覚障害",
    "func_sensory_vision_chk": "視覚障害",
    "func_sensory_superficial_chk": "表在感覚障害",
    "func_sensory_deep_chk": "深部感覚障害",
    "func_speech_disorder_chk": "音声発話障害",
    "func_speech_articulation_chk": "構音障害",
    "func_speech_aphasia_chk": "失語症",
    "func_speech_stuttering_chk": "吃音",
    "func_speech_other_chk": "音声発話(その他)",
    "func_speech_other_txt": "音声発話(その他詳細)",
    "func_higher_brain_dysfunction_chk": "高次脳機能障害",
    "func_higher_brain_memory_chk": "記憶障害(高次脳)",
    "func_higher_brain_attention_chk": "注意障害",
    "func_higher_brain_apraxia_chk": "失行",
    "func_higher_brain_agnosia_chk": "失認",
    "func_higher_brain_executive_chk": "遂行機能障害",
    "func_behavioral_psychiatric_disorder_chk": "精神行動障害",
    "func_behavioral_psychiatric_disorder_txt": "精神行動障害(詳細)",
    "func_disorientation_chk": "見当識障害",
    "func_disorientation_txt": "見当識障害(詳細)",
    "func_memory_disorder_chk": "記憶障害",
    "func_memory_disorder_txt": "記憶障害(詳細)",
    "func_developmental_disorder_chk": "発達障害",
    "func_developmental_asd_chk": "自閉症スペクトラム症",
    "func_developmental_ld_chk": "学習障害",
    "func_developmental_adhd_chk": "ADHD",
    # 基本動作
    "func_basic_rolling_chk": "寝返り(評価)",
    "func_basic_rolling_independent_chk": "寝返り(自立)",
    "func_basic_rolling_partial_assistance_chk": "寝返り(一部介助)",
    "func_basic_rolling_assistance_chk": "寝返り(介助)",
    "func_basic_rolling_not_performed_chk": "寝返り(非実施)",
    "func_basic_getting_up_chk": "起き上がり(評価)",
    "func_basic_getting_up_independent_chk": "起き上がり(自立)",
    "func_basic_getting_up_partial_assistance_chk": "起き上がり(一部介助)",
    "func_basic_getting_up_assistance_chk": "起き上がり(介助)",
    "func_basic_getting_up_not_performed_chk": "起き上がり(非実施)",
    "func_basic_standing_up_chk": "立ち上がり(評価)",
    "func_basic_standing_up_independent_chk": "立ち上がり(自立)",
    "func_basic_standing_up_partial_assistance_chk": "立ち上がり(一部介助)",
    "func_basic_standing_up_assistance_chk": "立ち上がり(介助)",
    "func_basic_standing_up_not_performed_chk": "立ち上がり(非実施)",
    "func_basic_sitting_balance_chk": "座位保持(評価)",
    "func_basic_sitting_balance_independent_chk": "座位保持(自立)",
    "func_basic_sitting_balance_partial_assistance_chk": "座位保持(一部介助)",
    "func_basic_sitting_balance_assistance_chk": "座位保持(介助)",
    "func_basic_sitting_balance_not_performed_chk": "座位保持(非実施)",
    "func_basic_standing_balance_chk": "立位保持(評価)",
    "func_basic_standing_balance_independent_chk": "立位保持(自立)",
    "func_basic_standing_balance_partial_assistance_chk": "立位保持(一部介助)",
    "func_basic_standing_balance_assistance_chk": "立位保持(介助)",
    "func_basic_standing_balance_not_performed_chk": "立位保持(非実施)",
    "func_basic_other_chk": "基本動作(その他)",
    "func_basic_other_txt": "基本動作(その他詳細)",
    # 栄養
    "nutrition_height_chk": "身長測定",
    "nutrition_height_val": "身長(cm)",
    "nutrition_weight_chk": "体重測定",
    "nutrition_weight_val": "体重(kg)",
    "nutrition_bmi_chk": "BMI測定",
    "nutrition_bmi_val": "BMI",
    "nutrition_method_oral_chk": "栄養補給(経口)",
    "nutrition_method_oral_meal_chk": "経口(食事)",
    "nutrition_method_oral_supplement_chk": "経口(補助食品)",
    "nutrition_method_tube_chk": "栄養補給(経管)",
    "nutrition_method_iv_chk": "栄養補給(静脈)",
    "nutrition_method_iv_peripheral_chk": "静脈(末梢)",
    "nutrition_method_iv_central_chk": "静脈(中心)",
    "nutrition_method_peg_chk": "栄養補給(胃ろう)",
    "nutrition_swallowing_diet_True_chk": "嚥下調整食の必要性",
    # "nutrition_swallowing_diet_slct": "嚥下調整食の必要性(選択)",
    "nutrition_swallowing_diet_code_txt": "嚥下調整食コード",
    "nutrition_status_assessment_no_problem_chk": "栄養状態の問題なし",
    "nutrition_status_assessment_malnutrition_chk": "栄養状態(低栄養)",
    "nutrition_status_assessment_malnutrition_risk_chk": "栄養状態(低栄養リスク)",
    "nutrition_status_assessment_overnutrition_chk": "栄養状態(過栄養)",
    "nutrition_status_assessment_other_chk": "栄養状態のその他",
    # "nutrition_status_assessment_slct": "栄養状態評価(選択)",
    "nutrition_status_assessment_other_txt": "栄養状態評価(その他詳細)",
    "nutrition_required_energy_val": "必要熱量(kcal)",
    "nutrition_required_protein_val": "必要タンパク質量(g)",
    "nutrition_total_intake_energy_val": "総摂取熱量(kcal)",
    "nutrition_total_intake_protein_val": "総摂取タンパク質量(g)",
    # 社会保障サービス
    "social_care_level_status_chk": "介護保険",
    "social_care_level_applying_chk": "介護保険(申請中)",
    "social_care_level_support_chk": "要支援",
    "social_care_level_support_num1_slct": "要支援1",
    "social_care_level_support_num2_slct": "要支援2",
    "social_care_level_care_slct": "要介護",
    "social_care_level_care_num1_slct": "要介護1",
    "social_care_level_care_num2_slct": "要介護2",
    "social_care_level_care_num3_slct": "要介護3",
    "social_care_level_care_num4_slct": "要介護4",
    "social_care_level_care_num5_slct": "要介護5",
    "social_disability_certificate_physical_chk": "身体障害者手帳",
    "social_disability_certificate_physical_txt": "身体障害者手帳(詳細)",
    "social_disability_certificate_physical_type_txt": "身体障害者手帳(種別)",
    "social_disability_certificate_physical_rank_val": "身体障害者手帳(等級)",
    "social_disability_certificate_mental_chk": "精神障害者保健福祉手帳",
    "social_disability_certificate_mental_rank_val": "精神障害者手帳(等級)",
    "social_disability_certificate_intellectual_chk": "療育手帳",
    "social_disability_certificate_intellectual_txt": "療育手帳(詳細)",
    "social_disability_certificate_intellectual_grade_txt": "療育手帳(障害程度)",
    "social_disability_certificate_other_chk": "社会保障(その他)",
    "social_disability_certificate_other_txt": "社会保障(その他詳細)",
    # --- 2枚目 (目標: 参加) ---
    "goal_p_residence_chk": "目標:住居場所",
    "goal_p_residence_home_type_slct": "目標:住居(自宅)",
    "goal_p_residence_home_type_detachedhouse_slct": "目標:住居(自宅は戸建)",
    "goal_p_residence_home_type_apartment_slct": "目標:住居(自宅はマンション）",
    "goal_p_residence_facility_chk": "目標:住居(施設)",
    "goal_p_residence_other_chk": "目標:住居(その他)",
    # "goal_p_residence_slct": "目標:住居場所(選択)",
    "goal_p_residence_other_txt": "目標:住居(その他詳細)",
    "goal_p_return_to_work_chk": "目標:復職",
    "goal_p_return_to_work_status_current_job_chk": "目標:復職(現場復帰)",
    "goal_p_return_to_work_status_reassignment_chk": "目標:復職(配置転換)",
    "goal_p_return_to_work_status_new_job_chk": "目標:復職(転職)",
    "goal_p_return_to_work_status_not_possible_chk": "目標:復職(不可)",
    "goal_p_return_to_work_status_other_chk": "目標:復職(その他)",
    # "goal_p_return_to_work_status_slct": "目標:復職(選択)",
    "goal_p_return_to_work_status_other_txt": "目標:復職(その他詳細)",
    "goal_p_return_to_work_commute_change_chk": "目標:通勤方法変更",
    "goal_p_schooling_chk": "目標:就学",
    "goal_p_schooling_status_possible_chk": "目標:就学(可能)",
    "goal_p_schooling_status_needs_consideration_chk": "目標:就学(要配慮)",
    "goal_p_schooling_status_change_course_chk": "目標:就学(転校等)",
    "goal_p_schooling_status_not_possible_chk": "目標:就学(不可)",
    "goal_p_schooling_status_other_chk": "目標:就学(その他)",
    "goal_p_schooling_status_other_txt": "目標:就学(その他詳細)",
    "goal_p_schooling_destination_chk": "目標:通学先",
    "goal_p_schooling_destination_txt": "目標:通学先(詳細)",
    "goal_p_schooling_commute_change_chk": "目標:通学方法変更",
    "goal_p_schooling_commute_change_txt": "目標:通学方法変更(詳細)",
    "goal_p_household_role_chk": "目標:家庭内役割",
    "goal_p_household_role_txt": "目標:家庭内役割(詳細)",
    "goal_p_social_activity_chk": "目標:社会活動",
    "goal_p_social_activity_txt": "目標:社会活動(詳細)",
    "goal_p_hobby_chk": "目標:趣味",
    "goal_p_hobby_txt": "目標:趣味(詳細)",
    # 2枚目 (目標: 活動)
    "goal_a_bed_mobility_chk": "活動目標:床上移動",
    "goal_a_bed_mobility_independent_chk": "活動目標:床上移動(自立)",
    "goal_a_bed_mobility_assistance_chk": "活動目標:床上移動(介助)",
    "goal_a_bed_mobility_not_performed_chk": "活動目標:床上移動(非実施)",
    "goal_a_bed_mobility_equipment_chk": "活動目標:床上移動(用具)",
    "goal_a_bed_mobility_environment_setup_chk": "活動目標:床上移動(環境設定)",
    "goal_a_indoor_mobility_chk": "活動目標:屋内移動",
    "goal_a_indoor_mobility_independent_chk": "活動目標:屋内移動(自立)",
    "goal_a_indoor_mobility_assistance_chk": "活動目標:屋内移動(介助)",
    "goal_a_indoor_mobility_not_performed_chk": "活動目標:屋内移動(非実施)",
    "goal_a_indoor_mobility_equipment_chk": "活動目標:屋内移動(用具)",
    "goal_a_indoor_mobility_equipment_txt": "活動目標:屋内移動(用具詳細)",
    "goal_a_outdoor_mobility_chk": "活動目標:屋外移動",
    "goal_a_outdoor_mobility_independent_chk": "活動目標:屋外移動(自立)",
    "goal_a_outdoor_mobility_assistance_chk": "活動目標:屋外移動(介助)",
    "goal_a_outdoor_mobility_not_performed_chk": "活動目標:屋外移動(非実施)",
    "goal_a_outdoor_mobility_equipment_chk": "活動目標:屋外移動(用具)",
    "goal_a_outdoor_mobility_equipment_txt": "活動目標:屋外移動(用具詳細)",
    "goal_a_driving_chk": "活動目標:自動車運転",
    "goal_a_driving_independent_chk": "活動目標:自動車運転(自立)",
    "goal_a_driving_assistance_chk": "活動目標:自動車運転(介助)",
    "goal_a_driving_not_performed_chk": "活動目標:自動車運転(非実施)",
    "goal_a_driving_modification_chk": "活動目標:自動車運転(改造)",
    "goal_a_driving_modification_txt": "活動目標:自動車運転(改造詳細)",
    "goal_a_public_transport_chk": "活動目標:公共交通",
    "goal_a_public_transport_independent_chk": "活動目標:公共交通(自立)",
    "goal_a_public_transport_assistance_chk": "活動目標:公共交通(介助)",
    "goal_a_public_transport_not_performed_chk": "活動目標:公共交通(非実施)",
    "goal_a_public_transport_type_chk": "活動目標:公共交通(種類)",
    "goal_a_public_transport_type_txt": "活動目標:公共交通(種類詳細)",
    "goal_a_toileting_chk": "活動目標:排泄",
    "goal_a_toileting_independent_chk": "活動目標:排泄(自立)",
    "goal_a_toileting_assistance_chk": "活動目標:排泄(介助)",
    "goal_a_toileting_assistance_clothing_chk": "活動目標:排泄(下衣操作)",
    "goal_a_toileting_assistance_wiping_chk": "活動目標:排泄(清拭)",
    "goal_a_toileting_assistance_catheter_chk": "活動目標:排泄(カテーテル)",
    "goal_a_toileting_type_chk": "活動目標:排泄(種類)",
    "goal_a_toileting_type_western_chk": "活動目標:排泄(洋式)",
    "goal_a_toileting_type_japanese_chk": "活動目標:排泄(和式)",
    "goal_a_toileting_type_other_chk": "活動目標:排泄(その他)",
    "goal_a_toileting_type_other_txt": "活動目標:排泄(その他詳細)",
    "goal_a_eating_chk": "活動目標:食事",
    "goal_a_eating_independent_chk": "活動目標:食事(自立)",
    "goal_a_eating_assistance_chk": "活動目標:食事(介助)",
    "goal_a_eating_not_performed_chk": "活動目標:食事(非実施)",
    "goal_a_eating_method_chopsticks_chk": "活動目標:食事(箸)",
    "goal_a_eating_method_fork_etc_chk": "活動目標:食事(フォーク等)",
    "goal_a_eating_method_tube_feeding_chk": "活動目標:食事(経管)",
    "goal_a_eating_diet_form_txt": "活動目標:食事(形態)",
    "goal_a_grooming_chk": "活動目標:整容",
    "goal_a_grooming_independent_chk": "活動目標:整容(自立)",
    "goal_a_grooming_assistance_chk": "活動目標:整容(介助)",
    "goal_a_dressing_chk": "活動目標:更衣",
    "goal_a_dressing_independent_chk": "活動目標:更衣(自立)",
    "goal_a_dressing_assistance_chk": "活動目標:更衣(介助)",
    "goal_a_bathing_chk": "活動目標:入浴",
    "goal_a_bathing_independent_chk": "活動目標:入浴(自立)",
    "goal_a_bathing_assistance_chk": "活動目標:入浴(介助)",
    "goal_a_bathing_type_tub_chk": "活動目標:入浴(浴槽)",
    "goal_a_bathing_type_shower_chk": "活動目標:入浴(シャワー)",
    "goal_a_bathing_assistance_body_washing_chk": "活動目標:入浴(洗身介助)",
    "goal_a_bathing_assistance_transfer_chk": "活動目標:入浴(移乗介助)",
    "goal_a_housework_meal_chk": "活動目標:家事",
    "goal_a_housework_meal_all_chk": "活動目標:家事(全般)",
    "goal_a_housework_meal_not_performed_chk": "活動目標:家事(非実施)",
    "goal_a_housework_meal_partial_chk": "活動目標:家事(一部)",
    "goal_a_housework_meal_partial_txt": "活動目標:家事(一部詳細)",
    "goal_a_writing_chk": "活動目標:書字",
    "goal_a_writing_independent_chk": "活動目標:書字(自立)",
    "goal_a_writing_independent_after_hand_change_chk": "活動目標:書字(利き手交換)",
    "goal_a_writing_other_chk": "活動目標:書字(その他)",
    "goal_a_writing_other_txt": "活動目標:書字(その他詳細)",
    "goal_a_ict_chk": "活動目標:ICT",
    "goal_a_ict_independent_chk": "活動目標:ICT(自立)",
    "goal_a_ict_assistance_chk": "活動目標:ICT(介助)",
    "goal_a_communication_chk": "活動目標:意思疎通",
    "goal_a_communication_independent_chk": "活動目標:意思疎通(自立)",
    "goal_a_communication_assistance_chk": "活動目標:意思疎通(介助)",
    "goal_a_communication_device_chk": "活動目標:意思疎通(機器)",
    "goal_a_communication_letter_board_chk": "活動目標:意思疎通(文字盤)",
    "goal_a_communication_cooperation_chk": "活動目標:意思疎通(協力)",
    # --- 2枚目 (対応項目) ---
    "goal_s_psychological_support_chk": "対応:心理的支援",
    "goal_s_psychological_support_txt": "対応:心理的支援(詳細)",
    "goal_s_disability_acceptance_chk": "対応:障害受容",
    "goal_s_disability_acceptance_txt": "対応:障害受容(詳細)",
    "goal_s_psychological_other_chk": "対応:心理(その他)",
    "goal_s_psychological_other_txt": "対応:心理(その他詳細)",
    "goal_s_env_home_modification_chk": "対応:住宅改修",
    "goal_s_env_home_modification_txt": "対応:住宅改修(詳細)",
    "goal_s_env_assistive_device_chk": "対応:福祉機器",
    "goal_s_env_assistive_device_txt": "対応:福祉機器(詳細)",
    "goal_s_env_social_security_chk": "対応:社会保障",
    "goal_s_env_social_security_physical_disability_cert_chk": "対応:社会保障(身障手帳)",
    "goal_s_env_social_security_disability_pension_chk": "対応:社会保障(年金)",
    "goal_s_env_social_security_intractable_disease_cert_chk": "対応:社会保障(難病)",
    "goal_s_env_social_security_other_chk": "対応:社会保障(その他)",
    "goal_s_env_social_security_other_txt": "対応:社会保障(その他詳細)",
    "goal_s_env_care_insurance_chk": "対応:介護保険",
    "goal_s_env_care_insurance_details_txt": "対応:介護保険(詳細)",
    "goal_s_env_care_insurance_outpatient_rehab_chk": "対応:介護保険(通所リハ)",
    "goal_s_env_care_insurance_home_rehab_chk": "対応:介護保険(訪問リハ)",
    "goal_s_env_care_insurance_day_care_chk": "対応:介護保険(通所介護)",
    "goal_s_env_care_insurance_home_nursing_chk": "対応:介護保険(訪問看護)",
    "goal_s_env_care_insurance_home_care_chk": "対応:介護保険(訪問介護)",
    "goal_s_env_care_insurance_health_facility_chk": "対応:介護保険(老健)",
    "goal_s_env_care_insurance_nursing_home_chk": "対応:介護保険(特養)",
    "goal_s_env_care_insurance_care_hospital_chk": "対応:介護保険(医療院)",
    "goal_s_env_care_insurance_other_chk": "対応:介護保険(その他)",
    "goal_s_env_care_insurance_other_txt": "対応:介護保険(その他詳細)",
    "goal_s_env_disability_welfare_chk": "対応:障害福祉",
    "goal_s_env_disability_welfare_after_school_day_service_chk": "対応:障害福祉(放デイ)",
    "goal_s_env_disability_welfare_child_development_support_chk": "対応:障害福祉(児発)",
    "goal_s_env_disability_welfare_life_care_chk": "対応:障害福祉(生活介護)",
    "goal_s_env_disability_welfare_other_chk": "対応:障害福祉(その他)",
    "goal_s_env_other_chk": "対応:環境(その他)",
    "goal_s_env_other_txt": "対応:環境(その他詳細)",
    "goal_s_3rd_party_main_caregiver_chk": "対応:主介護者",
    "goal_s_3rd_party_main_caregiver_txt": "対応:主介護者(詳細)",
    "goal_s_3rd_party_family_structure_change_chk": "対応:家族構成変化",
    "goal_s_3rd_party_family_structure_change_txt": "対応:家族構成変化(詳細)",
    "goal_s_3rd_party_household_role_change_chk": "対応:役割変化",
    "goal_s_3rd_party_household_role_change_txt": "対応:役割変化(詳細)",
    "goal_s_3rd_party_family_activity_change_chk": "対応:家族活動変化",
    "goal_s_3rd_party_family_activity_change_txt": "対応:家族活動変化(詳細)",
}

CHECK_TO_TEXT_MAP = {
    "func_pain_chk": "func_pain_txt",
    "func_rom_limitation_chk": "func_rom_limitation_txt",
    "func_muscle_weakness_chk": "func_muscle_weakness_txt",
    "func_swallowing_disorder_chk": "func_swallowing_disorder_txt",
    "func_behavioral_psychiatric_disorder_chk": "func_behavioral_psychiatric_disorder_txt",
    "func_nutritional_disorder_chk": "func_nutritional_disorder_txt",
    "func_excretory_disorder_chk": "func_excretory_disorder_txt",
    "func_pressure_ulcer_chk": "func_pressure_ulcer_txt",
    "func_contracture_deformity_chk": "func_contracture_deformity_txt",
    "func_motor_muscle_tone_abnormality_chk": "func_motor_muscle_tone_abnormality_txt",
    "func_disorientation_chk": "func_disorientation_txt",
    "func_memory_disorder_chk": "func_memory_disorder_txt",
}

USER_INPUT_FIELDS = ["main_comorbidities_txt"]


# def _prepare_patient_facts(patient_data: dict) -> dict:
#     """プロンプトに渡すための患者の事実情報を整形する"""
#     logger.debug(f"therapist_notes received = '{str(patient_data.get('therapist_notes'))[:100]}...'")
#     therapist_notes = patient_data.get("therapist_notes", "").strip()

#     facts = {
#         "基本情報": {},
#         "心身機能・構造": {},
#         "基本動作": {},
#         "ADL評価": {"FIM(現在値)": {}, "BI(現在値)": {}},
#         "栄養状態": {},
#         "社会保障サービス": {},
#         "生活状況・目標(本人・家族)": {},
#         "担当者からの所見": therapist_notes if therapist_notes else "特になし",
#     }

#     # 年齢を5歳刻み（前半/後半）で丸める匿名化処理
#     age = patient_data.get("age")
#     if age is not None:
#         try:
#             age_int = int(age)
#             decade = (age_int // 10) * 10
#             if age_int % 10 < 5:
#                 half = "前半"
#             else:
#                 half = "後半"
#             facts["基本情報"]["年齢"] = f"{decade}代{half}"
#         except (ValueError, TypeError):
#             facts["基本情報"]["年齢"] = "不明"
#     else:
#         facts["基本情報"]["年齢"] = "不明"

#     facts["基本情報"]["性別"] = _format_value(patient_data.get("gender"))

#     # 1. チェックボックスと関連しない項目を先に埋める
#     for key, value in patient_data.items():
#         formatted_value = _format_value(value)
#         if formatted_value is None:
#             continue

#         if "_chk" in key or "_txt" in key and key in [t[1] for t in CHECK_TO_TEXT_MAP.items()]:
#             continue

#         jp_name = CELL_NAME_MAPPING.get(key)
#         if not jp_name:
#             continue

#         category = None
#         if key.startswith(("header_", "main_")):
#             category = "基本情報"
#         elif key.startswith("func_basic_"):
#             category = "基本動作"
#         elif key.startswith("nutrition_"):
#             category = "栄養状態"
#         elif key.startswith("social_"):
#             category = "社会保障サービス"
#         elif key.startswith("goal_p_"):
#             category = "生活状況・目標(本人・家族)"
#         elif key.startswith("func_"):
#             category = "心身機能・構造"

#         if category:
#             facts[category][jp_name] = formatted_value

#     # 2. チェックボックスの状態を最優先で反映
#     for chk_key, txt_key in CHECK_TO_TEXT_MAP.items():
#         jp_name = CELL_NAME_MAPPING.get(chk_key)
#         if not jp_name:
#             continue

#         is_checked_value = patient_data.get(chk_key)
#         is_truly_checked = str(is_checked_value).lower() in ["true", "1", "on"]

#         if not is_truly_checked:
#             continue

#         txt_value = patient_data.get(txt_key)
#         if not txt_value or txt_value.strip() == "特記なし":
#             facts["心身機能・構造"][jp_name] = (
#                 "あり（患者の他のデータに基づき、具体的な症状やADLへの影響を推測して記述してください）"
#             )
#         else:
#             facts["心身機能・構造"][jp_name] = txt_value

#     # 3. ADL評価スコアを抽出
#     for key, value in patient_data.items():
#         val = _format_value(value)
#         if val is not None and "_val" in key:
#             if "fim_current_val" in key:
#                 item_name = key.replace("adl_", "").replace("_fim_current_val", "").replace("_", " ").title()
#                 facts["ADL評価"]["FIM(現在値)"][item_name] = f"{val}点"
#             elif "bi_current_val" in key:
#                 item_name = key.replace("adl_", "").replace("_bi_current_val", "").replace("_", " ").title()
#                 facts["ADL評価"]["BI(現在値)"][item_name] = f"{val}点"

#     # 空のカテゴリやサブカテゴリを最終的に削除
#     facts = {k: v for k, v in facts.items() if v or k == "担当者からの所見"}
#     if "ADL評価" in facts:
#         facts["ADL評価"] = {k: v for k, v in facts["ADL評価"].items() if v}
#         if not facts["ADL評価"]:
#             del facts["ADL評価"]

#     if "心身機能・構造" in facts and not facts["心身機能・構造"]:
#         del facts["心身機能・構造"]

#     return facts


def _prepare_patient_facts(patient_data: dict) -> dict:
    """プロンプトに渡すための患者の事実情報を整形する"""

    logger.debug(f"therapist_notes received = '{str(patient_data.get('therapist_notes'))[:100]}...'")

    therapist_notes = patient_data.get("therapist_notes", "").strip()

    facts = {
        "基本情報": {},
        "心身機能・構造": {},
        "基本動作": {},
        "ADL評価": {"FIM(現在値)": {}, "BI(現在値)": {}},
        "栄養状態": {},
        "社会保障サービス": {},
        "目標（参加）": {},
        "目標（活動）": {},
        "目標（環境・対応）": {},
        "担当者からの所見": therapist_notes if therapist_notes else "特になし",
    }

    # 年齢の処理
    age = patient_data.get("age")
    if age is not None:
        try:
            age_int = int(age)
            decade = (age_int // 10) * 10
            if age_int % 10 < 5:
                half = "前半"
            else:
                half = "後半"
            facts["基本情報"]["年齢"] = f"{decade}代{half}"
        except (ValueError, TypeError):
            facts["基本情報"]["年齢"] = "不明"
    else:
        facts["基本情報"]["年齢"] = "不明"

    facts["基本情報"]["性別"] = _format_value(patient_data.get("gender"))

    # 1. 通常項目の処理（マッピング定義に基づいてデータを振り分け）
    for key, value in patient_data.items():
        formatted_value = _format_value(value)
        if formatted_value is None:
            continue

        # BooleanのFalse（"なし"）は、情報量削減のためスキップする（"あり"のみ伝える）
        if formatted_value == "なし":
            continue

        # 特殊なペア項目（痛みや可動域制限など、詳細テキストとセットのもの）は
        # 後述の「2.」で専用の処理を行うため、ここではスキップします。
        # ただし、"CHECK_TO_TEXT_MAP" に含まれていない独立したチェックボックス（目標など）はここで処理します。

        # キーがペアの「チェックボックス側」である場合
        if key in CHECK_TO_TEXT_MAP:
            continue
        # キーがペアの「テキスト詳細側」である場合
        if key in CHECK_TO_TEXT_MAP.values():
            continue

        jp_name = CELL_NAME_MAPPING.get(key)
        if not jp_name:
            continue

        category = None
        # プレフィックスでカテゴリを判定
        if key.startswith(("header_", "main_")):
            category = "基本情報"
        elif key.startswith("func_basic_"):
            category = "基本動作"
        elif key.startswith("nutrition_"):
            category = "栄養状態"
        elif key.startswith("social_"):
            category = "社会保障サービス"
        elif key.startswith("goal_p_"):
            category = "目標（参加）"
        elif key.startswith("goal_a_"):
            category = "目標（活動）"
        elif key.startswith("goal_s_"):
            category = "目標（環境・対応）"
        elif key.startswith("func_"):
            category = "心身機能・構造"

        if category:
            facts[category][jp_name] = formatted_value

    # 2. チェックボックス + テキストのペア項目を処理 (優先度高)
    #    痛みや可動域制限など、チェックがあるのに詳細がない場合に「推測して」という指示を入れる処理
    for chk_key, txt_key in CHECK_TO_TEXT_MAP.items():
        jp_name = CELL_NAME_MAPPING.get(chk_key)
        if not jp_name:
            continue

        is_checked_value = patient_data.get(chk_key)
        is_truly_checked = str(is_checked_value).lower() in ["true", "1", "on"]

        if not is_truly_checked:
            continue

        txt_value = patient_data.get(txt_key)
        # 詳細記述が空、または「特記なし」の場合は、AIに推論を促す
        if not txt_value or txt_value.strip() == "特記なし":
            facts["心身機能・構造"][jp_name] = (
                "あり（患者の他のデータに基づき、具体的な症状やADLへの影響を推測して記述してください）"
            )
        else:
            facts["心身機能・構造"][jp_name] = txt_value

    # 3. ADL評価スコアを抽出
    for key, value in patient_data.items():
        val = _format_value(value)
        if val is not None and "_val" in key:
            if "fim_current_val" in key:
                item_name = key.replace("adl_", "").replace("_fim_current_val", "").replace("_", " ").title()
                facts["ADL評価"]["FIM(現在値)"][item_name] = f"{val}点"
            elif "bi_current_val" in key:
                item_name = key.replace("adl_", "").replace("_bi_current_val", "").replace("_", " ").title()
                facts["ADL評価"]["BI(現在値)"][item_name] = f"{val}点"

    # 空のカテゴリを削除してJSONを綺麗にする
    facts = {k: v for k, v in facts.items() if v or k == "担当者からの所見"}

    if "ADL評価" in facts:
        facts["ADL評価"] = {k: v for k, v in facts["ADL評価"].items() if v}
        if not facts["ADL評価"]:
            del facts["ADL評価"]

    # 新しく追加したカテゴリも含め、中身がないカテゴリは削除
    for cat in [
        "基本情報",
        "心身機能・構造",
        "基本動作",
        "栄養状態",
        "社会保障サービス",
        "目標（参加）",
        "目標（活動）",
        "目標（環境・対応）",
    ]:
        if cat in facts and not facts[cat]:
            del facts[cat]

    return facts


# --- Ollama用関数 ---


def _build_ollama_group_prompt(group_schema: type[BaseModel], patient_facts_str: str, generated_plan_so_far: dict) -> str:
    """Ollama用のグループ生成プロンプトを構築する"""
    return textwrap.dedent(f"""
        # 役割
        あなたは、患者様とそのご家族にリハビリテーション計画を説明する、経験豊富で説明上手なリハビリテーション科の専門医です。
        専門用語を避け、誰にでも理解できる平易な言葉で、誠実かつ丁寧に説明する文章を使用して、患者の個別性を最大限に尊重し、一貫性のあるリハビリテーション総合実施計画書を作成してください。

        # 患者データ (事実情報)
        ```json
        {patient_facts_str}
        ```

        # これまでの生成結果 (参考にしてください)
        ```json
        {json.dumps(generated_plan_so_far, indent=2, ensure_ascii=False, default=str)}
        ```

        # 作成指示
        上記の「患者データ」と「これまでの生成結果」を統合的に解釈し、**以下のJSONスキーマで定義されている項目のみ**を日本語で生成してください。
        - **最重要**: 生成する文章は、患者様やそのご家族が直接読んでも理解できるよう、**専門用語を避け、できるだけ平易な言葉で記述してください**。
        - ただし、**病名や疾患名はそのまま使用してください**。
        - 患者データから判断して該当しない、または情報が不足している場合は、必ず「特記なし」とだけ記述してください。
        - スキーマの`description`をよく読み、具体的で分かりやすい内容を記述してください。
        - 各項目は、他の項目との関連性や一貫性を保つように記述してください。

        ```json
        {json.dumps(group_schema.model_json_schema(), indent=2, ensure_ascii=False)}
        ```
        ---
        生成するJSON ({group_schema.__name__} の項目のみ):
    """)


def generate_ollama_plan_stream(patient_data: dict):
    """
    Ollamaを使用して計画案をグループごとに段階的に生成し、ストリーミングで返す関数。
    """
    if USE_DUMMY_DATA:
        print("--- ダミーデータを使用しています ---")
        dummy_plan = get_dummy_plan()
        for key, value in dummy_plan.items():
            time.sleep(0.05)
            event_data = json.dumps({"key": key, "value": value, "model_type": "ollama_general"})
            yield f"event: update\ndata: {event_data}\n\n"
        yield "event: finished\ndata: {}\n\n"
        return

    try:
        patient_facts = _prepare_patient_facts(patient_data)
        patient_facts_str = json.dumps(patient_facts, indent=2, ensure_ascii=False, default=str)
        generated_plan_so_far = {}

        # ユーザー入力項目を先に反映
        for field_name in USER_INPUT_FIELDS:
            if patient_data.get(field_name):
                value = patient_data[field_name]
                generated_plan_so_far[field_name] = value
                event_data = json.dumps({"key": field_name, "value": value, "model_type": "ollama_general"})
                yield f"event: update\ndata: {event_data}\n\n"

        max_retries = 10

        for group_schema in GENERATION_GROUPS:
            print(f"\n--- Ollama Generating Group: {group_schema.__name__} ---")
            
            for attempt in range(max_retries):
                try:
                    # プロンプト構築 (ループ内で毎回行う必要はないが、念のためここでも可)
                    prompt = _build_ollama_group_prompt(group_schema, patient_facts_str, generated_plan_so_far)
                    
                    # JSONモード切り替え
                    format_param = "json" if OLLAMA_USE_STRUCTURED_OUTPUT else None
                    if not OLLAMA_USE_STRUCTURED_OUTPUT:
                        prompt += "\n\nEnsure the output is a valid JSON object."

                    logger.info(f"--- Group: {group_schema.__name__} (Attempt: {attempt+1}/{max_retries}) ---")

                    print(prompt)
                    # API呼び出し
                    stream = ollama.chat(
                        model=OLLAMA_MODEL_NAME, 
                        messages=[{"role": "user", "content": prompt}], 
                        format=format_param, 
                        stream=True
                    )

                    accumulated_json_string = ""
                    for chunk in stream:
                        if chunk["message"]["content"]:
                            accumulated_json_string += chunk["message"]["content"]

                    logger.info(f"Ollama Raw Response:\n{accumulated_json_string}")

                    # パース処理 (前回の修正を適用)
                    raw_response_dict = {}
                    if OLLAMA_USE_STRUCTURED_OUTPUT:
                        raw_response_dict = json.loads(accumulated_json_string)
                    else:
                        raw_response_dict = extract_and_parse_json(accumulated_json_string)

                    data_to_validate: Dict[str, any] = {}

                    # ネスト構造の解決ロジック (そのまま)
                    if isinstance(raw_response_dict, dict):
                        schema_fields = set(group_schema.model_fields.keys())
                        response_keys = set(raw_response_dict.keys())
                        if schema_fields.issubset(response_keys):
                            data_to_validate = raw_response_dict
                        else:
                            schema_name_key = group_schema.__name__.lower()
                            if schema_name_key in raw_response_dict and isinstance(raw_response_dict[schema_name_key], dict):
                                data_to_validate = raw_response_dict[schema_name_key]
                            else:
                                nested_keys = ["properties", "attributes", "data"]
                                extracted = False
                                for key in nested_keys:
                                    if key in raw_response_dict and isinstance(raw_response_dict[key], dict):
                                        data_to_validate = raw_response_dict[key]
                                        extracted = True
                                        break
                                if not extracted:
                                    data_to_validate = raw_response_dict
                    else:
                        raise ValueError("Ollamaの応答が辞書形式ではありません。")

                    # Pydantic検証
                    group_result_obj = group_schema.model_validate(data_to_validate)
                    group_result_dict = group_result_obj.model_dump()
                    generated_plan_so_far.update(group_result_dict)

                    # ストリーム送信
                    for key, value in group_result_dict.items():
                        if value is not None:
                            event_data = json.dumps({"key": key, "value": str(value), "model_type": "ollama_general"})
                            yield f"event: update\ndata: {event_data}\n\n"
                    
                    print(f"--- Group {group_schema.__name__} processed successfully ---")
                    
                    # 成功したらリトライループを抜ける
                    break 

                except (ValidationError, json.JSONDecodeError, ValueError) as e:
                    print(f"エラー発生 (試行 {attempt+1}/{max_retries}): {e}")
                    logger.error(f"エラー詳細: {e}")
                    
                    # 最大回数に達したらエラーを通知して次のグループへ
                    if attempt == max_retries - 1:
                        error_message = f"グループ {group_schema.__name__} の生成に失敗しました (リトライ上限到達): {e}"
                        error_event = f"event: error\ndata: {json.dumps({'error': error_message})}\n\n"
                        yield error_event
                    else:
                        # リトライ前に少し待機
                        time.sleep(1)
                        continue

            time.sleep(1)  # グループ間の待機

        print("\n--- Ollamaによる全グループの生成完了 ---")
        # yield "event: finished\ndata: {}\n\n"
        yield "event: general_finished\ndata: {}\n\n"

    except Exception as e:
        print(f"Ollamaの段階的生成処理中に予期せぬエラーが発生しました: {e}")
        logger.error(f"Ollamaストリーム全体のエラー: {e}", exc_info=True)
        error_message = f"Ollama処理全体でエラーが発生しました: {e}"
        error_event = f"event: error\ndata: {json.dumps({'error': error_message})}\n\n"
        yield error_event


def generate_rag_plan_stream(patient_data: dict, rag_executor: "RAGExecutor"):
    """
    指定されたRAGExecutorを使って、特化モデルによる計画案をストリーミングで生成する。
    gemini_client.pyの同名関数をOllama用に移植したもの。
    rag_executorが内部で使用するLLM（Ollama）を呼び出し、その結果をストリーミングする。
    """
    try:
        logger.info("\n--- Ollama RAGモデルによる生成を開始 ---")

        # 1. RAGの検索クエリとLLMへの入力用に、患者データを整形
        patient_facts = _prepare_patient_facts(patient_data)

        # 2. RAGExecutorを実行し、専門的な計画案と根拠情報を取得
        # rag_executor.execute() は、内部で設定されたLLM (この場合はOllama) を呼び出す
        rag_result = rag_executor.execute(patient_facts)

        specialized_plan_dict = rag_result.get("answer", {})
        contexts = rag_result.get("contexts", [])

        # 3. RAGの実行結果をフロントエンドに送信
        if "error" in specialized_plan_dict:
            # RAG実行の内部でエラーが発生した場合
            error_msg = f"RAG Executorからのエラー: {specialized_plan_dict['error']}"
            logger.error(error_msg)

            # エラーをフロントエンドに通知
            rag_keys = [f.name for f in RehabPlanSchema.model_fields.values()]
            for key in rag_keys:
                error_value = f"RAGエラー: {specialized_plan_dict['error']}"
                event_data = json.dumps({"key": key, "value": error_value, "model_type": "ollama_specialized"})
                yield f"event: update\ndata: {event_data}\n\n"
        else:
            # 成功した場合、取得した辞書を項目ごとにストリームに流す
            logger.info("RAG Executorによる生成成功。結果をストリーミングします。")
            for key, value in specialized_plan_dict.items():
                event_data = json.dumps({"key": key, "value": str(value), "model_type": "ollama_specialized"})
                yield f"event: update\ndata: {event_data}\n\n"

            # 根拠情報(contexts)が存在すれば、それもフロントエンドに送信する
            if contexts:
                logger.info(f"{len(contexts)}件の根拠情報を送信します。")
                contexts_for_frontend = []
                for i, ctx in enumerate(contexts):
                    metadata = ctx.get("metadata", {})
                    contexts_for_frontend.append(
                        {
                            "id": i + 1,
                            "content": ctx.get("content", ""),
                            "source": metadata.get("source", "N/A"),
                            "disease": metadata.get("disease", "N/A"),
                            "section": metadata.get("section", "N/A"),
                            "subsection": metadata.get("subsection", "N/A"),
                            "subsubsection": metadata.get("subsubsection", "N/A"),
                        }
                    )

                context_event_data = json.dumps(contexts_for_frontend)
                yield f"event: context_update\ndata: {context_event_data}\n\n"

    except Exception as e:
        # RAGExecutorの初期化失敗など、この関数全体に関わるエラーが発生した場合
        logger.error(f"Ollama RAGストリームの実行中に致命的なエラーが発生しました: {e}", exc_info=True)
        # RAGが担当する全項目にエラーメッセージを送信
        rag_keys = [f.name for f in RehabPlanSchema.model_fields.values()]
        for key in rag_keys:
            error_value = f"RAG実行エラー: {e}"
            event_data = json.dumps({"key": key, "value": error_value, "model_type": "ollama_specialized"})
            yield f"event: update\ndata: {event_data}\n\n"

    finally:
        # 成功・失敗にかかわらず、RAG側の処理が完了したことを必ず通知する
        logger.info("Ollama RAGストリームが終了します。")
        yield "event: finished\ndata: {}\n\n"


def _build_ollama_regeneration_prompt(
    patient_facts_str: str,
    generated_plan_so_far: dict,
    item_key_to_regenerate: str,
    current_text: str,
    instruction: str,
    rag_context: Optional[str] = None,
    schema: Optional[Type[BaseModel]] = None,
) -> str:  # noqa: E501
    """Ollama用の項目再生成プロンプトを構築する"""

    schema_json_str = ""
    if schema:
        try:
            schema_json_str = json.dumps(schema.model_json_schema(), indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"スキーマのJSONシリアル化に失敗: {e}")
            schema_json_str = f'{{"{item_key_to_regenerate}": "(文字列)"}}'  # フォールバック

    return textwrap.dedent(f"""
        # 役割
        あなたは、経験豊富なリハビリテーション科の専門医です。
        これから提示する「現在の文章」を、与えられた「修正指示」に従って、より質の高い内容に書き換えてください。
        ただし、文章全体の構成や他の項目との一貫性も考慮し、不自然にならないように修正してください。
        専門用語を避け、誰にでも理解できる平易な言葉遣いを心がけてください。

        # 患者データ (事実情報)
        ```json
        {patient_facts_str}
        ```

        # これまでの生成結果 (修正対象以外)
        ```json
        {json.dumps(generated_plan_so_far, indent=2, ensure_ascii=False, default=str)}
        ```

        {"# 参考情報 (専門知識)" if rag_context else ""}
        {
        f'''これは、あなたの知識を補うための専門的な参考情報です。この情報を最優先で活用し、より根拠のある文章に修正してください。
        ```text
        {rag_context}
        ```'''
        if rag_context
        else ""
    }

        # 修正対象の項目
        `{item_key_to_regenerate}`

        # 現在の文章
        ```text
        {current_text}
        ```

        # 修正指示
        `{instruction}`

        # 作成指示
        上記のすべての情報を踏まえ、「現在の文章」を「修正指示」に従って書き直し、以下のJSONスキーマに従って出力してください。
        JSONスキーマ:
        ```json
        {schema_json_str}
        ```
        ---
        生成するJSON:
    """)

def regenerate_ollama_plan_item_stream(
    patient_data: dict, item_key: str, current_text: str, instruction: str, rag_executor: Optional["RAGExecutor"] = None
):
    """
    Ollamaを使用して、指定された単一項目を再生成するストリーミング関数。
    """
    if USE_DUMMY_DATA:
        print(f"--- ダミーデータ（再生成）を使用しています --- (RAG: {'あり' if rag_executor else 'なし'})")
        dummy_text = f"【Ollama再生成ダミー】\n指示：'{instruction}'\n元：'{current_text[:30]}...'"
        for char in dummy_text:
            time.sleep(0.02)
            event_data = json.dumps({"key": item_key, "chunk": char})
            yield f"event: update\ndata: {event_data}\n\n"
        yield "event: finished\ndata: {}\n\n"
        return

    try:
        # 1. プロンプト用に患者の事実情報を整形
        patient_facts = _prepare_patient_facts(patient_data)
        patient_facts_str = json.dumps(patient_facts, indent=2, ensure_ascii=False, default=str)

        # 2. 「これまでの生成結果」を準備（再生成対象の項目は除く）
        generated_plan_so_far = patient_data.copy()
        if item_key in generated_plan_so_far:
            del generated_plan_so_far[item_key]

        # 3. RAGが指定されていれば、専門知識を検索
        rag_context_str = None
        model_type = "ollama_general"
        if rag_executor:
            model_type = "ollama_specialized"
            print("--- RAG再生成: 専門知識の検索を開始 ---")
            try:
                # rag_executor.executeは辞書を返す想定
                rag_result = rag_executor.execute(patient_facts)
                contexts = rag_result.get("contexts", [])
                if contexts:
                    # contextsが辞書(content, metadata)のリストであると仮定
                    rag_context_str = "\n\n".join([ctx.get("content", str(ctx)) for ctx in contexts])
                    print(f"--- RAG再生成: {len(contexts)}件の専門知識を発見 ---")
            except Exception as e:
                print(f"RAGExecutorの実行に失敗: {e}")
                logger.error(f"RAGExecutor実行エラー (再生成時): {e}")
                # RAGが失敗しても、コンテキストなしで続行する

        # 4. 再生成用の動的Pydanticスキーマを作成
        RegenerationSchema = create_model(
            f"RegenerationSchema_{item_key}",
            **{item_key: (str, Field(..., description=f"修正指示に基づいて書き直された'{item_key}'の新しい文章。"))},
        )

        # 5. 再生成用プロンプトの構築
        prompt = _build_ollama_regeneration_prompt(
            patient_facts_str=patient_facts_str,
            generated_plan_so_far=generated_plan_so_far,
            item_key_to_regenerate=item_key,
            current_text=current_text,
            instruction=instruction,
            rag_context=rag_context_str,
            schema=RegenerationSchema,
        )

        # JSONモード切り替え
        format_param = "json" if OLLAMA_USE_STRUCTURED_OUTPUT else None
        if not OLLAMA_USE_STRUCTURED_OUTPUT:
            prompt += "\n\nEnsure the output is a valid JSON object."

        max_retries = 10
        regenerated_text = ""

        for attempt in range(max_retries):
            try:
                logging.info(f"--- Regenerating Item: {item_key} (Model: {model_type}, Format: {format_param}, Attempt: {attempt+1}) ---")
                logging.info("Regeneration Prompt:\n" + prompt)

                print(prompt)

                # 6. API呼び出し実行 (Ollama, ストリーミング)
                stream = ollama.chat(
                    model=OLLAMA_MODEL_NAME, 
                    messages=[{"role": "user", "content": prompt}], 
                    format=format_param, 
                    stream=True
                )

                accumulated_json_string = ""
                for chunk in stream:
                    if chunk["message"]["content"]:
                        accumulated_json_string += chunk["message"]["content"]

                # 7. 結果のパースと検証
                logging.info(f"Ollama Regeneration Response: {accumulated_json_string}")

                json_data_raw = {}
                if OLLAMA_USE_STRUCTURED_OUTPUT:
                    json_data_raw = json.loads(accumulated_json_string)
                else:
                    # 非強制モード: 自作関数で抽出・パース
                    json_data_raw = extract_and_parse_json(accumulated_json_string)

                data_to_validate: Dict[str, any] = {}

                # Ollamaがスキーマキーでネストするパターンに対応
                if isinstance(json_data_raw, dict):
                    if item_key in json_data_raw and isinstance(json_data_raw[item_key], str):
                        # {"main_risks_txt": "..."} の形式
                        data_to_validate = json_data_raw
                    elif "properties" in json_data_raw and item_key in json_data_raw["properties"]:
                        # {"properties": {"main_risks_txt": "..."}} の形式
                        data_to_validate = json_data_raw["properties"]
                    else:
                        # ネストなしと仮定
                        data_to_validate = json_data_raw
                else:
                    raise ValueError("Ollamaの応答が予期しない形式です（辞書ではありません）。")

                validated_data = RegenerationSchema.model_validate(data_to_validate)
                regenerated_text = validated_data.model_dump().get(item_key, "")
                
                # 成功したらループを抜ける
                break

            except (json.JSONDecodeError, ValidationError, ValueError) as e:
                print(f"Ollama再生成エラー (試行 {attempt+1}/{max_retries}): {e}")
                logger.error(f"Ollama再生成エラー: {e}\nデータ: {accumulated_json_string}")
                
                if attempt == max_retries - 1:
                    # 最終失敗時はエラーテキストを設定
                    regenerated_text = f"エラー: 再生成に失敗しました。{e}"
                else:
                    time.sleep(1)
                    continue

        # 8. ストリーミング風に返す
        for char in regenerated_text:
            event_data = json.dumps({"key": item_key, "chunk": char, "model_type": model_type})
            yield f"event: update\ndata: {event_data}\n\n"

        yield "event: finished\ndata: {}\n\n"

    except Exception as e:
        print(f"再生成API呼び出し中に予期せぬエラーが発生しました: {e}")
        logger.error(f"Ollama再生成ストリーム全体のエラー: {e}", exc_info=True)
        error_message = f"AIとの通信中にエラーが発生しました: {e}"
        error_event = f"event: error\ndata: {json.dumps({'error': error_message})}\n\n"
        yield error_event

# --- テスト用ダミーデータ ---


def get_dummy_plan():
    """開発用のダミーの計画書データを返す"""
    return {
        "main_comorbidities_txt": "高血圧症、2型糖尿病（ユーザー入力）",
        "main_risks_txt": "（ダミー）高血圧症があり、訓練中の血圧変動に注意。転倒リスクも高いため、移動・移乗時は必ず見守りを行う。",
        "main_contraindications_txt": "（ダミー）右肩関節の可動域制限に対し、無理な他動運動は避けること。疼痛を誘発しない範囲で実施する。",
        "func_pain_txt": "（ダミー）右肩関節において、挙上120度以上でシャープな痛み(NRS 7/10)を認める。",
        "func_rom_limitation_txt": "（ダミー）右肩関節の挙上・外旋制限により、更衣（特に上衣の袖通し）や、洗髪、整髪動作に支障をきたしている。",
        "func_muscle_weakness_txt": "（ダミー）右肩周囲筋の筋力低下(MMT4レベル)により、物品の保持や高所へのリーチ動作が困難となっている。",
        "func_swallowing_disorder_txt": "（ダミー）嚥下調整食コード2-1であり、食事は刻み食・とろみ付きで提供。",
        "func_behavioral_psychiatric_disorder_txt": "（ダミー）注意障害があり、一つの課題に集中することが難しい。",
        "func_nutritional_disorder_txt": "特記なし",
        "func_excretory_disorder_txt": "特記なし",
        "func_pressure_ulcer_txt": "特記なし",
        "func_contracture_deformity_txt": "特記なし",
        "func_motor_muscle_tone_abnormality_txt": "特記なし",
        "func_disorientation_txt": "特記なし",
        "func_memory_disorder_txt": "特記なし",
        "adl_equipment_and_assistance_details_txt": "（ダミー）移乗：ベッドから車椅子への移乗は軽介助レベル。\n歩行：屋内はT字杖を使用し見守りレベル。",
        "goals_1_month_txt": "（ダミー）【ADL】トイレ動作が手すりを使用して見守りレベルで自立する。",
        "goals_at_discharge_txt": "（ダミー）自宅の環境（手すり設置後）にて、日中の屋内ADLが見守り〜自立レベルとなる。",
        "policy_treatment_txt": "（ダミー）残存機能の最大化とADL自立度向上を目的とし、特に移乗・歩行能力の再獲得に焦点を当てる。",
        "policy_content_txt": "（ダミー）・関節可動域訓練：右肩関節の疼痛のない範囲での自動介助運動\n・筋力増強訓練：右上下肢の漸増抵抗運動",
        "goal_a_action_plan_txt": "（ダミー）トイレ動作については、動作を口頭指示で分解し、一つ一つの動きを確認しながら反復練習を行う。",
        "goal_s_env_action_plan_txt": "（ダミー）退院前訪問指導を計画し、家屋内の手すり設置場所（トイレ、廊下）について本人・家族と検討する。",
        "goal_p_action_plan_txt": "特記なし",
        "goal_s_psychological_action_plan_txt": "特記なし",
        "goal_s_3rd_party_action_plan_txt": "特記なし",
    }


# このファイルが直接実行された場合のテストコード
if __name__ == "__main__":
    print("--- Ollama クライアント 段階的生成テスト実行 ---")

    sample_patient_data = {
        "name": "テスト患者",
        "age": 75,
        "gender": "男性",
        "header_disease_name_txt": "脳梗塞右片麻痺",
        "therapist_notes": "テスト用所見。本人の意欲は高い。",
        "func_pain_chk": True,
        "func_muscle_weakness_chk": True,
        "func_rom_limitation_chk": False,  # チェックなしの項目
    }

    USE_DUMMY_DATA = False  # Trueにするとダミーデータでテスト

    # Ollama用関数を呼び出す
    stream_generator = generate_ollama_plan_stream(sample_patient_data)

    print("\n--- ストリームイベント ---")
    final_plan = {}
    error = None
    for event in stream_generator:
        print(event.strip())
        if "event: update" in event:
            try:
                data_str = event.split("data: ", 1)[1].strip()
                data = json.loads(data_str)
                final_plan[data["key"]] = data["value"]
            except Exception as e:
                print(f"Updateイベント解析エラー: {e}")
        elif "event: error" in event:
            try:
                data_str = event.split("data: ", 1)[1].strip()
                error = json.loads(data_str)
                print(f"!!! エラー受信: {error}")
            except Exception as e:
                print(f"Errorイベント解析エラー: {e}")

    if error:
        print("\n--- テスト実行中にエラーが検出されました ---")
        pprint.pprint(error)
    else:
        print("\n--- テスト完了 ---")
        print("最終生成結果:")
        pprint.pprint(final_plan)

    # --- 再生成のテスト ---
    print("\n\n--- Ollama クライアント 再生成テスト実行 ---")

    # RAGExecutorのダミーモックを作成（実際のインポートを避けるため）
    class MockRAGExecutor:
        def execute(self, facts):
            print("[MockRAGExecutor] execute()が呼び出されました。")
            return {"answer": {}, "contexts": [{"content": "【RAGからのダミー専門知識】", "metadata": {}}]}

    try:
        regenerate_stream = regenerate_ollama_plan_item_stream(
            patient_data=sample_patient_data,
            item_key="main_risks_txt",
            current_text="（元のテキスト）転倒リスクに注意。",
            instruction="もっと具体的に、高血圧の視点も加えてください。",
            rag_executor=MockRAGExecutor(),  # モックインスタンスを渡す
        )

        print("\n--- 再生成ストリームイベント ---")
        regenerated_text = ""
        for event in regenerate_stream:
            print(event.strip())
            if "event: update" in event:
                try:
                    data_str = event.split("data: ", 1)[1].strip()
                    data = json.loads(data_str)
                    regenerated_text += data.get("chunk", "")
                except Exception as e:
                    print(f"Updateイベント解析エラー: {e}")

        print("\n--- 再生成テスト完了 ---")
        print(f"最終生成テキスト:\n{regenerated_text}")

    except Exception as e:
        print(f"\n--- 再生成テスト中にエラーが発生 ---: {e}")
