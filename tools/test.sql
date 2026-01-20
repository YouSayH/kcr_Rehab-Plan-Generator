USE rehab_db;
SET NAMES utf8mb4;

-- username : test1
-- password : 1234

INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        101,
        'test1',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        101,
        '佐藤 健二',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (101, 101);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        101,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );



-- username : test2
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        102,
        'test2',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        102,
        '佐藤 健三',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (102, 102);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        102,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test3
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        103,
        'test3',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        103,
        '佐藤 健四',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (103, 103);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        104,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );



-- username : test4
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        104,
        'test4',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        104,
        '佐藤 健五',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (104, 104);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        105,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );



-- username : test5
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        105,
        'test5',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        105,
        '佐藤 健六',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (105, 105);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        105,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test6
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        106,
        'test6',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        106,
        '佐藤 健七',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (106, 106);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        106,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );



-- username : test7
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        107,
        'test7',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        107,
        '佐藤 健八',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (107, 107);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        107,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );



-- username : test8
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        108,
        'test8',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        108,
        '佐藤 健九',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (108, 108);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        108,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );



-- username : test9
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        109,
        'test9',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        109,
        '佐藤 健',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (109, 109);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        109,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test10
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        110,
        'test10',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        110,
        '佐藤 健太郎',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (110, 110);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        110,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );



-- username : test11
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        111,
        'test11',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        111,
        '佐藤 タロウ',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (111, 111);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        111,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test12
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        112,
        'test12',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        112,
        '佐藤 次郎',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (112, 112);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        112,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test13
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        113,
        'test13',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        113,
        '佐藤 二郎',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (113, 113);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        113,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test14
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        114,
        'test14',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        114,
        '佐藤 治郎',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (114, 114);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        114,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test15
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        115,
        'test15',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        115,
        '佐藤 三郎',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (115, 115);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        115,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );



-- username : test16
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        116,
        'test16',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        116,
        '佐藤 四郎',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (116, 116);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        116,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test17
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        117,
        'test17',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        117,
        '佐藤 五郎',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (117, 117);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        117,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test18
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        118,
        'test18',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        118,
        '佐藤 吾郎',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (118, 118);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        118,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test19
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        119,
        'test19',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        119,
        '佐藤 じろう',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (119, 119);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        119,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );



-- username : test20
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        120,
        'test20',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        120,
        '佐藤 たろう',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (120, 120);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        120,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );



-- username : test21
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        121,
        'test21',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        121,
        '佐藤 さぶろう',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (121, 121);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        121,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test22
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        122,
        'test22',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        122,
        '佐藤 サブロウ',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (122, 122);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        122,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test23
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        123,
        'test23',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        123,
        '佐藤',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (123, 123);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        123,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test24
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        124,
        'test24',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        124,
        '斎藤',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (124, 124);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        124,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test25
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        125,
        'test25',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        125,
        '佐々木',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (125, 125);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        125,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test26
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        126,
        'test26',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        126,
        '山田',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (126, 126);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        126,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test27
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        127,
        'test27',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        127,
        '山中',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (127, 127);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        127,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test28
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        128,
        'test28',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        128,
        '斉藤',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (128, 128);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        128,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test29
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        129,
        'test29',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        129,
        '田中',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (129, 129);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        129,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test30
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        130,
        'test30',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        130,
        '田中 タロウ',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (130, 130);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        130,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test31
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        131,
        'test31',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        131,
        '田中 太郎',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (131, 131);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        131,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );



-- username : test32
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        132,
        'test32',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        132,
        '田中 次郎',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (132, 132);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        132,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test33
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        133,
        'test33',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        133,
        '田中 さぶろう',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (133, 133);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        133,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test34
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        134,
        'test34',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        134,
        '田中 四郎',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (134, 134);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        134,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test35
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        135,
        'test35',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        135,
        '田中 シロウ',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (135, 135);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        135,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test36
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        136,
        'test36',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        136,
        '山田 次郎',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (136, 136);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        136,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test37
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        137,
        'test37',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        137,
        '山田 三郎',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (137, 137);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        137,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test38
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        138,
        'test38',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        138,
        '山田 健',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (138, 138);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        138,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test39
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        139,
        'test39',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        139,
        '山田 三郎',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (139, 139);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        139,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );


-- username : test40
-- password : 1234
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (
        140,
        'test40',
        'scrypt:32768:8:1$0QtDM5HWhwXYeWiP$e9dd38d0ee167df3589b9b9420c39d6db5857b2cd67f8d4b417f112dfe7d44e3455a136f695da8b52af63df87d7c92d3384e85052a323395485cc82be24078d3',
        '理学療法士',
        'admin'
    ) ON DUPLICATE KEY
