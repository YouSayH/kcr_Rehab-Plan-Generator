import json
import time
import os
import sys
import re
from datetime import datetime
from dotenv import load_dotenv
from tqdm import tqdm

import gemini_client
import ollama_client
# マッピング定義を利用するためにインポート
from ollama_client import CELL_NAME_MAPPING

load_dotenv()

INPUT_FILE = "0_validation_dataset.json"
OUTPUT_DIR = "evaluation_results"

# CELL_NAME_MAPPINGの逆引き辞書を作成（日本語名 -> DBカラム名）
def normalize_key(key):
    """キーの表記揺れを吸収するための正規化関数"""
    return key.replace("（", "(").replace("）", ")").replace(" ", "").replace("　", "")

REVERSE_CELL_MAPPING = {normalize_key(v): k for k, v in CELL_NAME_MAPPING.items()}

# データセットの項目名(日本語)とDBカラム名のマッピングを明示的に定義
MANUAL_MAPPING = {
    # 基本情報
    "年齢": "age",
    "性別": "gender",
    "算定病名": "header_disease_name_txt",
    "治療内容": "header_treatment_details_txt",
    "発症日・手術日": "header_onset_date",
    "リハ開始日": "header_rehab_start_date",
    "実施療法(PT)": "header_therapy_pt_chk",
    "実施療法(OT)": "header_therapy_ot_chk",
    "実施療法(ST)": "header_therapy_st_chk",
    "併存疾患・合併症": "main_comorbidities_txt",

    # 心身機能（チェックボックス項目）
    "意識障害": "func_consciousness_disorder_chk",
    "呼吸機能障害": "func_respiratory_disorder_chk",
    "酸素療法": "func_respiratory_o2_therapy_chk",
    "気管切開": "func_respiratory_tracheostomy_chk",
    "人工呼吸器": "func_respiratory_ventilator_chk",
    "循環障害": "func_circulatory_disorder_chk",
    "心駆出率(EF)測定": "func_circulatory_ef_chk",
    "不整脈": "func_circulatory_arrhythmia_chk",
    "危険因子": "func_risk_factors_chk",
    "高血圧症": "func_risk_hypertension_chk",
    "脂質異常症": "func_risk_dyslipidemia_chk",
    "糖尿病": "func_risk_diabetes_chk",
    "喫煙": "func_risk_smoking_chk",
    "肥満": "func_risk_obesity_chk",
    "高尿酸血症": "func_risk_hyperuricemia_chk",
    "慢性腎臓病(CKD)": "func_risk_ckd_chk",
    "家族歴": "func_risk_family_history_chk",
    "狭心症": "func_risk_angina_chk",
    "陳旧性心筋梗塞": "func_risk_omi_chk",
    "危険因子(その他)": "func_risk_other_chk",
    "心身機能(その他)": "func_other_chk",
    "運動機能障害": "func_motor_dysfunction_chk",
    "麻痺": "func_motor_paralysis_chk",
    "不随意運動": "func_motor_involuntary_movement_chk",
    "運動失調": "func_motor_ataxia_chk",
    "パーキンソニズム": "func_motor_parkinsonism_chk",
    "感覚機能障害": "func_sensory_dysfunction_chk",
    "聴覚障害": "func_sensory_hearing_chk",
    "視覚障害": "func_sensory_vision_chk",
    "表在感覚障害": "func_sensory_superficial_chk",
    "深部感覚障害": "func_sensory_deep_chk",
    "音声発話障害": "func_speech_disorder_chk",
    "構音障害": "func_speech_articulation_chk",
    "失語症": "func_speech_aphasia_chk",
    "吃音": "func_speech_stuttering_chk",
    "音声発話(その他)": "func_speech_other_chk",
    "高次脳機能障害": "func_higher_brain_dysfunction_chk",
    "記憶障害(高次脳)": "func_higher_brain_memory_chk",
    "注意障害": "func_higher_brain_attention_chk",
    "失行": "func_higher_brain_apraxia_chk",
    "失認": "func_higher_brain_agnosia_chk",
    "遂行機能障害": "func_higher_brain_executive_chk",
    "発達障害": "func_developmental_disorder_chk",
    "自閉症スペクトラム症": "func_developmental_asd_chk",
    "学習障害": "func_developmental_ld_chk",
    "ADHD": "func_developmental_adhd_chk",

    # 心身機能（詳細テキスト）
    "疼痛": "func_pain_txt",
    "関節可動域制限": "func_rom_limitation_txt",
    "筋力低下": "func_muscle_weakness_txt",
    "摂食嚥下障害": "func_swallowing_disorder_txt",
    "精神行動障害": "func_behavioral_psychiatric_disorder_txt",
    "栄養障害": "func_nutritional_disorder_txt",
    "排泄機能障害": "func_excretory_disorder_txt",
    "褥瘡": "func_pressure_ulcer_txt",
    "拘縮・変形": "func_contracture_deformity_txt",
    "筋緊張異常": "func_motor_muscle_tone_abnormality_txt",
    "見当識障害": "func_disorientation_txt",
    "記憶障害": "func_memory_disorder_txt",
    
    # 心身機能（数値・選択）
    "意識障害(JCS/GCS)": "func_consciousness_disorder_jcs_gcs_txt",
    "酸素流量(L/min)": "func_respiratory_o2_therapy_l_min_txt",
    "心駆出率(EF)値": "func_circulatory_ef_val",

    # 基本動作（評価）
    "寝返り(評価)": "func_basic_rolling_chk",
    "起き上がり(評価)": "func_basic_getting_up_chk",
    "立ち上がり(評価)": "func_basic_standing_up_chk",
    "座位保持(評価)": "func_basic_sitting_balance_chk",
    "立位保持(評価)": "func_basic_standing_balance_chk",
    "基本動作(その他)": "func_basic_other_chk",
    
    # 基本動作（レベル）
    "寝返り(自立)": "func_basic_rolling_independent_chk",
    "寝返り(介助)": "func_basic_rolling_assistance_chk",
    "起き上がり(自立)": "func_basic_getting_up_independent_chk",
    "起き上がり(介助)": "func_basic_getting_up_assistance_chk",
    "立ち上がり(自立)": "func_basic_standing_up_independent_chk",
    "立ち上がり(介助)": "func_basic_standing_up_assistance_chk",
    "座位保持(自立)": "func_basic_sitting_balance_independent_chk",
    "座位保持(介助)": "func_basic_sitting_balance_assistance_chk",
    "立位保持(自立)": "func_basic_standing_balance_independent_chk",
    "立位保持(介助)": "func_basic_standing_balance_assistance_chk",

    # 栄養状態
    "身長測定": "nutrition_height_chk",
    "身長(cm)": "nutrition_height_val",
    "体重測定": "nutrition_weight_chk",
    "体重(kg)": "nutrition_weight_val",
    "BMI測定": "nutrition_bmi_chk",
    "BMI": "nutrition_bmi_val",
    "栄養補給(経口)": "nutrition_method_oral_chk",
    "経口(食事)": "nutrition_method_oral_meal_chk",
    "経口(補助食品)": "nutrition_method_oral_supplement_chk",
    "栄養補給(経管)": "nutrition_method_tube_chk",
    "栄養補給(静脈)": "nutrition_method_iv_chk",
    "静脈(末梢)": "nutrition_method_iv_peripheral_chk",
    "静脈(中心)": "nutrition_method_iv_central_chk",
    "栄養補給(胃ろう)": "nutrition_method_peg_chk",
    "嚥下調整食コード": "nutrition_swallowing_diet_code_txt",
    "必要熱量(kcal)": "nutrition_required_energy_val",
    "必要タンパク質量(g)": "nutrition_required_protein_val",
    "総摂取熱量(kcal)": "nutrition_total_intake_energy_val",
    "総摂取タンパク質量(g)": "nutrition_total_intake_protein_val",

    # 社会保障サービス
    "介護保険": "social_care_level_status_chk",
    "介護保険(申請中)": "social_care_level_applying_chk",
    "要支援": "social_care_level_support_chk",
    "要支援1": "social_care_level_support_num1_slct",
    "要支援2": "social_care_level_support_num2_slct",
    "要介護": "social_care_level_care_slct",
    "要介護1": "social_care_level_care_num1_slct",
    "要介護2": "social_care_level_care_num2_slct",
    "要介護3": "social_care_level_care_num3_slct",
    "要介護4": "social_care_level_care_num4_slct",
    "要介護5": "social_care_level_care_num5_slct",
    "身体障害者手帳": "social_disability_certificate_physical_chk",
    "身体障害者手帳(種別)": "social_disability_certificate_physical_type_txt",
    "身体障害者手帳(等級)": "social_disability_certificate_physical_rank_val",
    "精神障害者保健福祉手帳": "social_disability_certificate_mental_chk",
    "精神障害者手帳(等級)": "social_disability_certificate_mental_rank_val",
    "療育手帳": "social_disability_certificate_intellectual_chk",
    "療育手帳(障害程度)": "social_disability_certificate_intellectual_grade_txt",
    "社会保障(その他)": "social_disability_certificate_other_chk",
    "社会保障(その他詳細)": "social_disability_certificate_other_txt",

    # 目標（参加）
    "目標:住居場所": "goal_p_residence_chk",
    "目標:住居場所(自宅)": "goal_p_residence_home_type_slct", # 値としてhome_type_slctを使用
    "目標:復職": "goal_p_return_to_work_chk",
    "目標:復職(現場復帰)": "goal_p_return_to_work_status_current_job_chk",
    "目標:通勤方法変更": "goal_p_return_to_work_commute_change_chk",
    "目標:就学": "goal_p_schooling_chk",
    "目標:就学(可能)": "goal_p_schooling_status_possible_chk",
    "目標:通学先(詳細)": "goal_p_schooling_destination_txt",
    "目標:通学方法変更(詳細)": "goal_p_schooling_commute_change_txt",
    "目標:家庭内役割": "goal_p_household_role_chk",
    "目標:家庭内役割(詳細)": "goal_p_household_role_txt",
    "目標:社会活動": "goal_p_social_activity_chk",
    "目標:社会活動(詳細)": "goal_p_social_activity_txt",
    "目標:趣味": "goal_p_hobby_chk",
    "目標:趣味(詳細)": "goal_p_hobby_txt",

    # 目標（活動）
    "活動目標:床上移動": "goal_a_bed_mobility_chk",
    "活動目標:床上移動(自立)": "goal_a_bed_mobility_independent_chk",
    "活動目標:床上移動(用具)": "goal_a_bed_mobility_equipment_chk",
    "活動目標:床上移動(環境設定)": "goal_a_bed_mobility_environment_setup_chk",
    "活動目標:屋内移動": "goal_a_indoor_mobility_chk",
    "活動目標:屋内移動(自立)": "goal_a_indoor_mobility_independent_chk",
    "活動目標:屋内移動(用具)": "goal_a_indoor_mobility_equipment_chk",
    "活動目標:屋内移動(用具詳細)": "goal_a_indoor_mobility_equipment_txt",
    "活動目標:屋外移動": "goal_a_outdoor_mobility_chk",
    "活動目標:屋外移動(自立)": "goal_a_outdoor_mobility_independent_chk",
    "活動目標:屋外移動(用具)": "goal_a_outdoor_mobility_equipment_chk",
    "活動目標:屋外移動(用具詳細)": "goal_a_outdoor_mobility_equipment_txt",
    "活動目標:自動車運転": "goal_a_driving_chk",
    "活動目標:自動車運転(自立)": "goal_a_driving_independent_chk",
    "活動目標:自動車運転(改造)": "goal_a_driving_modification_chk",
    "活動目標:自動車運転(改造詳細)": "goal_a_driving_modification_txt",
    "活動目標:公共交通": "goal_a_public_transport_chk",
    "活動目標:公共交通(自立)": "goal_a_public_transport_independent_chk",
    "活動目標:公共交通(種類)": "goal_a_public_transport_type_chk",
    "活動目標:公共交通(種類詳細)": "goal_a_public_transport_type_txt",
    "活動目標:排泄": "goal_a_toileting_chk",
    "活動目標:排泄(自立)": "goal_a_toileting_independent_chk",
    "活動目標:排泄(下衣操作)": "goal_a_toileting_assistance_clothing_chk",
    "活動目標:排泄(清拭)": "goal_a_toileting_assistance_wiping_chk",
    "活動目標:排泄(カテーテル)": "goal_a_toileting_assistance_catheter_chk",
    "活動目標:排泄(種類)": "goal_a_toileting_type_chk",
    "活動目標:排泄(洋式)": "goal_a_toileting_type_western_chk",
    "活動目標:排泄(和式)": "goal_a_toileting_type_japanese_chk",
    "活動目標:排泄(その他)": "goal_a_toileting_type_other_chk",
    "活動目標:食事": "goal_a_eating_chk",
    "活動目標:食事(自立)": "goal_a_eating_independent_chk",
    "活動目標:食事(箸)": "goal_a_eating_method_chopsticks_chk",
    "活動目標:食事(形態)": "goal_a_eating_diet_form_txt",
    "活動目標:整容": "goal_a_grooming_chk",
    "活動目標:整容(介助)": "goal_a_grooming_assistance_chk",
    "活動目標:更衣": "goal_a_dressing_chk",
    "活動目標:更衣(介助)": "goal_a_dressing_assistance_chk",
    "活動目標:入浴": "goal_a_bathing_chk",
    "活動目標:入浴(介助)": "goal_a_bathing_assistance_chk",
    "活動目標:入浴(浴槽)": "goal_a_bathing_type_tub_chk",
    "活動目標:入浴(シャワー)": "goal_a_bathing_type_shower_chk",
    "活動目標:入浴(洗身介助)": "goal_a_bathing_assistance_body_washing_chk",
    "活動目標:入浴(移乗介助)": "goal_a_bathing_assistance_transfer_chk",
    "活動目標:家事": "goal_a_housework_meal_chk",
    "活動目標:家事(一部)": "goal_a_housework_meal_partial_chk",
    "活動目標:書字": "goal_a_writing_chk",
    "活動目標:書字(利き手交換)": "goal_a_writing_independent_after_hand_change_chk",
    "活動目標:ICT": "goal_a_ict_chk",
    "活動目標:ICT(介助)": "goal_a_ict_assistance_chk",
    "活動目標:意思疎通": "goal_a_communication_chk",
    "活動目標:意思疎通(介助)": "goal_a_communication_assistance_chk",
    "活動目標:意思疎通(機器)": "goal_a_communication_device_chk",
    "活動目標:意思疎通(文字盤)": "goal_a_communication_letter_board_chk",
    "活動目標:意思疎通(協力)": "goal_a_communication_cooperation_chk",

    # 目標（環境・対応）
    "対応:心理的支援": "goal_s_psychological_support_chk",
    "対応:障害受容": "goal_s_disability_acceptance_chk",
    "対応:心理(その他)": "goal_s_psychological_other_chk",
    "対応:福祉機器": "goal_s_env_assistive_device_chk",
    "対応:社会保障": "goal_s_env_social_security_chk",
    "対応:社会保障(身障手帳)": "goal_s_env_social_security_physical_disability_cert_chk",
    "対応:社会保障(年金)": "goal_s_env_social_security_disability_pension_chk",
    "対応:社会保障(難病)": "goal_s_env_social_security_intractable_disease_cert_chk",
    "対応:社会保障(その他)": "goal_s_env_social_security_other_chk",
    "対応:介護保険": "goal_s_env_care_insurance_chk",
    "対応:介護保険(通所リハ)": "goal_s_env_care_insurance_outpatient_rehab_chk",
    "対応:介護保険(訪問リハ)": "goal_s_env_care_insurance_home_rehab_chk",
    "対応:介護保険(通所介護)": "goal_s_env_care_insurance_day_care_chk",
    "対応:介護保険(訪問看護)": "goal_s_env_care_insurance_home_nursing_chk",
    "対応:介護保険(訪問介護)": "goal_s_env_care_insurance_home_care_chk",
    "対応:介護保険(老健)": "goal_s_env_care_insurance_health_facility_chk",
    "対応:介護保険(特養)": "goal_s_env_care_insurance_nursing_home_chk",
    "対応:介護保険(医療院)": "goal_s_env_care_insurance_care_hospital_chk",
    "対応:介護保険(その他)": "goal_s_env_care_insurance_other_chk",
    "対応:障害福祉": "goal_s_env_disability_welfare_chk",
    "対応:障害福祉(放デイ)": "goal_s_env_disability_welfare_after_school_day_service_chk",
    "対応:障害福祉(児発)": "goal_s_env_disability_welfare_child_development_support_chk",
    "対応:障害福祉(生活介護)": "goal_s_env_disability_welfare_life_care_chk",
    "対応:障害福祉(その他)": "goal_s_env_disability_welfare_other_chk",
    "対応:環境(その他)": "goal_s_env_other_chk",
    "対応:主介護者": "goal_s_3rd_party_main_caregiver_chk",
    "対応:家族構成変化": "goal_s_3rd_party_family_structure_change_chk",
    "対応:役割変化": "goal_s_3rd_party_household_role_change_chk",
    "対応:家族活動変化": "goal_s_3rd_party_family_activity_change_chk",
    
    "ADL(使用用具及び介助内容等)": "adl_equipment_and_assistance_details_txt"
}

