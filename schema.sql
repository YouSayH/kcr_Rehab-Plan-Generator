-- =================================================================
-- リハビリテーション総合実施計画書 自動作成システム用データベーススキーマ
-- =================================================================
-- TODO あくまでもテスト用に作ったものなので、作り直す必要があります。


-- 1. データベースの作成
CREATE DATABASE IF NOT EXISTS rehab_db CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE rehab_db;

SET NAMES utf8mb4;

-- 外部キー制約を一時的に無効化
SET FOREIGN_KEY_CHECKS = 0;

-- テーブルを削除
DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS staff;
DROP TABLE IF EXISTS staff_patients;
DROP TABLE IF EXISTS rehabilitation_plans;
DROP TABLE IF EXISTS liked_item_details;
DROP TABLE IF EXISTS regeneration_history;
DROP TABLE IF EXISTS suggestion_likes;

-- 外部キー制約を再度有効化
SET FOREIGN_KEY_CHECKS = 1;


-- =================================================================
-- 2. 患者マスターテーブル
-- =================================================================

CREATE TABLE IF NOT EXISTS patients (
    `patient_id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '患者を一意に識別するID',
    `name` VARCHAR(255) NOT NULL COMMENT '患者氏名',
    `date_of_birth` DATE NULL COMMENT '生年月日',
    `gender` VARCHAR(10) NULL COMMENT '性別 (例: 男, 女)',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'レコード作成日時'
) ENGINE = InnoDB COMMENT = '患者の基本情報を格納するマスターテーブル';




-- =================================================================
-- 3. 職員マスターテーブル
-- =================================================================
CREATE TABLE IF NOT EXISTS staff (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '職員を一意に識別するID',
    `username` VARCHAR(255) NOT NULL UNIQUE COMMENT 'ログイン用のユーザー名',
    `password` VARCHAR(255) NOT NULL COMMENT 'ハッシュ化されたパスワード',
    `occupation` VARCHAR(255) NOT NULL COMMENT '職種',
    `role` VARCHAR(50) NOT NULL DEFAULT 'general' COMMENT '役割 (admin, generalなど)',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'レコード作成日時',
    `session_token` VARCHAR(255) NULL COMMENT '同時ログイン防止用のセッショントークン',
    `must_change_password` BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'TRUEの間はパスワード変更画面以外を使用できない',
    `password_updated_at` TIMESTAMP NULL COMMENT '最後にパスワードを変更した日時',
    INDEX `idx_session_token` (`session_token`)
) ENGINE = InnoDB COMMENT = '職員（アプリのユーザー）情報を格納するテーブル';


-- =================================================================
-- 4. 職員と患者の関連テーブル (担当者機能のため追加)
-- =================================================================
CREATE TABLE IF NOT EXISTS staff_patients (
    `staff_id` INT NOT NULL COMMENT '外部キー (staffテーブルを参照)',
    `patient_id` INT NOT NULL COMMENT '外部キー (patientsテーブルを参照)',
    PRIMARY KEY (`staff_id`, `patient_id`),
    CONSTRAINT `fk_staff_id` FOREIGN KEY (`staff_id`) REFERENCES `staff` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_staff_patient_id` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`patient_id`) ON DELETE CASCADE
) ENGINE = InnoDB COMMENT = '職員と担当患者の関連を管理する中間テーブル';


