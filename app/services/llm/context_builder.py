import logging
from datetime import date
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# DBカラム名と日本語名のマッピング
# gemini_client.py および ollama_client.py から抽出
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

# チェックボックスと詳細テキストのペア定義
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

# ユーザー入力フィールド
USER_INPUT_FIELDS = ["main_comorbidities_txt"]


def format_value(value: Any) -> Optional[str]:
    """値を人間が読みやすい形に整形する"""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return "あり" if value else "なし"
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value)


def prepare_patient_facts(patient_data: Dict[str, Any]) -> Dict[str, Any]:
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
        # 新しく追加するカテゴリ
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

    facts["基本情報"]["性別"] = format_value(patient_data.get("gender"))

    # 1. 通常項目の処理（マッピング定義に基づいてデータを振り分け）
    for key, value in patient_data.items():
        formatted_value = format_value(value)
        if formatted_value is None or formatted_value == "なし":
            continue

        if key in CHECK_TO_TEXT_MAP or key in CHECK_TO_TEXT_MAP.values():
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

    # 2. チェックボックス + テキストのペア項目を処理
    for chk_key, txt_key in CHECK_TO_TEXT_MAP.items():
        jp_name = CELL_NAME_MAPPING.get(chk_key)
        if not jp_name:
            continue

        is_checked_value = patient_data.get(chk_key)
        is_truly_checked = str(is_checked_value).lower() in ["true", "1", "on"]

        if not is_truly_checked:
            continue

        txt_value = patient_data.get(txt_key)
        if not txt_value or txt_value.strip() == "特記なし":
            facts["心身機能・構造"][jp_name] = (
                "あり（患者の他のデータに基づき、具体的な症状やADLへの影響を推測して記述してください）"
            )
        else:
            facts["心身機能・構造"][jp_name] = txt_value

    # 3. ADL評価スコアを抽出
    for key, value in patient_data.items():
        val = format_value(value)
        if val is not None and "_val" in key:
            if "fim_current_val" in key:
                item_name = key.replace("adl_", "").replace("_fim_current_val", "").replace("_", " ").title()
                facts["ADL評価"]["FIM(現在値)"][item_name] = f"{val}点"
            elif "bi_current_val" in key:
                item_name = key.replace("adl_", "").replace("_bi_current_val", "").replace("_", " ").title()
                facts["ADL評価"]["BI(現在値)"][item_name] = f"{val}点"

    # 空のカテゴリを削除
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