def transform_dataset_to_api_format(input_context):
    """
    データセットのネストされた日本語構造を、ollama_clientが期待する
    フラットなDBカラム名形式の辞書に変換する
    """
    flat_data = {}
    
    # 1. 所感のコピー
    if "therapist_notes" in input_context:
        flat_data["therapist_notes"] = input_context["therapist_notes"]
        
    # 2. generated_plan_so_far の内容も統合
    if "generated_plan_so_far" in input_context:
        flat_data.update(input_context["generated_plan_so_far"])

    patient_facts = input_context.get("patient_facts", {})
    
    # 3. 各カテゴリを走査してマッピング
    for category, items in patient_facts.items():
        
        # --- 特殊処理: ADL評価 (ネストされたスコア) ---
        if category == "ADL評価":
            for sub_cat, sub_items in items.items():
                score_type = "" # fim or bi
                if "FIM" in sub_cat:
                    score_type = "fim"
                elif "BI" in sub_cat:
                    score_type = "bi"
                
                if score_type:
                    for jp_key, value in sub_items.items():
                        # "Eating" -> "eating"
                        normalized_key = jp_key.lower().replace(" ", "_")
                        # FIM/BIの項目名マッピング補正（必要に応じて）
                        if normalized_key == "transfer_bed_chair_wc": normalized_key = "transfer_bed_chair_wc"
                        if normalized_key == "locomotion_walk_walkingaids_wc": normalized_key = "locomotion_walk_walkingAids_wc"
                        if normalized_key == "locomotion_walk_walking_aids_wc": normalized_key = "locomotion_walk_walkingAids_wc" # 表記揺れ対応

                        db_key = f"adl_{normalized_key}_{score_type}_current_val"
                        
                        # 値から「点」を除去して数値化
                        clean_val = value
                        if isinstance(value, str) and value.endswith("点"):
                            try:
                                clean_val = int(value.replace("点", ""))
                            except ValueError:
                                pass
                        
                        flat_data[db_key] = clean_val
            continue

        # --- 特殊処理: ADL詳細テキスト ---
        if "ADL(使用用具及び介助内容等)" in category:
             combined_text = ""
             for k, v in items.items():
                 combined_text += f"{k}: {v}\n"
             flat_data["adl_equipment_and_assistance_details_txt"] = combined_text.strip()
             continue

        # --- 通常項目の処理 ---
        for jp_key, value in items.items():
            normalized_jp_key = normalize_key(jp_key)
            db_key = None
            
            # 1. マニュアルマッピング確認
            if normalized_jp_key in MANUAL_MAPPING:
                db_key = MANUAL_MAPPING[normalized_jp_key]
            elif jp_key in MANUAL_MAPPING: # 正規化前も確認
                db_key = MANUAL_MAPPING[jp_key]
            
            # 2. 自動逆引き確認
            elif normalized_jp_key in REVERSE_CELL_MAPPING:
                db_key = REVERSE_CELL_MAPPING[normalized_jp_key]
            
            # 変換できたキーに値をセット
            if db_key:
                flat_data[db_key] = value

                # 値が「あり」や数値が入っている場合、対応するチェックボックスをTrueにする
                # 例: func_pain_txt に値があれば、func_pain_chk を True にする
                if value and value != "なし":
                    # テキストフィールド (_txt) の場合
                    if db_key.endswith("_txt") and db_key.startswith("func_"):
                        chk_key = db_key.replace("_txt", "_chk")
                        flat_data[chk_key] = True
                    # 数値フィールド (_val) の場合
                    elif db_key.endswith("_val") and db_key.startswith("nutrition_"):
                        chk_key = db_key.replace("_val", "_chk")
                        flat_data[chk_key] = True
                    # "あり" の場合
                    elif value == "あり":
                         flat_data[db_key] = True
            else:
                # マッピングできなかった項目をログに出力
                print(f"[警告] マッピング失敗: {jp_key} (Category: {category})")
                         
    # 4. 栄養状態の親子関係の補正 (経口摂取など)
    if flat_data.get("nutrition_method_oral_meal_chk") or flat_data.get("nutrition_method_oral_supplement_chk"):
        flat_data["nutrition_method_oral_chk"] = True
    if flat_data.get("nutrition_method_iv_peripheral_chk") or flat_data.get("nutrition_method_iv_central_chk"):
        flat_data["nutrition_method_iv_chk"] = True

    return flat_data

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    if not os.path.exists(INPUT_FILE):
        print(f"エラー: データファイル {INPUT_FILE} が見つかりません。")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    client_type = os.getenv("LLM_CLIENT_TYPE", "gemini")
    model_name = "gemini-2.5-flash" if client_type == "gemini" else os.getenv("OLLAMA_MODEL_NAME", "unknown")
    
    print(f"--- 生成プロセス開始 ---")
    print(f"クライアント: {client_type}")
    print(f"モデル: {model_name}")
    print(f"データ件数: {len(dataset)}件")

    results = []

    for data in tqdm(dataset, desc="Generating"):
        case_id = data.get("case_id", "unknown")
        input_context = data.get("input_context", {})
        
        # データ構造変換処理を実行
        input_payload = transform_dataset_to_api_format(input_context)

        if client_type == "ollama":
            stream = ollama_client.generate_ollama_plan_stream(input_payload)
        else:
            stream = gemini_client.generate_general_plan_stream(input_payload)

        start_time = time.time()
        generated_content = {}
        error_msg = None

        try:
            for event in stream:
                if "event: update" in event:
                    lines = event.split('\n')
                    for line in lines:
                        if line.startswith("data:"):
                            json_str = line[len("data:"):].strip()
                            try:
                                event_data = json.loads(json_str)
                                key = event_data.get("key")
                                value = event_data.get("value")
                                if key and value:
                                    generated_content[key] = value
                            except json.JSONDecodeError:
                                pass
                elif "event: error" in event:
                     error_msg = event
        except Exception as e:
            print(f"生成エラー (ID: {case_id}): {e}")
            error_msg = str(e)

        end_time = time.time()
        duration = end_time - start_time
        
        if error_msg:
             generated_content["error"] = error_msg

        results.append({
            "case_id": case_id,
            "generation_time_sec": round(duration, 2),
            "model_name": model_name,
            "client_type": client_type,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "generated_plan": generated_content,
            "ground_truth": data.get("ground_truth", {}),
            "input_data_converted": input_payload # デバッグ用に変換後のデータも保存
        })
        
        if client_type == "gemini":
            time.sleep(2)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_model_name = model_name.replace(':', '-').replace('/', '_').replace('\\', '_')
    output_filename = f"{OUTPUT_DIR}/gen_{client_type}_{safe_model_name}_{timestamp}.json"
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n生成完了。結果を保存しました: {output_filename}")

if __name__ == "__main__":
    main()