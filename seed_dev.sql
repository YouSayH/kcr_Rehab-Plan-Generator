-- =================================================================
-- 開発用サンプルデータ
-- =================================================================
-- このファイルは開発・動作確認用です。本番環境では読み込まないでください。
-- docker-compose.yml が /docker-entrypoint-initdb.d/2_seed_dev.sql として
-- マウントしており、DBの初回起動時にのみ実行されます。
--
-- 職員アカウントはここには含めません。既知のログイン情報を配布することに
-- なるためです。管理者アカウントはアプリ起動時に環境変数
-- INITIAL_ADMIN_USER / INITIAL_ADMIN_PASSWORD から作成されます
-- (app/core/bootstrap.py)。患者の担当割り当ては管理画面から行ってください。

USE rehab_db;
SET NAMES utf8mb4;


-- -- =================================================================
-- -- 7. サンプルデータの挿入 本番環境でのデータベース作成では使わないでください。
-- -- =================================================================

-- =================================================================
-- 1人目の患者: 佐藤 健一 (68歳 男性)
-- 疾患: 左変形性股関節症による人工股関節全置換術後
-- 背景: 趣味のゴルフと旅行に意欲的。骨粗鬆症と高血圧の既往あり。
-- =================================================================
-- 1. 患者情報の登録
INSERT INTO patients (
        `patient_id`,
        `name`,
        `date_of_birth`,
        `gender`
    )
VALUES (
        1,
        '佐藤 健一',
        '1957-11-05',
        '男'
    );
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
        1,
        NULL,   -- created_by_staff_id: サンプルデータに職員は含めないためNULL
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