-- =================================================================
-- 5. リハビリテーション計画書テーブル
-- =================================================================
CREATE TABLE IF NOT EXISTS rehabilitation_plans (
    `plan_id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '計画書を一意に識別するID',
    `patient_id` INT NOT NULL COMMENT '外部キー (patientsテーブルを参照)',
    `created_by_staff_id` INT NULL COMMENT '作成した職員のID (staffテーブル参照)',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'レコード作成日時',
    `liked_items_json` TEXT NULL COMMENT 'いいね情報のスナップショットをJSONで保存',

    -- 【1枚目】----------------------------------------------------
    -- ヘッダー・基本情報
    `header_evaluation_date` DATE NULL COMMENT '計画評価実施日',
    `header_disease_name_txt` TEXT NULL COMMENT '算定病名',
    `header_treatment_details_txt` TEXT NULL COMMENT '治療内容',
    `header_onset_date` DATE NULL COMMENT '発症日・手術日',
    `header_rehab_start_date` DATE NULL COMMENT 'リハ開始日',
    `header_therapy_pt_chk` BOOLEAN DEFAULT FALSE COMMENT '理学療法',
    `header_therapy_ot_chk` BOOLEAN DEFAULT FALSE COMMENT '作業療法',
    `header_therapy_st_chk` BOOLEAN DEFAULT FALSE COMMENT '言語療法',

    -- 併存疾患・リスク・特記事項 (AI生成 + ユーザー編集)
    `main_comorbidities_txt` TEXT NULL,
    `main_risks_txt` TEXT NULL,
    `main_contraindications_txt` TEXT NULL,

    -- 心身機能・構造
    `func_consciousness_disorder_chk` BOOLEAN DEFAULT FALSE,
    `func_consciousness_disorder_jcs_gcs_txt` VARCHAR(255) NULL,
    `func_respiratory_disorder_chk` BOOLEAN DEFAULT FALSE,
    `func_respiratory_o2_therapy_chk` BOOLEAN DEFAULT FALSE,
    `func_respiratory_o2_therapy_l_min_txt` VARCHAR(255) NULL,
    `func_respiratory_tracheostomy_chk` BOOLEAN DEFAULT FALSE,
    `func_respiratory_ventilator_chk` BOOLEAN DEFAULT FALSE,
    `func_circulatory_disorder_chk` BOOLEAN DEFAULT FALSE,
    `func_circulatory_ef_chk` BOOLEAN DEFAULT FALSE,
    `func_circulatory_ef_val` INT NULL,
    `func_circulatory_arrhythmia_chk` BOOLEAN DEFAULT FALSE,
    `func_circulatory_arrhythmia_status_slct` VARCHAR(50) NULL,
    `func_risk_factors_chk` BOOLEAN DEFAULT FALSE,
    `func_risk_hypertension_chk` BOOLEAN DEFAULT FALSE,
    `func_risk_dyslipidemia_chk` BOOLEAN DEFAULT FALSE,
    `func_risk_diabetes_chk` BOOLEAN DEFAULT FALSE,
    `func_risk_smoking_chk` BOOLEAN DEFAULT FALSE,
    `func_risk_obesity_chk` BOOLEAN DEFAULT FALSE,
    `func_risk_hyperuricemia_chk` BOOLEAN DEFAULT FALSE,
    `func_risk_ckd_chk` BOOLEAN DEFAULT FALSE,
    `func_risk_family_history_chk` BOOLEAN DEFAULT FALSE,
    `func_risk_angina_chk` BOOLEAN DEFAULT FALSE,
    `func_risk_omi_chk` BOOLEAN DEFAULT FALSE,
    `func_risk_other_chk` BOOLEAN DEFAULT FALSE,
    `func_risk_other_txt` TEXT NULL,
    `func_swallowing_disorder_chk` BOOLEAN DEFAULT FALSE,
    `func_swallowing_disorder_txt` TEXT NULL,
    `func_nutritional_disorder_chk` BOOLEAN DEFAULT FALSE,
    `func_nutritional_disorder_txt` TEXT NULL,
    `func_excretory_disorder_chk` BOOLEAN DEFAULT FALSE,
    `func_excretory_disorder_txt` TEXT NULL,
    `func_pressure_ulcer_chk` BOOLEAN DEFAULT FALSE,
    `func_pressure_ulcer_txt` TEXT NULL,
    `func_pain_chk` BOOLEAN DEFAULT FALSE,
    `func_pain_txt` TEXT NULL,
    `func_other_chk` BOOLEAN DEFAULT FALSE,
    `func_other_txt` TEXT NULL,
    `func_rom_limitation_chk` BOOLEAN DEFAULT FALSE,
    `func_rom_limitation_txt` TEXT NULL,
    `func_contracture_deformity_chk` BOOLEAN DEFAULT FALSE,
    `func_contracture_deformity_txt` TEXT NULL,
    `func_muscle_weakness_chk` BOOLEAN DEFAULT FALSE,
    `func_muscle_weakness_txt` TEXT NULL,
    `func_motor_dysfunction_chk` BOOLEAN DEFAULT FALSE,
    `func_motor_paralysis_chk` BOOLEAN DEFAULT FALSE,
    `func_motor_involuntary_movement_chk` BOOLEAN DEFAULT FALSE,
    `func_motor_ataxia_chk` BOOLEAN DEFAULT FALSE,
    `func_motor_parkinsonism_chk` BOOLEAN DEFAULT FALSE,
    `func_motor_muscle_tone_abnormality_chk` BOOLEAN DEFAULT FALSE,
    `func_motor_muscle_tone_abnormality_txt` TEXT NULL,
    `func_sensory_dysfunction_chk` BOOLEAN DEFAULT FALSE,
    `func_sensory_hearing_chk` BOOLEAN DEFAULT FALSE,
    `func_sensory_vision_chk` BOOLEAN DEFAULT FALSE,
    `func_sensory_superficial_chk` BOOLEAN DEFAULT FALSE,
    `func_sensory_deep_chk` BOOLEAN DEFAULT FALSE,
    `func_speech_disorder_chk` BOOLEAN DEFAULT FALSE,
    `func_speech_articulation_chk` BOOLEAN DEFAULT FALSE,
    `func_speech_aphasia_chk` BOOLEAN DEFAULT FALSE,
    `func_speech_stuttering_chk` BOOLEAN DEFAULT FALSE,
    `func_speech_other_chk` BOOLEAN DEFAULT FALSE,
    `func_speech_other_txt` TEXT NULL,
    `func_higher_brain_dysfunction_chk` BOOLEAN DEFAULT FALSE,
    `func_higher_brain_memory_chk` BOOLEAN DEFAULT FALSE,
    `func_higher_brain_attention_chk` BOOLEAN DEFAULT FALSE,
    `func_higher_brain_apraxia_chk` BOOLEAN DEFAULT FALSE,
    `func_higher_brain_agnosia_chk` BOOLEAN DEFAULT FALSE,
    `func_higher_brain_executive_chk` BOOLEAN DEFAULT FALSE,
    `func_behavioral_psychiatric_disorder_chk` BOOLEAN DEFAULT FALSE,
    `func_behavioral_psychiatric_disorder_txt` TEXT NULL,
    `func_disorientation_chk` BOOLEAN DEFAULT FALSE,
    `func_disorientation_txt` TEXT NULL,
    `func_memory_disorder_chk` BOOLEAN DEFAULT FALSE,
    `func_memory_disorder_txt` TEXT NULL,
    `func_developmental_disorder_chk` BOOLEAN DEFAULT FALSE,
    `func_developmental_asd_chk` BOOLEAN DEFAULT FALSE,
    `func_developmental_ld_chk` BOOLEAN DEFAULT FALSE,
    `func_developmental_adhd_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_rolling_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_rolling_independent_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_rolling_partial_assistance_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_rolling_assistance_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_rolling_not_performed_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_getting_up_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_getting_up_independent_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_getting_up_partial_assistance_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_getting_up_assistance_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_getting_up_not_performed_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_standing_up_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_standing_up_independent_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_standing_up_partial_assistance_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_standing_up_assistance_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_standing_up_not_performed_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_sitting_balance_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_sitting_balance_independent_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_sitting_balance_partial_assistance_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_sitting_balance_assistance_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_sitting_balance_not_performed_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_standing_balance_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_standing_balance_independent_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_standing_balance_partial_assistance_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_standing_balance_assistance_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_standing_balance_not_performed_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_other_chk` BOOLEAN DEFAULT FALSE,
    `func_basic_other_txt` TEXT NULL,

    -- ADL (FIM/BI)
    `adl_eating_fim_start_val` INT NULL, `adl_eating_fim_current_val` INT NULL, `adl_eating_bi_start_val` INT NULL, `adl_eating_bi_current_val` INT NULL,
    `adl_grooming_fim_start_val` INT NULL, `adl_grooming_fim_current_val` INT NULL, `adl_grooming_bi_start_val` INT NULL, `adl_grooming_bi_current_val` INT NULL,
    `adl_bathing_fim_start_val` INT NULL, `adl_bathing_fim_current_val` INT NULL, `adl_bathing_bi_start_val` INT NULL, `adl_bathing_bi_current_val` INT NULL,
    `adl_dressing_upper_fim_start_val` INT NULL, `adl_dressing_upper_fim_current_val` INT NULL,
    `adl_dressing_lower_fim_start_val` INT NULL, `adl_dressing_lower_fim_current_val` INT NULL,
    `adl_dressing_bi_start_val` INT NULL, `adl_dressing_bi_current_val` INT NULL,
    `adl_toileting_fim_start_val` INT NULL, `adl_toileting_fim_current_val` INT NULL, `adl_toileting_bi_start_val` INT NULL, `adl_toileting_bi_current_val` INT NULL,
    `adl_bladder_management_fim_start_val` INT NULL, `adl_bladder_management_fim_current_val` INT NULL, `adl_bladder_management_bi_start_val` INT NULL, `adl_bladder_management_bi_current_val` INT NULL,
    `adl_bowel_management_fim_start_val` INT NULL, `adl_bowel_management_fim_current_val` INT NULL, `adl_bowel_management_bi_start_val` INT NULL, `adl_bowel_management_bi_current_val` INT NULL,
    `adl_transfer_bed_chair_wc_fim_start_val` INT NULL, `adl_transfer_bed_chair_wc_fim_current_val` INT NULL,
    `adl_transfer_toilet_fim_start_val` INT NULL, `adl_transfer_toilet_fim_current_val` INT NULL,
    `adl_transfer_tub_shower_fim_start_val` INT NULL, `adl_transfer_tub_shower_fim_current_val` INT NULL,
    `adl_transfer_bi_start_val` INT NULL, `adl_transfer_bi_current_val` INT NULL,
    `adl_locomotion_walk_walkingAids_wc_fim_start_val` INT NULL, `adl_locomotion_walk_walkingAids_wc_fim_current_val` INT NULL, `adl_locomotion_walk_walkingAids_wc_bi_start_val` INT NULL, `adl_locomotion_walk_walkingAids_wc_bi_current_val` INT NULL,
    `adl_locomotion_stairs_fim_start_val` INT NULL, `adl_locomotion_stairs_fim_current_val` INT NULL, `adl_locomotion_stairs_bi_start_val` INT NULL, `adl_locomotion_stairs_bi_current_val` INT NULL,
    `adl_comprehension_fim_start_val` INT NULL, `adl_comprehension_fim_current_val` INT NULL,
    `adl_expression_fim_start_val` INT NULL, `adl_expression_fim_current_val` INT NULL,
    `adl_social_interaction_fim_start_val` INT NULL, `adl_social_interaction_fim_current_val` INT NULL,
    `adl_problem_solving_fim_start_val` INT NULL, `adl_problem_solving_fim_current_val` INT NULL,
    `adl_memory_fim_start_val` INT NULL, `adl_memory_fim_current_val` INT NULL,
    `adl_equipment_and_assistance_details_txt` TEXT NULL,

    -- 栄養
    `nutrition_height_chk` BOOLEAN DEFAULT FALSE, `nutrition_height_val` DECIMAL(5,1) NULL,
    `nutrition_weight_chk` BOOLEAN DEFAULT FALSE, `nutrition_weight_val` DECIMAL(5,1) NULL,
    `nutrition_bmi_chk` BOOLEAN DEFAULT FALSE, `nutrition_bmi_val` DECIMAL(4,1) NULL,
    `nutrition_method_oral_chk` BOOLEAN DEFAULT FALSE, `nutrition_method_oral_meal_chk` BOOLEAN DEFAULT FALSE,
    `nutrition_method_oral_supplement_chk` BOOLEAN DEFAULT FALSE, `nutrition_method_tube_chk` BOOLEAN DEFAULT FALSE,
    `nutrition_method_iv_chk` BOOLEAN DEFAULT FALSE, `nutrition_method_iv_peripheral_chk` BOOLEAN DEFAULT FALSE,
    `nutrition_method_iv_central_chk` BOOLEAN DEFAULT FALSE, `nutrition_method_peg_chk` BOOLEAN DEFAULT FALSE,
    `nutrition_swallowing_diet_slct` VARCHAR(50) NULL COMMENT '嚥下調整食の選択',
    `nutrition_swallowing_diet_code_txt` VARCHAR(255) NULL,
    `nutrition_status_assessment_slct` VARCHAR(50) NULL COMMENT '栄養状態評価の選択',
    `nutrition_status_assessment_other_txt` TEXT NULL,
    `nutrition_required_energy_val` INT NULL, `nutrition_required_protein_val` INT NULL,
    `nutrition_total_intake_energy_val` INT NULL, `nutrition_total_intake_protein_val` INT NULL,

    -- 社会保障サービス
    `social_care_level_status_chk` BOOLEAN DEFAULT FALSE, `social_care_level_applying_chk` BOOLEAN DEFAULT FALSE,
    `social_care_level_support_chk` BOOLEAN DEFAULT FALSE, `social_care_level_support_num1_slct` BOOLEAN DEFAULT FALSE,
    `social_care_level_support_num2_slct` BOOLEAN DEFAULT FALSE, `social_care_level_care_slct` BOOLEAN DEFAULT FALSE,
    `social_care_level_care_num1_slct` BOOLEAN DEFAULT FALSE, `social_care_level_care_num2_slct` BOOLEAN DEFAULT FALSE,
    `social_care_level_care_num3_slct` BOOLEAN DEFAULT FALSE, `social_care_level_care_num4_slct` BOOLEAN DEFAULT FALSE,
    `social_care_level_care_num5_slct` BOOLEAN DEFAULT FALSE, `social_disability_certificate_physical_chk` BOOLEAN DEFAULT FALSE,
    `social_disability_certificate_physical_txt` TEXT NULL, `social_disability_certificate_physical_type_txt` VARCHAR(255) NULL,
    `social_disability_certificate_physical_rank_val` INT NULL, `social_disability_certificate_mental_chk` BOOLEAN DEFAULT FALSE,
    `social_disability_certificate_mental_rank_val` INT NULL, `social_disability_certificate_intellectual_chk` BOOLEAN DEFAULT FALSE,
    `social_disability_certificate_intellectual_txt` TEXT NULL, `social_disability_certificate_intellectual_grade_txt` VARCHAR(255) NULL,
    `social_disability_certificate_other_chk` BOOLEAN DEFAULT FALSE, `social_disability_certificate_other_txt` TEXT NULL,

    -- 目標・方針・署名
    `goals_1_month_txt` TEXT NULL, `goals_at_discharge_txt` TEXT NULL,
    `goals_planned_hospitalization_period_chk` BOOLEAN DEFAULT FALSE, `goals_planned_hospitalization_period_txt` TEXT NULL,
    `goals_discharge_destination_chk` BOOLEAN DEFAULT FALSE, `goals_discharge_destination_txt` TEXT NULL,
    `goals_long_term_care_needed_chk` BOOLEAN DEFAULT FALSE,
    `policy_treatment_txt` TEXT NULL, `policy_content_txt` TEXT NULL,
    `signature_rehab_doctor_txt` VARCHAR(255) NULL, `signature_primary_doctor_txt` VARCHAR(255) NULL,
    `signature_pt_txt` VARCHAR(255) NULL, `signature_ot_txt` VARCHAR(255) NULL,
    `signature_st_txt` VARCHAR(255) NULL, `signature_nurse_txt` VARCHAR(255) NULL,
    `signature_dietitian_txt` VARCHAR(255) NULL, `signature_social_worker_txt` VARCHAR(255) NULL,
    `signature_explained_to_txt` VARCHAR(255) NULL, `signature_explanation_date` DATE NULL, `signature_explainer_txt` VARCHAR(255) NULL,

    -- 【2枚目】----------------------------------------------------
    -- 目標(参加)
    `goal_p_residence_chk` BOOLEAN DEFAULT FALSE, `goal_p_residence_slct` VARCHAR(50) NULL,
    `goal_p_residence_other_txt` TEXT NULL, 
    `goal_p_return_to_work_chk` BOOLEAN DEFAULT FALSE,
    `goal_p_return_to_work_status_slct` VARCHAR(50) NULL, `goal_p_return_to_work_status_other_txt` TEXT NULL,
    `goal_p_return_to_work_commute_change_chk` BOOLEAN DEFAULT FALSE, `goal_p_schooling_chk` BOOLEAN DEFAULT FALSE,
    `goal_p_schooling_status_possible_chk` BOOLEAN DEFAULT FALSE, `goal_p_schooling_status_needs_consideration_chk` BOOLEAN DEFAULT FALSE,
    `goal_p_schooling_status_change_course_chk` BOOLEAN DEFAULT FALSE, `goal_p_schooling_status_not_possible_chk` BOOLEAN DEFAULT FALSE,
    `goal_p_schooling_status_other_chk` BOOLEAN DEFAULT FALSE, `goal_p_schooling_status_other_txt` TEXT NULL,
    `goal_p_schooling_destination_chk` BOOLEAN DEFAULT FALSE, `goal_p_schooling_destination_txt` TEXT NULL,
    `goal_p_schooling_commute_change_chk` BOOLEAN DEFAULT FALSE, `goal_p_schooling_commute_change_txt` TEXT NULL,
    `goal_p_household_role_chk` BOOLEAN DEFAULT FALSE, `goal_p_household_role_txt` TEXT NULL,
    `goal_p_social_activity_chk` BOOLEAN DEFAULT FALSE, `goal_p_social_activity_txt` TEXT NULL,
    `goal_p_hobby_chk` BOOLEAN DEFAULT FALSE, `goal_p_hobby_txt` TEXT NULL,

    -- 目標(活動)
    `goal_a_bed_mobility_chk` BOOLEAN DEFAULT FALSE, `goal_a_bed_mobility_independent_chk` BOOLEAN DEFAULT FALSE, `goal_a_bed_mobility_assistance_chk` BOOLEAN DEFAULT FALSE,
    `goal_a_bed_mobility_not_performed_chk` BOOLEAN DEFAULT FALSE, `goal_a_bed_mobility_equipment_chk` BOOLEAN DEFAULT FALSE, `goal_a_bed_mobility_environment_setup_chk` BOOLEAN DEFAULT FALSE,
    `goal_a_indoor_mobility_chk` BOOLEAN DEFAULT FALSE, `goal_a_indoor_mobility_independent_chk` BOOLEAN DEFAULT FALSE, `goal_a_indoor_mobility_assistance_chk` BOOLEAN DEFAULT FALSE,
    `goal_a_indoor_mobility_not_performed_chk` BOOLEAN DEFAULT FALSE, `goal_a_indoor_mobility_equipment_chk` BOOLEAN DEFAULT FALSE, `goal_a_indoor_mobility_equipment_txt` TEXT NULL,
    `goal_a_outdoor_mobility_chk` BOOLEAN DEFAULT FALSE, `goal_a_outdoor_mobility_independent_chk` BOOLEAN DEFAULT FALSE, `goal_a_outdoor_mobility_assistance_chk` BOOLEAN DEFAULT FALSE,
    `goal_a_outdoor_mobility_not_performed_chk` BOOLEAN DEFAULT FALSE, `goal_a_outdoor_mobility_equipment_chk` BOOLEAN DEFAULT FALSE, `goal_a_outdoor_mobility_equipment_txt` TEXT NULL,
    `goal_a_driving_chk` BOOLEAN DEFAULT FALSE, `goal_a_driving_independent_chk` BOOLEAN DEFAULT FALSE, `goal_a_driving_assistance_chk` BOOLEAN DEFAULT FALSE, `goal_a_driving_not_performed_chk` BOOLEAN DEFAULT FALSE,
    `goal_a_driving_modification_chk` BOOLEAN DEFAULT FALSE, `goal_a_driving_modification_txt` TEXT NULL, `goal_a_public_transport_chk` BOOLEAN DEFAULT FALSE,
    `goal_a_public_transport_independent_chk` BOOLEAN DEFAULT FALSE, `goal_a_public_transport_assistance_chk` BOOLEAN DEFAULT FALSE, `goal_a_public_transport_not_performed_chk` BOOLEAN DEFAULT FALSE,
    `goal_a_public_transport_type_chk` BOOLEAN DEFAULT FALSE, `goal_a_public_transport_type_txt` TEXT NULL, `goal_a_toileting_chk` BOOLEAN DEFAULT FALSE,
    `goal_a_toileting_independent_chk` BOOLEAN DEFAULT FALSE, `goal_a_toileting_assistance_chk` BOOLEAN DEFAULT FALSE, `goal_a_toileting_assistance_clothing_chk` BOOLEAN DEFAULT FALSE,
    `goal_a_toileting_assistance_wiping_chk` BOOLEAN DEFAULT FALSE, `goal_a_toileting_assistance_catheter_chk` BOOLEAN DEFAULT FALSE, `goal_a_toileting_type_chk` BOOLEAN DEFAULT FALSE,
    `goal_a_toileting_type_western_chk` BOOLEAN DEFAULT FALSE, `goal_a_toileting_type_japanese_chk` BOOLEAN DEFAULT FALSE, `goal_a_toileting_type_other_chk` BOOLEAN DEFAULT FALSE,
    `goal_a_toileting_type_other_txt` TEXT NULL, `goal_a_eating_chk` BOOLEAN DEFAULT FALSE, `goal_a_eating_independent_chk` BOOLEAN DEFAULT FALSE, `goal_a_eating_assistance_chk` BOOLEAN DEFAULT FALSE,
    `goal_a_eating_not_performed_chk` BOOLEAN DEFAULT FALSE, `goal_a_eating_method_chopsticks_chk` BOOLEAN DEFAULT FALSE, `goal_a_eating_method_fork_etc_chk` BOOLEAN DEFAULT FALSE,
    `goal_a_eating_method_tube_feeding_chk` BOOLEAN DEFAULT FALSE, `goal_a_eating_diet_form_txt` TEXT NULL, `goal_a_grooming_chk` BOOLEAN DEFAULT FALSE,
    `goal_a_grooming_independent_chk` BOOLEAN DEFAULT FALSE, `goal_a_grooming_assistance_chk` BOOLEAN DEFAULT FALSE, `goal_a_dressing_chk` BOOLEAN DEFAULT FALSE,
    `goal_a_dressing_independent_chk` BOOLEAN DEFAULT FALSE, `goal_a_dressing_assistance_chk` BOOLEAN DEFAULT FALSE, `goal_a_bathing_chk` BOOLEAN DEFAULT FALSE,
    `goal_a_bathing_independent_chk` BOOLEAN DEFAULT FALSE, `goal_a_bathing_assistance_chk` BOOLEAN DEFAULT FALSE, `goal_a_bathing_type_tub_chk` BOOLEAN DEFAULT FALSE,
    `goal_a_bathing_type_shower_chk` BOOLEAN DEFAULT FALSE, `goal_a_bathing_assistance_body_washing_chk` BOOLEAN DEFAULT FALSE, `goal_a_bathing_assistance_transfer_chk` BOOLEAN DEFAULT FALSE,
    `goal_a_housework_meal_chk` BOOLEAN DEFAULT FALSE, `goal_a_housework_meal_all_chk` BOOLEAN DEFAULT FALSE, `goal_a_housework_meal_not_performed_chk` BOOLEAN DEFAULT FALSE,
    `goal_a_housework_meal_partial_chk` BOOLEAN DEFAULT FALSE, `goal_a_housework_meal_partial_txt` TEXT NULL, `goal_a_writing_chk` BOOLEAN DEFAULT FALSE,
    `goal_a_writing_independent_chk` BOOLEAN DEFAULT FALSE, `goal_a_writing_independent_after_hand_change_chk` BOOLEAN DEFAULT FALSE, `goal_a_writing_other_chk` BOOLEAN DEFAULT FALSE,
    `goal_a_writing_other_txt` TEXT NULL, `goal_a_ict_chk` BOOLEAN DEFAULT FALSE, `goal_a_ict_independent_chk` BOOLEAN DEFAULT FALSE, `goal_a_ict_assistance_chk` BOOLEAN DEFAULT FALSE,
    `goal_a_communication_chk` BOOLEAN DEFAULT FALSE, `goal_a_communication_independent_chk` BOOLEAN DEFAULT FALSE, `goal_a_communication_assistance_chk` BOOLEAN DEFAULT FALSE,
    `goal_a_communication_device_chk` BOOLEAN DEFAULT FALSE, `goal_a_communication_letter_board_chk` BOOLEAN DEFAULT FALSE, `goal_a_communication_cooperation_chk` BOOLEAN DEFAULT FALSE,

    -- 対応を要する項目
    `goal_s_psychological_support_chk` BOOLEAN DEFAULT FALSE, `goal_s_psychological_support_txt` TEXT NULL, `goal_s_disability_acceptance_chk` BOOLEAN DEFAULT FALSE,
    `goal_s_disability_acceptance_txt` TEXT NULL, `goal_s_psychological_other_chk` BOOLEAN DEFAULT FALSE, `goal_s_psychological_other_txt` TEXT NULL,
    `goal_s_env_home_modification_chk` BOOLEAN DEFAULT FALSE, `goal_s_env_home_modification_txt` TEXT NULL, `goal_s_env_assistive_device_chk` BOOLEAN DEFAULT FALSE,
    `goal_s_env_assistive_device_txt` TEXT NULL, `goal_s_env_social_security_chk` BOOLEAN DEFAULT FALSE, `goal_s_env_social_security_physical_disability_cert_chk` BOOLEAN DEFAULT FALSE,
    `goal_s_env_social_security_disability_pension_chk` BOOLEAN DEFAULT FALSE, `goal_s_env_social_security_intractable_disease_cert_chk` BOOLEAN DEFAULT FALSE,
    `goal_s_env_social_security_other_chk` BOOLEAN DEFAULT FALSE, `goal_s_env_social_security_other_txt` TEXT NULL, `goal_s_env_care_insurance_chk` BOOLEAN DEFAULT FALSE,
    `goal_s_env_care_insurance_details_txt` TEXT NULL, `goal_s_env_care_insurance_outpatient_rehab_chk` BOOLEAN DEFAULT FALSE,
    `goal_s_env_care_insurance_home_rehab_chk` BOOLEAN DEFAULT FALSE, `goal_s_env_care_insurance_day_care_chk` BOOLEAN DEFAULT FALSE,
    `goal_s_env_care_insurance_home_nursing_chk` BOOLEAN DEFAULT FALSE, `goal_s_env_care_insurance_home_care_chk` BOOLEAN DEFAULT FALSE,
    `goal_s_env_care_insurance_health_facility_chk` BOOLEAN DEFAULT FALSE, `goal_s_env_care_insurance_nursing_home_chk` BOOLEAN DEFAULT FALSE,
    `goal_s_env_care_insurance_care_hospital_chk` BOOLEAN DEFAULT FALSE, `goal_s_env_care_insurance_other_chk` BOOLEAN DEFAULT FALSE,
    `goal_s_env_care_insurance_other_txt` TEXT NULL, `goal_s_env_disability_welfare_chk` BOOLEAN DEFAULT FALSE,
    `goal_s_env_disability_welfare_after_school_day_service_chk` BOOLEAN DEFAULT FALSE, `goal_s_env_disability_welfare_child_development_support_chk` BOOLEAN DEFAULT FALSE,
    `goal_s_env_disability_welfare_life_care_chk` BOOLEAN DEFAULT FALSE, `goal_s_env_disability_welfare_other_chk` BOOLEAN DEFAULT FALSE, `goal_s_env_other_chk` BOOLEAN DEFAULT FALSE,
    `goal_s_env_other_txt` TEXT NULL, `goal_s_3rd_party_main_caregiver_chk` BOOLEAN DEFAULT FALSE, `goal_s_3rd_party_main_caregiver_txt` TEXT NULL,
    `goal_s_3rd_party_family_structure_change_chk` BOOLEAN DEFAULT FALSE, `goal_s_3rd_party_family_structure_change_txt` TEXT NULL,
    `goal_s_3rd_party_household_role_change_chk` BOOLEAN DEFAULT FALSE, `goal_s_3rd_party_household_role_change_txt` TEXT NULL,
    `goal_s_3rd_party_family_activity_change_chk` BOOLEAN DEFAULT FALSE, `goal_s_3rd_party_family_activity_change_txt` TEXT NULL,

    -- 具体的な対応方針
    `goal_p_action_plan_txt` TEXT NULL, `goal_a_action_plan_txt` TEXT NULL, `goal_s_psychological_action_plan_txt` TEXT NULL,
    `goal_s_env_action_plan_txt` TEXT NULL, `goal_s_3rd_party_action_plan_txt` TEXT NULL,

    -- 外部キー制約
    INDEX `idx_plan_patient_id` (`patient_id`),
    CONSTRAINT `fk_plan_patient_id` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`patient_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_plan_staff_id` FOREIGN KEY (`created_by_staff_id`) REFERENCES `staff` (`id`) ON DELETE SET NULL
) ENGINE = InnoDB;


-- =================================================================
-- 6. AI提案 いいね評価テーブル (一時保存用)
-- =================================================================
-- ユーザーが計画書を確定するまでの間、「いいね」の評価状態を一時的に保存するテーブル。
CREATE TABLE IF NOT EXISTS suggestion_likes (
    `patient_id` INT NOT NULL COMMENT 'いいね評価の対象となる患者のID (patientsテーブル参照)',
    `item_key` VARCHAR(255) NOT NULL COMMENT 'いいねされた計画書項目のキー (例: main_risks_txt)',
    `liked_model` VARCHAR(50) NOT NULL COMMENT 'いいねされたAIモデルの種類 (general/specialized)',
    `staff_id` INT NOT NULL COMMENT 'いいね操作を行った職員のID (staffテーブル参照)',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'レコード作成日時',
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'レコード更新日時',

    -- 複合主キー: 1人の患者の1項目に対して、各モデルごとに1つの評価しかできないように制約
    PRIMARY KEY (`patient_id`, `item_key`, `liked_model`),

    -- 検索パフォーマンス向上のためのインデックス
    INDEX `idx_suggestion_like_staff_id` (`staff_id`),

    -- 外部キー制約: 関連する患者や職員が削除された場合に、このテーブルのデータも自動的に削除(CASCADE)される
    CONSTRAINT `fk_suggestion_like_patient_id` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`patient_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_suggestion_like_staff_id` FOREIGN KEY (`staff_id`) REFERENCES `staff` (`id`) ON DELETE CASCADE
) ENGINE = InnoDB COMMENT = 'AI提案への「いいね」評価を一時的に保存するテーブル';


-- =================================================================
-- 6. いいね詳細情報テーブル
-- =================================================================
CREATE TABLE IF NOT EXISTS liked_item_details (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT 'レコードを一意に識別するID',
    `rehabilitation_plan_id` INT NOT NULL COMMENT '関連する計画書のID',
    `staff_id` INT NOT NULL COMMENT 'いいねをした職員のID',
    `item_key` VARCHAR(255) NOT NULL COMMENT 'いいねされた項目キー',
    `liked_model` TEXT NULL COMMENT 'いいねされたモデル (カンマ区切り)',
    `general_suggestion_text` TEXT NULL COMMENT '通常モデルの提案内容',
    `specialized_suggestion_text` TEXT NULL COMMENT '特化モデルの提案内容',
    `therapist_notes_at_creation` TEXT NULL COMMENT '計画書作成時の所感',
    `patient_info_snapshot_json` JSON NULL COMMENT '計画書作成時の患者情報スナップショット',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'レコード作成日時',
    INDEX `idx_liked_plan_id` (`rehabilitation_plan_id`),
    INDEX `idx_liked_staff_id` (`staff_id`),
    CONSTRAINT `fk_liked_plan_id` FOREIGN KEY (`rehabilitation_plan_id`) REFERENCES `rehabilitation_plans` (`plan_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_liked_staff_id` FOREIGN KEY (`staff_id`) REFERENCES `staff` (`id`) ON DELETE CASCADE
) ENGINE = InnoDB COMMENT = 'いいね評価の詳細情報を格納するテーブル';

-- =================================================================
-- 再生成履歴テーブル
-- =================================================================
CREATE TABLE IF NOT EXISTS regeneration_history (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT 'レコードを一意に識別するID',
    `rehabilitation_plan_id` INT NOT NULL COMMENT '関連する計画書のID',
    `item_key` VARCHAR(255) NOT NULL COMMENT '再生成された項目キー',
    `model_type` VARCHAR(50) NOT NULL COMMENT '再生成に使用されたモデル (general/specialized)',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'レコード作成日時',

    INDEX `idx_regen_plan_id` (`rehabilitation_plan_id`),
    CONSTRAINT `fk_regen_plan_id` FOREIGN KEY (`rehabilitation_plan_id`) REFERENCES `rehabilitation_plans` (`plan_id`) ON DELETE CASCADE
) ENGINE = InnoDB COMMENT = 'AI提案の再生成履歴を格納するテーブル';