UPDATE `username` = `username`,
    `occupation` = '理学療法士',
    `role` = 'admin';


-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        140,
        '佐藤 健二',
        '1957-11-05',
        '男'
    );
-- 2. 担当職員の関連付け (山田さんと佐藤さんが担当)
INSERT INTO staff_patients (`staff_id`, `patient_id`)
VALUES (140, 140);
-- 3. リハビリテーション計画書の登録
INSERT INTO rehabilitation_plans (
        `patient_id`,
        `created_by_staff_id`,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        `header_evaluation_date`,
        `header_disease_name_txt`,
        `header_onset_date`,
        `header_rehab_start_date`,
        `header_therapy_pt_chk`,
        `header_therapy_ot_chk`,
        `header_therapy_st_chk`,
        -- 併存疾患・リスク・特記事項
        `main_comorbidities_txt`,
        `main_risks_txt`,
        `main_contraindications_txt`,
        -- 心身機能・構造
        `func_risk_factors_chk`,
        `func_risk_hypertension_chk`,
        `func_risk_ckd_chk`,
        `func_pain_chk`,
        `func_pain_txt`,
        `func_rom_limitation_chk`,
        `func_rom_limitation_txt`,
        `func_muscle_weakness_chk`,
        `func_muscle_weakness_txt`,
        `func_basic_standing_balance_chk`,
        `func_basic_standing_balance_partial_assistance_chk`,
        `func_basic_standing_balance_assistance_chk`,
        -- ADL (FIM/BI) - 術後の可動域制限と荷重制限により低下
        `adl_eating_fim_start_val`,
        `adl_eating_fim_current_val`,
        `adl_grooming_fim_start_val`,
        `adl_grooming_fim_current_val`,
        `adl_bathing_fim_start_val`,
        `adl_bathing_fim_current_val`,
        `adl_dressing_upper_fim_start_val`,
        `adl_dressing_upper_fim_current_val`,
        `adl_dressing_lower_fim_start_val`,
        `adl_dressing_lower_fim_current_val`,
        `adl_toileting_fim_start_val`,
        `adl_toileting_fim_current_val`,
        `adl_bladder_management_fim_start_val`,
        `adl_bladder_management_fim_current_val`,
        `adl_bowel_management_fim_start_val`,
        `adl_bowel_management_fim_current_val`,
        `adl_transfer_bed_chair_wc_fim_start_val`,
        `adl_transfer_bed_chair_wc_fim_current_val`,
        `adl_transfer_toilet_fim_start_val`,
        `adl_transfer_toilet_fim_current_val`,
        `adl_transfer_tub_shower_fim_start_val`,
        `adl_transfer_tub_shower_fim_current_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_start_val`,
        `adl_locomotion_walk_walkingAids_wc_fim_current_val`,
        `adl_locomotion_stairs_fim_start_val`,
        `adl_locomotion_stairs_fim_current_val`,
        `adl_comprehension_fim_start_val`,
        `adl_comprehension_fim_current_val`,
        `adl_expression_fim_start_val`,
        `adl_expression_fim_current_val`,
        `adl_equipment_and_assistance_details_txt`,
        -- 栄養
        `nutrition_height_chk`,
        `nutrition_height_val`,
        `nutrition_weight_chk`,
        `nutrition_weight_val`,
        `nutrition_bmi_chk`,
        `nutrition_bmi_val`,
        `nutrition_method_oral_chk`,
        `nutrition_method_oral_meal_chk`,
        -- 社会保障サービス
        `social_care_level_status_chk`,
        `social_care_level_care_slct`,
        `social_care_level_care_num1_slct`,
        -- 目標・方針・署名
        `goals_1_month_txt`,
        `goals_at_discharge_txt`,
        `goals_discharge_destination_chk`,
        `goals_discharge_destination_txt`,
        `policy_treatment_txt`,
        `policy_content_txt`,
        `signature_rehab_doctor_txt`,
        `signature_pt_txt`,
        `signature_ot_txt`,
        `signature_explanation_date`,
        `signature_explainer_txt`,
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        `goal_p_residence_chk`,
        `goal_p_residence_slct`,
        `goal_p_social_activity_chk`,
        `goal_p_social_activity_txt`,
        `goal_p_hobby_chk`,
        `goal_p_hobby_txt`,
        -- 目標(活動)
        `goal_a_indoor_mobility_chk`,
        `goal_a_indoor_mobility_assistance_chk`,
        `goal_a_indoor_mobility_equipment_chk`,
        `goal_a_indoor_mobility_equipment_txt`,
        `goal_a_outdoor_mobility_chk`,
        `goal_a_outdoor_mobility_assistance_chk`,
        `goal_a_outdoor_mobility_equipment_chk`,
        `goal_a_outdoor_mobility_equipment_txt`,
        `goal_a_bathing_chk`,
        `goal_a_bathing_independent_chk`,
        `goal_a_bathing_type_tub_chk`,
        `goal_a_housework_meal_chk`,
        `goal_a_housework_meal_partial_chk`,
        `goal_a_housework_meal_partial_txt`,
        -- 対応を要する項目
        `goal_s_env_home_modification_chk`,
        `goal_s_env_home_modification_txt`,
        `goal_s_env_assistive_device_chk`,
        `goal_s_env_assistive_device_txt`,
        `goal_s_env_care_insurance_chk`,
        `goal_s_env_care_insurance_details_txt`,
        `goal_s_3rd_party_main_caregiver_chk`,
        `goal_s_3rd_party_main_caregiver_txt`,
        -- 具体的な対応方針
        `goal_p_action_plan_txt`,
        `goal_a_action_plan_txt`,
        `goal_s_env_action_plan_txt`,
        `goal_s_3rd_party_action_plan_txt`
    )