-- =================================================================
-- 新規患者: 渡辺 明子 (70歳 女性)
-- 疾患: 右変形性膝関節症による人工膝関節全置換術後
-- 背景: 畑仕事が好きだが、膝の痛みで困難になっていた。術後は再び畑仕事を楽しみたいと希望。
--       高血圧、脂質異常症の既往あり。
-- =================================================================
-- 1. 患者情報の登録
INSERT INTO patients (
    `patient_id`,
    `name`,
    `date_of_birth`,
    `gender`
)
VALUES (
    2,                 -- 次の利用可能なIDを指定（例として8）
    '渡辺 明子',
    '1955-03-15',      -- 70歳になる生年月日
    '女'
);
-- 3. リハビリテーション計画書（事実情報のみ）の登録
INSERT INTO rehabilitation_plans (
    `plan_id`,                     -- 自動採番されるため指定しない
    `patient_id`,
    `created_by_staff_id`,
    -- 【1枚目】----------------------------------------------------
    -- ヘッダー・基本情報
    `header_evaluation_date`,
    `header_disease_name_txt`,
    `header_onset_date`,           -- 手術日
    `header_rehab_start_date`,
    `header_therapy_pt_chk`,
    `header_therapy_ot_chk`,
    `header_therapy_st_chk`,
    -- 併存疾患・リスク・特記事項
    `main_comorbidities_txt`,
    `main_risks_txt`,              -- AI生成のためNULL
    `main_contraindications_txt`,  -- AI生成のためNULL
    -- 心身機能・構造
    `func_risk_factors_chk`,
    `func_risk_hypertension_chk`,
    `func_risk_dyslipidemia_chk`,
    `func_pain_chk`,
    `func_pain_txt`,
    `func_rom_limitation_chk`,
    `func_rom_limitation_txt`,
    `func_muscle_weakness_chk`,
    `func_muscle_weakness_txt`,
    `func_basic_standing_balance_chk`,
    `func_basic_standing_balance_partial_assistance_chk`,
    -- ADL (FIM/BI) - 術後早期
    `adl_eating_fim_start_val`, `adl_eating_fim_current_val`, `adl_eating_bi_start_val`, `adl_eating_bi_current_val`,
    `adl_grooming_fim_start_val`, `adl_grooming_fim_current_val`, `adl_grooming_bi_start_val`, `adl_grooming_bi_current_val`,
    `adl_bathing_fim_start_val`, `adl_bathing_fim_current_val`, `adl_bathing_bi_start_val`, `adl_bathing_bi_current_val`,
    `adl_dressing_upper_fim_start_val`, `adl_dressing_upper_fim_current_val`,
    `adl_dressing_lower_fim_start_val`, `adl_dressing_lower_fim_current_val`, `adl_dressing_bi_start_val`, `adl_dressing_bi_current_val`,
    `adl_toileting_fim_start_val`, `adl_toileting_fim_current_val`, `adl_toileting_bi_start_val`, `adl_toileting_bi_current_val`,
    `adl_bladder_management_fim_start_val`, `adl_bladder_management_fim_current_val`, `adl_bladder_management_bi_start_val`, `adl_bladder_management_bi_current_val`,
    `adl_bowel_management_fim_start_val`, `adl_bowel_management_fim_current_val`, `adl_bowel_management_bi_start_val`, `adl_bowel_management_bi_current_val`,
    `adl_transfer_bed_chair_wc_fim_start_val`, `adl_transfer_bed_chair_wc_fim_current_val`,
    `adl_transfer_toilet_fim_start_val`, `adl_transfer_toilet_fim_current_val`,
    `adl_transfer_tub_shower_fim_start_val`, `adl_transfer_tub_shower_fim_current_val`, `adl_transfer_bi_start_val`, `adl_transfer_bi_current_val`,
    `adl_locomotion_walk_walkingAids_wc_fim_start_val`, `adl_locomotion_walk_walkingAids_wc_fim_current_val`, `adl_locomotion_walk_walkingAids_wc_bi_start_val`, `adl_locomotion_walk_walkingAids_wc_bi_current_val`,
    `adl_locomotion_stairs_fim_start_val`, `adl_locomotion_stairs_fim_current_val`, `adl_locomotion_stairs_bi_start_val`, `adl_locomotion_stairs_bi_current_val`,
    `adl_comprehension_fim_start_val`, `adl_comprehension_fim_current_val`,
    `adl_expression_fim_start_val`, `adl_expression_fim_current_val`,
    `adl_social_interaction_fim_start_val`, `adl_social_interaction_fim_current_val`,
    `adl_problem_solving_fim_start_val`, `adl_problem_solving_fim_current_val`,
    `adl_memory_fim_start_val`, `adl_memory_fim_current_val`,
    `adl_equipment_and_assistance_details_txt`, -- AI生成のためNULL
    -- 栄養
    `nutrition_height_chk`, `nutrition_height_val`,
    `nutrition_weight_chk`, `nutrition_weight_val`,
    `nutrition_bmi_chk`, `nutrition_bmi_val`,
    `nutrition_method_oral_chk`, `nutrition_method_oral_meal_chk`,
    -- 社会保障サービス
    `social_care_level_status_chk`, `social_care_level_care_slct`, `social_care_level_care_num2_slct`,
    -- 目標・方針・署名
    `goals_1_month_txt`,           -- AI生成のためNULL
    `goals_at_discharge_txt`,      -- AI生成のためNULL
    `goals_discharge_destination_chk`, `goals_discharge_destination_txt`,
    `policy_treatment_txt`,        -- AI生成のためNULL
    `policy_content_txt`,          -- AI生成のためNULL
    `signature_rehab_doctor_txt`, `signature_pt_txt`, `signature_ot_txt`, `signature_explanation_date`, `signature_explainer_txt`,
    -- 【2枚目】----------------------------------------------------
    -- 目標(参加)
    `goal_p_residence_chk`, `goal_p_residence_slct`,
    `goal_p_social_activity_chk`, `goal_p_social_activity_txt`,
    `goal_p_hobby_chk`, `goal_p_hobby_txt`,
    -- 目標(活動)
    `goal_a_indoor_mobility_chk`, `goal_a_indoor_mobility_assistance_chk`, `goal_a_indoor_mobility_equipment_chk`, `goal_a_indoor_mobility_equipment_txt`,
    `goal_a_outdoor_mobility_chk`, `goal_a_outdoor_mobility_assistance_chk`, `goal_a_outdoor_mobility_equipment_chk`, `goal_a_outdoor_mobility_equipment_txt`,
    `goal_a_bathing_chk`, `goal_a_bathing_assistance_chk`, `goal_a_bathing_type_shower_chk`,
    `goal_a_housework_meal_chk`, `goal_a_housework_meal_partial_chk`, `goal_a_housework_meal_partial_txt`,
    -- 対応を要する項目
    `goal_s_env_home_modification_chk`, `goal_s_env_home_modification_txt`,
    `goal_s_env_assistive_device_chk`, `goal_s_env_assistive_device_txt`,
    `goal_s_env_care_insurance_chk`, `goal_s_env_care_insurance_details_txt`, `goal_s_env_care_insurance_home_rehab_chk`, `goal_s_env_care_insurance_day_care_chk`,
    `goal_s_3rd_party_main_caregiver_chk`, `goal_s_3rd_party_main_caregiver_txt`,
    -- 具体的な対応方針
    `goal_p_action_plan_txt`,      -- AI生成のためNULL
    `goal_a_action_plan_txt`,      -- AI生成のためNULL
    `goal_s_env_action_plan_txt`,  -- AI生成のためNULL
    `goal_s_3rd_party_action_plan_txt` -- AI生成のためNULL
)
VALUES (
    NULL, -- plan_id は自動採番
    2,    -- patient_id
    NULL,   -- created_by_staff_id: サンプルデータに職員は含めないためNULL
    -- 【1枚目】----------------------------------------------------
    -- ヘッダー・基本情報
    '2025-10-29',                                    -- 計画評価実施日
    '右変形性膝関節症による人工膝関節全置換術後',          -- 算定病名
    '2025-10-15',                                    -- 手術日
    '2025-10-16',                                    -- リハ開始日
    TRUE, TRUE, FALSE,                               -- PT, OT, ST
    -- 併存疾患・リスク・特記事項
    '高血圧症、脂質異常症（いずれも内服コントロール中）', -- 併存疾患
    NULL,                                            -- リスク (AI生成)
    NULL,                                            -- 禁忌 (AI生成)
    -- 心身機能・構造
    TRUE, TRUE, TRUE,                                -- 危険因子, 高血圧, 脂質異常症
    TRUE, '右膝術創部周囲の疼痛および運動時痛あり。NRS 6/10。鎮痛薬使用中。', -- 疼痛
    TRUE, '右膝関節ROM 屈曲90度、伸展-5度。',          -- ROM制限
    TRUE, '右大腿四頭筋を中心に右下肢筋力低下（MMT 3レベル）。', -- 筋力低下
    TRUE, TRUE,                                      -- 立位保持チェック, 一部介助
    -- ADL (FIM/BI) - 術後早期
    7, 7, 10, 10,  -- 食事
    5, 5, 5, 5,    -- 整容
    2, 3, 0, 0,    -- 入浴
    6, 6,          -- 更衣(上)
    3, 4, 5, 5,    -- 更衣(下), 更衣(BI)
    4, 5, 5, 5,    -- トイレ動作
    7, 7, 10, 10,  -- 排尿管理
    7, 7, 10, 10,  -- 排便管理
    3, 4,          -- 移乗(ベッド)
    3, 4,          -- 移乗(トイレ)
    1, 2, 5, 5,    -- 移乗(浴槽), 移乗(BI)
    2, 3, 5, 5,    -- 移動(歩行/車椅子)
    1, 1, 0, 0,    -- 階段
    7, 7,          -- 理解
    7, 7,          -- 表出
    7, 7,          -- 社会的交流
    6, 6,          -- 問題解決
    7, 7,          -- 記憶
    NULL,          -- 使用用具・介助内容 (AI生成)
    -- 栄養
    TRUE, 155.0, TRUE, 58.0, TRUE, 24.2, TRUE, TRUE, -- 身長, 体重, BMI, 経口, 食事
    -- 社会保障サービス
    TRUE, TRUE, TRUE,                                -- 介護保険状況, 要介護, 要介護2
    -- 目標・方針・署名
    NULL, NULL,                                      -- 短期目標, 長期目標 (AI生成)
    TRUE, '自宅（長男夫婦と同居）',                    -- 退院先
    NULL, NULL,                                      -- 治療方針, 治療内容 (AI生成)
    '医師A', '理学療法士B', '作業療法士C', '2025-10-29', '理学療法士B', -- 署名
    -- 【2枚目】----------------------------------------------------
    -- 目標(参加)
    TRUE, 'home_detached',                           -- 住居場所(自宅戸建)
    TRUE, '近所の友人との交流、地域の老人会活動への参加。', -- 社会活動
    TRUE, '畑仕事（野菜作り）、編み物',                -- 趣味
    -- 目標(活動)
    TRUE, TRUE, TRUE, '歩行器',                      -- 屋内移動
    TRUE, TRUE, TRUE, 'シルバーカー',                   -- 屋外移動
    TRUE, TRUE, TRUE,                                -- 入浴
    TRUE, TRUE, '簡単な調理（野菜洗い、米とぎ）、洗濯物たたみ', -- 家事
    -- 対応を要する項目
    TRUE, '自宅玄関の段差解消、浴室・トイレへの手すり設置。', -- 住宅改修
    TRUE, '歩行器、シルバーカー、シャワーチェア、補高便座。', -- 福祉機器
    TRUE, '要介護2認定済み。', TRUE, TRUE,             -- 介護保険, 訪問リハ, デイケア
    TRUE, '長男の妻（日中の見守り、家事援助）',          -- 主介護者
    -- 具体的な対応方針
    NULL, NULL, NULL, NULL                           -- (AI生成)
);


