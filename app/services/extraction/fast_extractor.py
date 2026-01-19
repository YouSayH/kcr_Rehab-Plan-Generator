# app/services/extraction/fast_extractor.py
import logging
import re
from datetime import datetime

# 新しいモジュールのインポート
try:
    from app.services.extraction.nlp_loader import load_ginza
    from app.services.extraction.negation import NegationDetector
except ImportError:
    pass

# ロガー設定
logger = logging.getLogger(__name__)

class FastExtractor:
    """
    正規表現とNegEx（否定判定）を用いて、テキストから医療情報を高速に抽出するクラス。
    GLiNERなどのDeep Learningモデルを使用しないため、CPUのみで高速に動作します。
    """
    def __init__(self, use_gpu=False, model_name=None):
    # def __init__(self, use_gpu=True, model_name="fastino/gliner2-large-v1"):
        # 互換性のために引数は残していますが、内部では使用しません
        
        # 1. GiNZA (Spacy) & NegationDetector の初期化
        # これらは否定判定（「麻痺なし」など）に必須です
        logger.info("Initializing FastExtractor (Regex + NegEx mode)...")
        self.nlp = load_ginza()
        self.negation_detector = NegationDetector(self.nlp)

        # 3. キーワードマッピング (Regex検索対象)
        self.label_mapping = {
            # --- 治療・基本情報 ---
            "header_therapy_pt_chk": ["理学療法", "PT", "理学療法士"],
            "header_therapy_ot_chk": ["作業療法", "OT", "作業療法士"],
            "header_therapy_st_chk": ["言語聴覚療法", "ST", "言語聴覚士"],

            # --- リスク・既往歴・全身状態 ---
            "func_risk_hypertension_chk": ["高血圧", "HT", "HTN", "Hypertension"], 
            "func_risk_diabetes_chk": ["糖尿病", "DM", "Diabetes", "T2DM"],
            "func_risk_dyslipidemia_chk": ["脂質異常症", "高脂血症", "DL", "Dyslipidemia"],
            "func_risk_ckd_chk": ["CKD", "慢性腎臓病", "腎不全", "透析", "HD"],
            "func_risk_angina_chk": ["狭心症", "AP", "Angina"],
            "func_risk_omi_chk": ["陳旧性心筋梗塞", "OMI", "心筋梗塞", "MI"],
            "func_risk_smoking_chk": ["喫煙", "タバコ", "スモーカー", "Brinkman", "BI"], 
            "func_risk_obesity_chk": ["肥満", "Obesity"], 
            "func_risk_hyperuricemia_chk": ["高尿酸血症", "痛風", "HU", "UA高値"],
            "func_risk_family_history_chk": ["家族歴", "FH"],
            "func_risk_other_chk": ["その他リスク", "特記事項"],

            "func_circulatory_disorder_chk": ["循環器疾患", "心疾患", "心不全", "弁膜症", "CHF"],
            "func_circulatory_arrhythmia_chk": ["不整脈", "心房細動", "Af", "A-fib", "ペースメーカー", "PVC"],
            "func_circulatory_ef_chk": ["EF", "駆出率", "LVEF"],

            "func_consciousness_disorder_chk": ["意識障害", "JCS", "GCS", "傾眠", "昏睡"],
            "func_respiratory_disorder_chk": ["呼吸障害", "COPD", "肺炎", "呼吸不全", "肺気腫", "喘息"],
            "func_respiratory_o2_therapy_chk": ["酸素療法", "HOT", "在宅酸素", "O2投与"],
            "func_respiratory_ventilator_chk": ["人工呼吸器", "ベンチレーター", "NPPV", "CPAP"],
            "func_respiratory_tracheostomy_chk": ["気管切開", "気切", "カニューレ"],
            
            # --- 運動機能 ---
            "func_motor_paralysis_chk": ["麻痺", "片麻痺", "対麻痺", "四肢麻痺", "運動麻痺", "単麻痺"],
            "func_pain_chk": ["疼痛", "痛み", "Pain", "自発痛", "運動時痛", "激痛", "NRS", "VAS"],
            "func_rom_limitation_chk": ["可動域制限", "ROM制限", "拘縮", "関節拘縮", "上がりにくい", "動かしにくい", "硬い", "ROM"],
            "func_muscle_weakness_chk": ["筋力低下", "脱力", "MMT低下", "力が入らない", "筋力"],
            "func_motor_ataxia_chk": ["失調", "運動失調", "ふらつき", "協調運動障害"],
            "func_motor_parkinsonism_chk": ["パーキンソニズム", "固縮", "振戦", "すくみ足", "小刻み歩行"],
            "func_pressure_ulcer_chk": ["褥瘡", "床ずれ", "デクービタス", "創傷", "DESIGN-R"],
            "func_other_chk": ["その他機能障害"],
            
            # 運動機能詳細
            "func_motor_involuntary_movement_chk": ["不随意運動", "ジスキネジア", "アテトーゼ", "舞踏様運動", "クローヌス", "バリスム"],
            "func_motor_muscle_tone_abnormality_chk": ["筋緊張", "痙性", "低緊張", "MAS", "Ashworth", "固縮"],
            "func_contracture_deformity_chk": ["変形", "関節変形", "円背", "側弯", "内反尖足", "外反母趾", "亀背"],

            # --- 嚥下・栄養 ---
            "func_swallowing_disorder_chk": ["嚥下障害", "誤嚥", "ムセ", "Dysphagia", "飲み込みにくい", "嚥下", "飲み込み", "とろみ", "刻み食", "VF", "VE"],
            "func_nutritional_disorder_chk": ["低栄養", "栄養障害", "アルブミン低下", "Alb低下", "低蛋白"],
            
            # 栄養補給方法
            "nutrition_method_oral_chk": ["経口摂取", "常食", "全粥", "食事", "経口"], 
            "nutrition_method_oral_meal_chk": ["食事摂取", "食事"], 
            "nutrition_method_oral_supplement_chk": ["補助食品", "ONS", "エンシュア", "ラコール", "メイバランス"],
            "nutrition_method_tube_chk": ["経管栄養", "経鼻", "EDチューブ"], 
            "nutrition_method_peg_chk": ["胃ろう", "PEG", "胃瘻"],
            "nutrition_method_iv_chk": ["静脈栄養", "点滴", "輸液", "IV"],
            "nutrition_method_iv_central_chk": ["中心静脈栄養", "IVH", "TPN", "CVポート"],
            "nutrition_method_iv_peripheral_chk": ["末梢静脈栄養", "PPN"],

            # --- 認知・精神・高次脳・発達 ---
            "func_disorientation_chk": ["見当識障害", "見当識"],
            "func_behavioral_psychiatric_disorder_chk": ["不穏", "暴言", "暴力", "拒絶", "せん妄", "注意力散漫", "落ち着きがない", "注意力", "散漫", "易怒性", "徘徊"],
            "func_memory_disorder_chk": ["記憶障害", "物忘れ", "HDS-R", "MMSE", "近時記憶障害"],
            "func_higher_brain_dysfunction_chk": ["高次脳機能障害", "高次脳"],
            "func_higher_brain_memory_chk": ["記憶障害"], 
            "func_higher_brain_attention_chk": ["注意障害", "注意機能"],
            "func_higher_brain_apraxia_chk": ["失行", "着衣失行", "観念運動失行", "観念失行"],
            "func_higher_brain_agnosia_chk": ["失認", "半側空間無視", "USN", "相貌失認"],
            "func_higher_brain_executive_chk": ["遂行機能障害", "遂行機能"],
            "func_developmental_disorder_chk": ["発達障害"],
            "func_developmental_asd_chk": ["自閉症", "ASD", "自閉スペクトラム症"],
            "func_developmental_adhd_chk": ["ADHD", "注意欠陥多動性障害"],
            "func_developmental_ld_chk": ["学習障害", "LD"],

            # --- 言語・感覚 ---
            "func_speech_aphasia_chk": ["失語", "失語症", "言葉が出にくい", "言語障害", "運動性失語", "感覚性失語"],
            "func_speech_articulation_chk": ["構音障害", "呂律", "ろれつ", "発語"],
            "func_speech_stuttering_chk": ["吃音", "どもり"],
            "func_sensory_hearing_chk": ["難聴", "聴覚障害", "聞こえにくい", "補聴器"],
            "func_sensory_vision_chk": ["視力低下", "盲", "半盲", "見えにくい", "白内障", "緑内障"],
            "func_sensory_superficial_chk": ["表在感覚", "触覚鈍麻", "しびれ", "感覚鈍麻", "感覚障害"],
            "func_sensory_deep_chk": ["深部感覚", "位置覚", "振動覚"],

            # --- 排泄 ---
            "func_excretory_disorder_chk": ["排泄障害", "尿失禁", "便秘", "バルーン", "導尿", "頻尿", "便失禁"],

            # --- 社会背景・手帳 ---
            "social_care_level_status_chk": ["介護保険", "要介護", "要支援", "申請中"],
            "social_care_level_support_chk": ["要支援"],
            "social_disability_certificate_physical_chk": ["身体障害者手帳"],
            "social_disability_certificate_mental_chk": ["精神障害者保健福祉手帳"],
            "social_disability_certificate_intellectual_chk": ["療育手帳", "愛の手帳"],
            "social_disability_certificate_other_chk": ["難病受給者証", "特定疾患"],

            # --- 基本動作 (実施の有無・トピック) ---
            "func_basic_rolling_chk": ["寝返り", "体位変換"],
            "func_basic_getting_up_chk": ["起き上がり"],
            "func_basic_standing_up_chk": ["立ち上がり", "起立"],
            "func_basic_sitting_balance_chk": ["座位", "端座位", "座位保持"],
            "func_basic_standing_balance_chk": ["立位", "立位保持"],
            "func_basic_other_chk": ["その他の動作"],

            # --- 目標・参加 (Goal P) ---
            "goal_p_return_to_work_chk": ["復職", "就労", "仕事復帰", "職場復帰"],
            "goal_p_return_to_work_commute_change_chk": ["通勤方法", "通勤"],
            "goal_p_schooling_chk": ["復学", "就学", "通学"],
            "goal_p_schooling_commute_change_chk": ["通学方法"],
            "goal_p_schooling_destination_chk": ["就学先", "進学先"],
            "goal_p_household_role_chk": ["家事役割", "家庭内役割", "主婦業", "家事"],
            "goal_p_hobby_chk": ["趣味", "余暇活動"],
            "goal_p_social_activity_chk": ["社会参加", "地域活動", "町内会", "外出"],

            # 就学ステータス
            "goal_p_schooling_status_possible_chk": ["復学可能", "通学可能"],
            "goal_p_schooling_status_needs_consideration_chk": ["復学検討", "要検討"],
            "goal_p_schooling_status_change_course_chk": ["転校", "転籍", "支援学級"],
            "goal_p_schooling_status_not_possible_chk": ["通学困難", "復学困難"],
            "goal_p_schooling_status_other_chk": ["就学その他"],

            # --- 活動目標 (Goal A) ---
            "goal_a_bed_mobility_chk": ["床上動作", "寝返り練習", "起き上がり練習", "体位変換"],
            "goal_a_bed_mobility_independent_chk": ["床上動作自立", "寝返り自立"],
            "goal_a_bed_mobility_assistance_chk": ["床上動作介助", "寝返り介助"],
            "goal_a_bed_mobility_not_performed_chk": ["床上動作不可"],
            "goal_a_bed_mobility_equipment_chk": ["ベッド柵", "L字柵", "ギャジアップ"],
            "goal_a_bed_mobility_environment_setup_chk": ["環境設定"],

            "goal_a_indoor_mobility_chk": ["屋内移動", "歩行練習", "車椅子操作", "歩行"],
            "goal_a_indoor_mobility_independent_chk": ["屋内移動自立", "歩行自立"],
            "goal_a_indoor_mobility_assistance_chk": ["屋内移動介助", "歩行介助"],
            "goal_a_indoor_mobility_not_performed_chk": ["屋内移動不可"],
            "goal_a_indoor_mobility_equipment_chk": ["歩行器", "杖", "車椅子"],

            "goal_a_outdoor_mobility_chk": ["屋外移動", "屋外歩行", "外出練習", "散歩"],
            "goal_a_outdoor_mobility_independent_chk": ["屋外移動自立", "外出自立"],
            "goal_a_outdoor_mobility_assistance_chk": ["屋外移動介助", "外出介助"],
            "goal_a_outdoor_mobility_not_performed_chk": ["屋外移動不可"],
            "goal_a_outdoor_mobility_equipment_chk": ["屋外用車椅子", "電動車椅子"],

            "goal_a_driving_chk": ["自動車運転", "運転再開", "運転"],
            "goal_a_driving_independent_chk": ["運転自立"],
            "goal_a_driving_assistance_chk": ["運転介助", "運転補助"],
            "goal_a_driving_not_performed_chk": ["運転不可", "運転中止"],
            "goal_a_driving_modification_chk": ["運転改造", "手動装置"],
            
            "goal_a_public_transport_chk": ["公共交通機関", "バス利用", "電車利用", "バス", "電車"],
            "goal_a_public_transport_independent_chk": ["公共交通機関自立"],
            "goal_a_public_transport_assistance_chk": ["公共交通機関介助"],
            "goal_a_public_transport_not_performed_chk": ["公共交通機関不可"],
            "goal_a_public_transport_type_chk": ["バス", "電車", "タクシー"],
            
            # ADL詳細
            "goal_a_eating_chk": ["食事動作", "摂食訓練", "食事", "摂食"], 
            "goal_a_eating_independent_chk": ["食事自立"],
            "goal_a_eating_assistance_chk": ["食事介助"],
            "goal_a_eating_not_performed_chk": ["食事不可", "絶食"],
            "goal_a_eating_method_chopsticks_chk": ["箸", "箸操作"],
            "goal_a_eating_method_fork_etc_chk": ["スプーン", "フォーク"],
            "goal_a_eating_method_tube_feeding_chk": ["経管栄養"],

            "goal_a_grooming_chk": ["整容動作", "整容"],
            "goal_a_grooming_independent_chk": ["整容自立"],
            "goal_a_grooming_assistance_chk": ["整容介助"],

            "goal_a_dressing_chk": ["更衣動作", "着替え", "更衣"],
            "goal_a_dressing_independent_chk": ["更衣自立"],
            "goal_a_dressing_assistance_chk": ["更衣介助"],
            
            "goal_a_toileting_chk": ["排泄動作", "トイレ動作", "トイレ"],
            "goal_a_toileting_independent_chk": ["排泄自立", "トイレ自立"],
            "goal_a_toileting_assistance_chk": ["排泄介助", "トイレ介助"],
            "goal_a_toileting_assistance_clothing_chk": ["下衣操作", "ズボン操作", "パンツ操作", "上げ下げ"],
            "goal_a_toileting_assistance_wiping_chk": ["清拭", "後始末", "お尻拭き"],
            "goal_a_toileting_assistance_catheter_chk": ["カテーテル管理", "自己導尿"],
            "goal_a_toileting_type_chk": ["トイレ種類"],
            "goal_a_toileting_type_japanese_chk": ["和式トイレ"],
            "goal_a_toileting_type_western_chk": ["洋式トイレ"],
            "goal_a_toileting_type_other_chk": ["ポータブルトイレ"],

            "goal_a_bathing_chk": ["入浴動作", "お風呂", "入浴"],
            "goal_a_bathing_independent_chk": ["入浴自立"],
            "goal_a_bathing_assistance_chk": ["入浴介助"],
            "goal_a_bathing_assistance_body_washing_chk": ["洗身", "体洗い"],
            "goal_a_bathing_assistance_transfer_chk": ["浴槽移乗", "またぎ動作"],
            "goal_a_bathing_type_shower_chk": ["シャワー浴", "シャワー"],
            "goal_a_bathing_type_tub_chk": ["浴槽", "湯船", "入槽"],

            "goal_a_housework_meal_chk": ["調理訓練", "家事動作", "調理"],
            "goal_a_housework_meal_all_chk": ["家事全般"],
            "goal_a_housework_meal_partial_chk": ["家事一部"],
            "goal_a_housework_meal_not_performed_chk": ["家事不可"],

            "goal_a_writing_chk": ["書字"],
            "goal_a_writing_independent_chk": ["書字自立"],
            "goal_a_writing_independent_after_hand_change_chk": ["利き手交換"],
            "goal_a_writing_other_chk": ["書字その他"],

            "goal_a_ict_chk": ["ICT", "スマホ", "パソコン操作", "携帯電話"],
            "goal_a_ict_independent_chk": ["ICT自立"],
            "goal_a_ict_assistance_chk": ["ICT介助"],

            "goal_a_communication_chk": ["コミュニケーション", "意思疎通"],
            "goal_a_communication_independent_chk": ["コミュニケーション自立"],
            "goal_a_communication_assistance_chk": ["コミュニケーション介助"],
            "goal_a_communication_device_chk": ["意思伝達装置", "VOCA", "レッツチャット"],
            "goal_a_communication_letter_board_chk": ["文字盤", "50音表"],
            "goal_a_communication_cooperation_chk": ["合図", "はい・いいえで答える"],

            # --- 環境・サービス (Goal S - Env) ---
            "goal_s_env_home_modification_chk": ["住宅改修", "手すり設置", "段差解消"],
            "goal_s_env_assistive_device_chk": ["補装具", "車椅子作成", "装具作成"],
            "goal_s_env_other_chk": ["その他の環境"],
            
            # 介護保険サービス
            "goal_s_env_care_insurance_chk": ["介護保険サービス", "ケアマネジャー"],
            "goal_s_env_care_insurance_outpatient_rehab_chk": ["通所リハビリ", "通所リハ", "デイケア"],
            "goal_s_env_care_insurance_day_care_chk": ["通所介護", "デイサービス"],
            "goal_s_env_care_insurance_home_care_chk": ["訪問介護", "ヘルパー", "ホームヘルプ"],
            "goal_s_env_care_insurance_home_nursing_chk": ["訪問看護"],
            "goal_s_env_care_insurance_home_rehab_chk": ["訪問リハビリ", "訪問リハ"],
            "goal_s_env_care_insurance_health_facility_chk": ["老人保健施設", "老健"],
            "goal_s_env_care_insurance_nursing_home_chk": ["特別養護老人ホーム", "特養"],
            "goal_s_env_care_insurance_care_hospital_chk": ["介護医療院"],
            "goal_s_env_care_insurance_other_chk": ["その他の介護サービス"],
            
            # 障害福祉サービス
            "goal_s_env_disability_welfare_chk": ["障害福祉サービス"],
            "goal_s_env_disability_welfare_life_care_chk": ["生活介護"],
            "goal_s_env_disability_welfare_child_development_support_chk": ["児童発達支援"],
            "goal_s_env_disability_welfare_after_school_day_service_chk": ["放課後等デイサービス"],
            "goal_s_env_disability_welfare_other_chk": ["その他の障害福祉"],

            # 社会保障・経済
            "goal_s_env_social_security_chk": ["社会保障"],
            "goal_s_env_social_security_disability_pension_chk": ["障害年金"],
            "goal_s_env_social_security_intractable_disease_cert_chk": ["難病医療費助成", "特定疾患"],
            "goal_s_env_social_security_physical_disability_cert_chk": ["身体障害者手帳取得"],
            "goal_s_env_social_security_other_chk": ["その他の社会保障"],

            # --- 心理・人的 (Goal S - Psych/3rd) ---
            "goal_s_psychological_support_chk": ["心理的サポート", "精神的ケア", "カウンセリング", "傾聴"],
            "goal_s_disability_acceptance_chk": ["障害受容"],
            "goal_s_psychological_other_chk": ["心理面その他"],
            "goal_s_3rd_party_main_caregiver_chk": ["キーパーソン", "主介護者", "介護力", "協力者"],
            "goal_s_3rd_party_family_structure_change_chk": ["家族構成の変化", "同居"],
            "goal_s_3rd_party_household_role_change_chk": ["役割変化"],
            "goal_s_3rd_party_family_activity_change_chk": ["家族活動の変化"],

            # --- 退院・長期 ---
            "goals_discharge_destination_chk": ["退院先", "転院先", "施設入所", "在宅復帰"],
            "goals_planned_hospitalization_period_chk": ["入院期間", "在院日数"],
            "goals_long_term_care_needed_chk": ["長期療養"],
        }
        
        self.comorbidity_names = {
            "func_risk_hypertension_chk": "高血圧症",
            "func_risk_diabetes_chk": "糖尿病",
            "func_risk_dyslipidemia_chk": "脂質異常症",
            "func_risk_ckd_chk": "慢性腎臓病",
            "func_risk_angina_chk": "狭心症",
            "func_risk_omi_chk": "陳旧性心筋梗塞",
        }

    def extract_facts(self, text: str) -> dict:
        result = {}

        # 0. テキスト前処理 (GiNZA解析)
        doc = None
        if self.nlp:
            try:
                doc = self.nlp(text)
            except Exception as e:
                logger.error(f"GiNZA processing failed: {e}")

        # 1. ルールベース/正規表現 (年齢、性別、日付)
        age_match = re.search(r'(\d{1,3})歳', text)
        if age_match:
            result['age'] = int(age_match.group(1))

        if "女性" in text or "女" in text:
            result['gender'] = "女"
        elif "男性" in text or "男" in text:
            result['gender'] = "男"

        name_match = re.search(r'(?:患者プロフィール|氏名|名前)[:：]\s*([^\r\n(（]+)', text)
        if name_match:
            result['name'] = name_match.group(1).replace("様", "").strip()

        disease_match = re.search(r'(?:診断名|病名)[:：]\s*(.+)', text)
        if disease_match:
            result['header_disease_name_txt'] = disease_match.group(1).strip()

        for key, pattern in {
            'header_onset_date': r'発症日[:：]\s*([0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日|[0-9]{4}/[0-9]{1,2}/[0-9]{1,2})',
            'header_rehab_start_date': r'リハビリ開始日[:：]\s*([0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日|[0-9]{4}/[0-9]{1,2}/[0-9]{1,2})',
            'header_evaluation_date': r'(?:評価日|作成日)[:：]\s*([0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日|[0-9]{4}/[0-9]{1,2}/[0-9]{1,2})'
        }.items():
            match = re.search(pattern, text)
            if match:
                result[key] = self._parse_date(match.group(1))

        # 2. キーワード検索 + NegEx判定
        for schema_key, keywords in self.label_mapping.items():
            is_positive_found = False
            
            for kw in keywords:
                # 正規表現検索（re.escapeで記号をエスケープ）
                for match in re.finditer(re.escape(kw), text):
                    entity_info = {
                        'text': kw,
                        'start': match.start(),
                        'end': match.end()
                    }
                    
                    # 否定判定
                    if not self.negation_detector.is_negated(text, entity_info, doc):
                        is_positive_found = True
                        break 
                
                if is_positive_found:
                    break 
            
            if is_positive_found:
                result[schema_key] = True

        # 合併症テキスト生成
        comorbidities = []
        for key, name in self.comorbidity_names.items():
            if result.get(key):
                comorbidities.append(name)

        if comorbidities:
            result['main_comorbidities_txt'] = "、".join(comorbidities)

        return result

    def _parse_date(self, date_str: str) -> str:
        try:
            normalized = date_str.replace("年", "/").replace("月", "/").replace("日", "").strip()
            dt = datetime.strptime(normalized, "%Y/%m/%d")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return None