VALUES (
        140,
        1,
        -- 【1枚目】----------------------------------------------------
        -- ヘッダー・基本情報
        '2025-10-04',
        '左変形性股関節症による人工股関節全置換術後',
        '2025-09-10',
        '2025-09-17',
        TRUE,
        TRUE,
        FALSE,
        -- 併存疾患・リスク・特記事項
        '骨粗鬆症、高血圧症（内服治療中、血圧コントロール良好）',
        NULL,
        NULL,
        -- 心身機能・構造
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        NULL,
        TRUE,
        TRUE,
        TRUE,
        -- ADL (FIM/BI)
        7,
        7,
        -- 整容
        6,
        6,
        -- 清拭
        4,
        5,
        -- 更衣(上半身)
        7,
        7,
        -- 更衣(下半身)
        3,
        4,
        -- トイレ動作
        5,
        6,
        -- 排尿管理
        7,
        7,
        -- 排便管理
        7,
        7,
        -- 移乗(ベッド・椅子・車椅子)
        4,
        5,
        -- 移乗(トイレ)
        4,
        5,
        -- 移乗(風呂)
        3,
        4,
        -- 移動(歩行・車椅子)
        3,
        4,
        -- 階段
        1,
        1,
        -- 理解
        7,
        7,
        -- 表出
        7,
        7,
        NULL,
        -- 栄養
        TRUE,
        168.0,
        TRUE,
        63.0,
        TRUE,
        22.3,
        TRUE,
        TRUE,
        -- 社会保障サービス
        TRUE,
        TRUE,
        TRUE,
        -- 目標・方針・署名
        NULL,
        NULL,
        TRUE,
        '自宅（妻と二人暮らし）',
        NULL,
        '【理学療法】: 股関節周囲筋力強化、バランス訓練、歩行訓練（歩行器→T字杖）、階段昇降訓練。\n【作業療法】: ADL指導（更衣、入浴、トイレ動作の工夫、自助具の活用）、家事動作訓練（調理、洗濯）、高所作業やかがむ動作の練習。',
        '',
        '',
        '',
        '2025-10-04',
        '',
        -- 【2枚目】----------------------------------------------------
        -- 目標(参加)
        TRUE,
        '自宅',
        TRUE,
        '地域でのゴルフサークル活動への復帰。夫婦での旅行（国内）の再開。',
        TRUE,
        'ゴルフ、旅行、園芸（ベランダでの鉢植え程度）',
        -- 目標(活動)
        TRUE,
        TRUE,
        TRUE,
        '歩行器',
        TRUE,
        TRUE,
        TRUE,
        'T字杖',
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        TRUE,
        'かがむ動作や重いものを持つ際に介助が必要。',
        -- 対応を要する項目
        TRUE,
        '自宅内の段差解消、手すりの設置、浴槽への踏み台設置などを検討。',
        TRUE,
        '股関節屈曲制限対応の自助具（ソックスエイド、リーチャー、股関節用の長い靴べら）。',
        TRUE,
        '介護保険申請を検討。訪問リハビリテーション、デイサービス等の利用可能性を調査。',
        TRUE,
        '妻（介助負担の軽減、介護指導）',
        -- 具体的な対応方針
        NULL,
        NULL,
        NULL,
        NULL
    );