-- =================================================================
-- 新規患者: 伊藤 良子 (75歳 女性)
-- 疾患: 左変形性股関節症による人工股関節全置換術後
-- 背景: 以前は活発にゲートボールを楽しんでいたが、股関節痛のため断念。術後は再びゲートボール仲間と交流したいと希望。
--       心房細動、骨粗鬆症の既往あり。
-- =================================================================
-- 1. 患者情報の登録
INSERT INTO patients (
    `patient_id`,
    `name`,
    `date_of_birth`,
    `gender`
)
VALUES (
    3,                 -- 次の利用可能なIDを指定
    '伊藤 良子',
    '1950-10-29',      -- 75歳になる生年月日
    '女'
);
-- 3. リハビリテーション計画書（事実情報のみ）の登録
INSERT INTO rehabilitation_plans (
    `plan_id`,                     -- 自動採番されるため指定しない
    `patient_id`,
    `created_by_staff_id`,
    -- 【1枚目】----------------------------------------------------
    -- ヘッダー・基本情報
    `header_evaluation_date`,
    `header_disease_name_txt`,
    `header_onset_date`,           -- 手術日
    `header_rehab_start_date`,
    `header_therapy_pt_chk`,
    `header_therapy_ot_chk`,
    `header_therapy_st_chk`,
    -- 併存疾患・リスク・特記事項
    `main_comorbidities_txt`,
    `main_risks_txt`,              -- AI生成のためNULL
    `main_contraindications_txt`,  -- AI生成のためNULL
    -- 心身機能・構造
    `func_circulatory_disorder_chk`, `func_circulatory_arrhythmia_chk`, `func_circulatory_arrhythmia_status_slct`, -- 心房細動
    `func_pain_chk`,
    `func_pain_txt`,
    `func_rom_limitation_chk`,
    `func_rom_limitation_txt`,
    `func_muscle_weakness_chk`,
    `func_muscle_weakness_txt`,
    `func_basic_standing_balance_chk`,
    `func_basic_standing_balance_assistance_chk`, -- バランスは介助レベル
    -- ADL (FIM/BI) - 術後早期
    `adl_eating_fim_start_val`, `adl_eating_fim_current_val`, `adl_eating_bi_start_val`, `adl_eating_bi_current_val`,
    `adl_grooming_fim_start_val`, `adl_grooming_fim_current_val`, `adl_grooming_bi_start_val`, `adl_grooming_bi_current_val`,
    `adl_bathing_fim_start_val`, `adl_bathing_fim_current_val`, `adl_bathing_bi_start_val`, `adl_bathing_bi_current_val`,
    `adl_dressing_upper_fim_start_val`, `adl_dressing_upper_fim_current_val`,
    `adl_dressing_lower_fim_start_val`, `adl_dressing_lower_fim_current_val`, `adl_dressing_bi_start_val`, `adl_dressing_bi_current_val`,
    `adl_toileting_fim_start_val`, `adl_toileting_fim_current_val`, `adl_toileting_bi_start_val`, `adl_toileting_bi_current_val`,
    `adl_bladder_management_fim_start_val`, `adl_bladder_management_fim_current_val`, `adl_bladder_management_bi_start_val`, `adl_bladder_management_bi_current_val`,
    `adl_bowel_management_fim_start_val`, `adl_bowel_management_fim_current_val`, `adl_bowel_management_bi_start_val`, `adl_bowel_management_bi_current_val`,
    `adl_transfer_bed_chair_wc_fim_start_val`, `adl_transfer_bed_chair_wc_fim_current_val`,
    `adl_transfer_toilet_fim_start_val`, `adl_transfer_toilet_fim_current_val`,
    `adl_transfer_tub_shower_fim_start_val`, `adl_transfer_tub_shower_fim_current_val`, `adl_transfer_bi_start_val`, `adl_transfer_bi_current_val`,
    `adl_locomotion_walk_walkingAids_wc_fim_start_val`, `adl_locomotion_walk_walkingAids_wc_fim_current_val`, `adl_locomotion_walk_walkingAids_wc_bi_start_val`, `adl_locomotion_walk_walkingAids_wc_bi_current_val`,
    `adl_locomotion_stairs_fim_start_val`, `adl_locomotion_stairs_fim_current_val`, `adl_locomotion_stairs_bi_start_val`, `adl_locomotion_stairs_bi_current_val`,
    `adl_comprehension_fim_start_val`, `adl_comprehension_fim_current_val`,
    `adl_expression_fim_start_val`, `adl_expression_fim_current_val`,
    `adl_social_interaction_fim_start_val`, `adl_social_interaction_fim_current_val`,
    `adl_problem_solving_fim_start_val`, `adl_problem_solving_fim_current_val`,
    `adl_memory_fim_start_val`, `adl_memory_fim_current_val`,
    `adl_equipment_and_assistance_details_txt`, -- AI生成のためNULL
    -- 栄養
    `nutrition_height_chk`, `nutrition_height_val`,
    `nutrition_weight_chk`, `nutrition_weight_val`,
    `nutrition_bmi_chk`, `nutrition_bmi_val`,
    `nutrition_method_oral_chk`, `nutrition_method_oral_meal_chk`,
    -- 社会保障サービス
    `social_care_level_status_chk`, `social_care_level_care_slct`, `social_care_level_care_num1_slct`,
    -- 目標・方針・署名
    `goals_1_month_txt`,           -- AI生成のためNULL
    `goals_at_discharge_txt`,      -- AI生成のためNULL
    `goals_discharge_destination_chk`, `goals_discharge_destination_txt`,
    `policy_treatment_txt`,        -- AI生成のためNULL
    `policy_content_txt`,          -- AI生成のためNULL
    `signature_rehab_doctor_txt`, `signature_pt_txt`, `signature_ot_txt`, `signature_explanation_date`, `signature_explainer_txt`,
    -- 【2枚目】----------------------------------------------------
    -- 目標(参加)
    `goal_p_residence_chk`, `goal_p_residence_slct`,
    `goal_p_social_activity_chk`, `goal_p_social_activity_txt`,
    `goal_p_hobby_chk`, `goal_p_hobby_txt`,
    -- 目標(活動)
    `goal_a_indoor_mobility_chk`, `goal_a_indoor_mobility_assistance_chk`, `goal_a_indoor_mobility_equipment_chk`, `goal_a_indoor_mobility_equipment_txt`,
    `goal_a_outdoor_mobility_chk`, `goal_a_outdoor_mobility_assistance_chk`, `goal_a_outdoor_mobility_equipment_chk`, `goal_a_outdoor_mobility_equipment_txt`,
    `goal_a_bathing_chk`, `goal_a_bathing_assistance_chk`, `goal_a_bathing_type_shower_chk`,
    `goal_a_housework_meal_chk`, `goal_a_housework_meal_partial_chk`, `goal_a_housework_meal_partial_txt`,
    -- 対応を要する項目
    `goal_s_env_assistive_device_chk`, `goal_s_env_assistive_device_txt`,
    `goal_s_env_care_insurance_chk`, `goal_s_env_care_insurance_details_txt`, `goal_s_env_care_insurance_home_care_chk`,
    `goal_s_3rd_party_main_caregiver_chk`, `goal_s_3rd_party_main_caregiver_txt`,
    -- 具体的な対応方針
    `goal_p_action_plan_txt`,      -- AI生成のためNULL
    `goal_a_action_plan_txt`,      -- AI生成のためNULL
    `goal_s_env_action_plan_txt`,  -- AI生成のためNULL
    `goal_s_3rd_party_action_plan_txt` -- AI生成のためNULL
)
VALUES (
    NULL, -- plan_id は自動採番
    3,    -- patient_id
    NULL,   -- created_by_staff_id: サンプルデータに職員は含めないためNULL
    -- 【1枚目】----------------------------------------------------
    -- ヘッダー・基本情報
    '2025-10-29',                                    -- 計画評価実施日
    '左変形性股関節症による人工股関節全置換術後',          -- 算定病名
    '2025-10-20',                                    -- 手術日
    '2025-10-21',                                    -- リハ開始日
    TRUE, TRUE, FALSE,                               -- PT, OT, ST
    -- 併存疾患・リスク・特記事項
    '心房細動（ワーファリン内服中）、骨粗鬆症',       -- 併存疾患
    NULL,                                            -- リスク (AI生成)
    NULL,                                            -- 禁忌 (AI生成)
    -- 心身機能・構造
    TRUE, TRUE, 'yes',                               -- 循環障害, 不整脈チェック, 不整脈あり
    TRUE, '左股関節術創部痛、動作時痛あり。NRS 5/10。安静時は軽快。', -- 疼痛
    TRUE, '左股関節ROM 屈曲80度、伸展0度、外転20度。脱臼肢位回避指導実施中。', -- ROM制限
    TRUE, '左股関節周囲筋（特に外転筋）の筋力低下（MMT 3レベル）。', -- 筋力低下
    TRUE, TRUE,                                      -- 立位保持チェック, 介助レベル
    -- ADL (FIM/BI) - 術後早期
    7, 7, 10, 10,  -- 食事
    6, 6, 5, 5,    -- 整容
    3, 4, 0, 0,    -- 入浴
    7, 7,          -- 更衣(上)
    3, 4, 5, 5,    -- 更衣(下), 更衣(BI)
    4, 5, 5, 5,    -- トイレ動作
    7, 7, 10, 10,  -- 排尿管理
    7, 7, 10, 10,  -- 排便管理
    3, 4,          -- 移乗(ベッド)
    3, 4,          -- 移乗(トイレ)
    2, 3, 5, 5,    -- 移乗(浴槽), 移乗(BI)
    2, 3, 0, 0,    -- 移動(歩行/車椅子)
    1, 1, 0, 0,    -- 階段
    7, 7,          -- 理解
    7, 7,          -- 表出
    7, 7,          -- 社会的交流
    7, 7,          -- 問題解決
    7, 7,          -- 記憶
    NULL,          -- 使用用具・介助内容 (AI生成)
    -- 栄養
    TRUE, 150.0, TRUE, 50.0, TRUE, 22.2, TRUE, TRUE, -- 身長, 体重, BMI, 経口, 食事
    -- 社会保障サービス
    TRUE, TRUE, TRUE,                                -- 介護保険状況, 要介護, 要介護1
    -- 目標・方針・署名
    NULL, NULL,                                      -- 短期目標, 長期目標 (AI生成)
    TRUE, '自宅（独居）',                              -- 退院先
    NULL, NULL,                                      -- 治療方針, 治療内容 (AI生成)
    '医師B', '理学療法士D', '作業療法士E', '2025-10-29', '作業療法士E', -- 署名
    -- 【2枚目】----------------------------------------------------
    -- 目標(参加)
    TRUE, 'home_apartment',                          -- 住居場所(自宅マンション)
    TRUE, 'ゲートボール仲間との交流再開。',             -- 社会活動
    TRUE, 'ゲートボール（軽度なプレー）、読書',          -- 趣味
    -- 目標(活動)
    TRUE, TRUE, TRUE, '歩行器',                      -- 屋内移動
    TRUE, TRUE, TRUE, 'T字杖',                       -- 屋外移動 (目標はT字杖)
    TRUE, TRUE, TRUE,                                -- 入浴
    TRUE, TRUE, '簡単な調理（電子レンジ使用など）、洗濯（洗濯機操作）', -- 家事
    -- 対応を要する項目
    TRUE, 'ソックスエイド、リーチャー、長柄ブラシ',      -- 福祉機器
    TRUE, '要介護1認定済み。', TRUE,                   -- 介護保険, 訪問介護
    TRUE, '近隣に住む長女（週2-3回訪問）',              -- 主介護者
    -- 具体的な対応方針
    NULL, NULL, NULL, NULL                           -- (AI生成)
);


-- =================================================================
-- 新規患者: 木村 さゆり (65歳 女性)
-- 疾患: 関節リウマチによる両変形性膝関節症に対する右人工膝関節全置換術後
-- 背景: 長年関節リウマチを患い、膝の変形と痛みが進行。日常生活に支障をきたし手術に至る。
--       活動意欲は高いが、リウマチによる他関節の痛みや易疲労性も考慮が必要。
--       合併症としてシェーグレン症候群あり。
-- =================================================================
-- 1. 患者情報の登録
INSERT INTO patients (
    `patient_id`,
    `name`,
    `date_of_birth`,
    `gender`
)
VALUES (
    4,                -- 次の利用可能なIDを指定
    '木村 さゆり',
    '1960-06-10',      -- 65歳になる生年月日
    '女'
);
-- 3. リハビリテーション計画書（事実情報のみ）の登録
INSERT INTO rehabilitation_plans (
    `plan_id`,                     -- 自動採番されるため指定しない
    `patient_id`,
    `created_by_staff_id`,
    -- 【1枚目】----------------------------------------------------
    -- ヘッダー・基本情報
    `header_evaluation_date`,
    `header_disease_name_txt`,
    `header_onset_date`,           -- 手術日
    `header_rehab_start_date`,
    `header_therapy_pt_chk`,
    `header_therapy_ot_chk`,
    `header_therapy_st_chk`,
    -- 併存疾患・リスク・特記事項
    `main_comorbidities_txt`,
    `main_risks_txt`,              -- AI生成のためNULL
    `main_contraindications_txt`,  -- AI生成のためNULL
    -- 心身機能・構造
    `func_pain_chk`,               -- リウマチによる他関節痛も考慮
    `func_pain_txt`,
    `func_rom_limitation_chk`,     -- 術側膝以外にもリウマチによる可動域制限がある可能性
    `func_rom_limitation_txt`,
    `func_muscle_weakness_chk`,
    `func_muscle_weakness_txt`,
    `func_other_chk`,              -- 易疲労性など
    `func_other_txt`,
    `func_basic_standing_balance_chk`,
    `func_basic_standing_balance_partial_assistance_chk`,
    -- ADL (FIM/BI) - 術後早期、リウマチの影響も加味
    `adl_eating_fim_start_val`, `adl_eating_fim_current_val`, `adl_eating_bi_start_val`, `adl_eating_bi_current_val`,
    `adl_grooming_fim_start_val`, `adl_grooming_fim_current_val`, `adl_grooming_bi_start_val`, `adl_grooming_bi_current_val`,
    `adl_bathing_fim_start_val`, `adl_bathing_fim_current_val`, `adl_bathing_bi_start_val`, `adl_bathing_bi_current_val`,
    `adl_dressing_upper_fim_start_val`, `adl_dressing_upper_fim_current_val`,
    `adl_dressing_lower_fim_start_val`, `adl_dressing_lower_fim_current_val`, `adl_dressing_bi_start_val`, `adl_dressing_bi_current_val`,
    `adl_toileting_fim_start_val`, `adl_toileting_fim_current_val`, `adl_toileting_bi_start_val`, `adl_toileting_bi_current_val`,
    `adl_bladder_management_fim_start_val`, `adl_bladder_management_fim_current_val`, `adl_bladder_management_bi_start_val`, `adl_bladder_management_bi_current_val`,
    `adl_bowel_management_fim_start_val`, `adl_bowel_management_fim_current_val`, `adl_bowel_management_bi_start_val`, `adl_bowel_management_bi_current_val`,
    `adl_transfer_bed_chair_wc_fim_start_val`, `adl_transfer_bed_chair_wc_fim_current_val`,
    `adl_transfer_toilet_fim_start_val`, `adl_transfer_toilet_fim_current_val`,
    `adl_transfer_tub_shower_fim_start_val`, `adl_transfer_tub_shower_fim_current_val`, `adl_transfer_bi_start_val`, `adl_transfer_bi_current_val`,
    `adl_locomotion_walk_walkingAids_wc_fim_start_val`, `adl_locomotion_walk_walkingAids_wc_fim_current_val`, `adl_locomotion_walk_walkingAids_wc_bi_start_val`, `adl_locomotion_walk_walkingAids_wc_bi_current_val`,
    `adl_locomotion_stairs_fim_start_val`, `adl_locomotion_stairs_fim_current_val`, `adl_locomotion_stairs_bi_start_val`, `adl_locomotion_stairs_bi_current_val`,
    `adl_comprehension_fim_start_val`, `adl_comprehension_fim_current_val`,
    `adl_expression_fim_start_val`, `adl_expression_fim_current_val`,
    `adl_social_interaction_fim_start_val`, `adl_social_interaction_fim_current_val`,
    `adl_problem_solving_fim_start_val`, `adl_problem_solving_fim_current_val`,
    `adl_memory_fim_start_val`, `adl_memory_fim_current_val`,
    `adl_equipment_and_assistance_details_txt`, -- AI生成のためNULL
    -- 栄養
    `nutrition_height_chk`, `nutrition_height_val`,
    `nutrition_weight_chk`, `nutrition_weight_val`,
    `nutrition_bmi_chk`, `nutrition_bmi_val`,
    `nutrition_method_oral_chk`, `nutrition_method_oral_meal_chk`,
    -- 社会保障サービス
    `social_care_level_status_chk`, `social_care_level_support_chk`, `social_care_level_support_num2_slct`, -- 例: 要支援2
    `social_disability_certificate_physical_chk`, `social_disability_certificate_physical_type_txt`, `social_disability_certificate_physical_rank_val`, -- リウマチによる身体障害者手帳
    -- 目標・方針・署名
    `goals_1_month_txt`,           -- AI生成のためNULL
    `goals_at_discharge_txt`,      -- AI生成のためNULL
    `goals_discharge_destination_chk`, `goals_discharge_destination_txt`,
    `policy_treatment_txt`,        -- AI生成のためNULL
    `policy_content_txt`,          -- AI生成のためNULL
    `signature_rehab_doctor_txt`, `signature_pt_txt`, `signature_ot_txt`, `signature_explanation_date`, `signature_explainer_txt`,
    -- 【2枚目】----------------------------------------------------
    -- 目標(参加)
    `goal_p_residence_chk`, `goal_p_residence_slct`,
    `goal_p_social_activity_chk`, `goal_p_social_activity_txt`,
    `goal_p_hobby_chk`, `goal_p_hobby_txt`,
    -- 目標(活動)
    `goal_a_indoor_mobility_chk`, `goal_a_indoor_mobility_assistance_chk`, `goal_a_indoor_mobility_equipment_chk`, `goal_a_indoor_mobility_equipment_txt`,
    `goal_a_outdoor_mobility_chk`, `goal_a_outdoor_mobility_assistance_chk`, `goal_a_outdoor_mobility_equipment_chk`, `goal_a_outdoor_mobility_equipment_txt`,
    `goal_a_dressing_chk`, `goal_a_dressing_assistance_chk`, -- 更衣に介助が必要
    `goal_a_bathing_chk`, `goal_a_bathing_assistance_chk`, `goal_a_bathing_type_shower_chk`,
    `goal_a_housework_meal_chk`, `goal_a_housework_meal_partial_chk`, `goal_a_housework_meal_partial_txt`,
    -- 対応を要する項目
    `goal_s_env_assistive_device_chk`, `goal_s_env_assistive_device_txt`, -- 自助具
    `goal_s_env_care_insurance_chk`, `goal_s_env_care_insurance_details_txt`, `goal_s_env_care_insurance_home_care_chk`, -- 訪問介護
    `goal_s_3rd_party_main_caregiver_chk`, `goal_s_3rd_party_main_caregiver_txt`,
    -- 具体的な対応方針
    `goal_p_action_plan_txt`,      -- AI生成のためNULL
    `goal_a_action_plan_txt`,      -- AI生成のためNULL
    `goal_s_env_action_plan_txt`,  -- AI生成のためNULL
    `goal_s_3rd_party_action_plan_txt` -- AI生成のためNULL
)
VALUES (
    NULL, -- plan_id は自動採番
    4,   -- patient_id
    NULL,   -- created_by_staff_id: サンプルデータに職員は含めないためNULL
    -- 【1枚目】----------------------------------------------------
    -- ヘッダー・基本情報
    '2025-10-29',                                    -- 計画評価実施日
    '関節リウマチによる両変形性膝関節症、右人工膝関節全置換術後', -- 算定病名
    '2025-10-18',                                    -- 手術日
    '2025-10-19',                                    -- リハ開始日
    TRUE, TRUE, FALSE,                               -- PT, OT, ST
    -- 併存疾患・リスク・特記事項
    '関節リウマチ（生物学的製剤使用中）、シェーグレン症候群、骨粗鬆症', -- 併存疾患
    NULL,                                            -- リスク (AI生成)
    NULL,                                            -- 禁忌 (AI生成)
    -- 心身機能・構造
    TRUE, '右膝術部痛(NRS 4/10)。左膝、両手指にもリウマチによる痛みあり(NRS 3/10)。', -- 疼痛
    TRUE, '右膝ROM 屈曲95度、伸展-10度。両手指PIP, DIP関節にも軽度可動域制限あり。', -- ROM制限
    TRUE, '右下肢筋力低下(MMT 3+)。リウマチによる全身倦怠感、易疲労性あり。', -- 筋力低下
    TRUE, '易疲労性あり。長時間の活動は困難。',         -- その他
    TRUE, TRUE,                                      -- 立位保持チェック, 一部介助
    -- ADL (FIM/BI) - 術後早期、リウマチの影響も加味
    6, 6, 10, 10,  -- 食事 (手指の痛みでやや困難)
    4, 5, 5, 5,    -- 整容 (手指、肩の動きにくさ)
    2, 3, 0, 0,    -- 入浴 (膝、全身状態)
    5, 5,          -- 更衣(上) (手指、肩)
    3, 4, 5, 5,    -- 更衣(下), 更衣(BI) (膝、手指)
    4, 5, 5, 5,    -- トイレ動作
    7, 7, 10, 10,  -- 排尿管理
    7, 7, 10, 10,  -- 排便管理
    3, 4,          -- 移乗(ベッド)
    3, 4,          -- 移乗(トイレ)
    2, 3, 5, 5,    -- 移乗(浴槽), 移乗(BI)
    2, 3, 0, 0,    -- 移動(歩行/車椅子)
    1, 1, 0, 0,    -- 階段
    7, 7,          -- 理解
    7, 7,          -- 表出
    7, 7,          -- 社会的交流
    7, 7,          -- 問題解決
    7, 7,          -- 記憶
    NULL,          -- 使用用具・介助内容 (AI生成)
    -- 栄養
    TRUE, 152.0, TRUE, 45.0, TRUE, 19.5, TRUE, TRUE, -- 身長, 体重(やや低体重), BMI, 経口, 食事
    -- 社会保障サービス
    TRUE, TRUE, TRUE,                                -- 介護保険状況, 要支援, 要支援2
    TRUE, '下肢機能障害', 4,                          -- 身体障害者手帳あり, 下肢, 4級
    -- 目標・方針・署名
    NULL, NULL,                                      -- 短期目標, 長期目標 (AI生成)
    TRUE, '自宅（夫と二人暮らし）',                    -- 退院先
    NULL, NULL,                                      -- 治療方針, 治療内容 (AI生成)
    '医師C', '理学療法士F', '作業療法士G', '2025-10-29', '理学療法士F', -- 署名
    -- 【2枚目】----------------------------------------------------
    -- 目標(参加)
    TRUE, 'home_detached',                           -- 住居場所(自宅戸建)
    TRUE, '友人との散歩（30分程度）、地域の編み物教室への参加。', -- 社会活動
    TRUE, '編み物、読書',                              -- 趣味
    -- 目標(活動)
    TRUE, TRUE, TRUE, '歩行器',                      -- 屋内移動
    TRUE, TRUE, TRUE, 'シルバーカー',                   -- 屋外移動
    TRUE, TRUE,                                      -- 更衣（介助）
    TRUE, TRUE, TRUE,                                -- 入浴（介助、シャワー）
    TRUE, TRUE, '食事の準備（簡単なもの）、洗濯物干し', -- 家事
    -- 対応を要する項目
    TRUE, '太柄カトラリー、ボタンエイド、リーチャー、編み物用補助具', -- 自助具
    TRUE, '要支援2認定済み。', TRUE,                   -- 介護保険, 訪問介護
    TRUE, '夫（高齢、腰痛持ち）',                      -- 主介護者
    -- 具体的な対応方針
    NULL, NULL, NULL, NULL                           -- (AI生成)
);



-- 完了メッセージ
SELECT 'データベースとテーブルの作成、サンプルデータの挿入が完了しました。' AS 'Status';
