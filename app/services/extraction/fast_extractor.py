# app/services/extraction/fast_extractor.py
import logging
import re
from datetime import datetime

# ロガー設定
logger = logging.getLogger(__name__)

class FastExtractor:
    def __init__(self, use_gpu=True, model_name="fastino/gliner2-large-v1"):
        self.model = None

        # この __init__ は、ハイブリッドモードがONの時しか呼ばれないため安全です
        try:
            import torch  # ここで初めて torch をロード
            from gliner2 import GLiNER2  # ここで初めて gliner2 をロード
            HAS_GLINER = True
        except ImportError:
            HAS_GLINER = False
            logger.warning("gliner2 or torch not found. Install with `pip install gliner2 torch`")

        if HAS_GLINER:
            if use_gpu and torch.cuda.is_available():
                print(f"Loading GLiNER2 ({model_name}) on CUDA...")
                self.model = GLiNER2.from_pretrained(model_name)
                if hasattr(self.model, "to"):
                    self.model.to("cuda")
            else:
                print(f"Loading GLiNER2 ({model_name}) on CPU...")
                self.model = GLiNER2.from_pretrained(model_name)

        # GLiNER用ラベルマッピング
        # 「上がりにくい」「動かしにくい」など、患者表現も追加
        self.label_mapping = {
            # リスク・既往歴
            "func_risk_hypertension_chk": ["高血圧", "高血圧症", "HT", "Hypertension"],
            "func_risk_diabetes_chk": ["糖尿病", "DM", "Diabetes", "2型糖尿病"],
            "func_risk_dyslipidemia_chk": ["脂質異常症", "高脂血症", "DL", "Dyslipidemia"],
            "func_risk_ckd_chk": ["CKD", "慢性腎臓病", "腎不全", "透析"],
            "func_risk_angina_chk": ["狭心症", "AP"],
            "func_risk_omi_chk": ["陳旧性心筋梗塞", "OMI", "心筋梗塞"],
            "func_risk_smoking_chk": ["喫煙", "タバコ", "スモーカー", "Brinkman"], # 追加
            "func_risk_obesity_chk": ["肥満", "Obesity"], # 追加

            # 全身状態・意識
            "func_consciousness_disorder_chk": ["意識障害", "JCS", "GCS", "傾眠"], # 追加
            "func_respiratory_disorder_chk": ["呼吸障害", "COPD", "肺炎", "呼吸不全", "酸素療法", "HOT"], # 追加

            # 運動機能
            "func_motor_paralysis_chk": ["麻痺", "片麻痺", "対麻痺", "四肢麻痺", "運動麻痺", "右片麻痺", "左片麻痺"],
            "func_pain_chk": ["疼痛", "痛み", "Pain", "自発痛", "運動時痛", "激痛", "NRS"],
            "func_rom_limitation_chk": ["可動域制限", "ROM制限", "拘縮", "関節拘縮", "上がりにくい", "動かしにくい"],
            "func_muscle_weakness_chk": ["筋力低下", "脱力", "MMT低下", "力が入らない"],
            "func_motor_ataxia_chk": ["失調", "運動失調", "ふらつき"], # 追加
            "func_motor_parkinsonism_chk": ["パーキンソニズム", "固縮", "振戦", "すくみ足"], # 追加
            "func_pressure_ulcer_chk": ["褥瘡", "床ずれ", "デクービタス", "創傷", "DESIGN-R"],
            "func_circulatory_arrhythmia_chk": ["不整脈", "心房細動", "Af", "ペースメーカー", "PVC"],
            "func_respiratory_tracheostomy_chk": ["気管切開", "気切", "カニューレ"],

            # 追加推奨: 運動機能詳細
            "func_motor_involuntary_movement_chk": ["不随意運動", "ジスキネジア", "アテトーゼ", "舞踏様運動", "クローヌス"],
            "func_motor_muscle_tone_abnormality_chk": ["筋緊張", "痙性", "低緊張", "MAS", "Ashworth"],
            "func_contracture_deformity_chk": ["変形", "関節変形", "円背", "側弯", "内反尖足", "外反母趾"],

            # 嚥下・栄養
            "func_swallowing_disorder_chk": ["嚥下障害", "誤嚥", "ムセ", "Dysphagia", "飲み込みにくい", "嚥下", "飲み込み", "とろみ", "刻み食"],
            "nutrition_method_oral_chk": ["経口摂取", "常食", "全粥"], # 追加
            "nutrition_method_tube_chk": ["経管栄養", "経鼻", "胃ろう", "PEG"], # 追加

            # 認知・精神・高次脳 (大幅追加)
            "func_disorientation_chk": ["見当識障害", "見当識"],
            "func_behavioral_psychiatric_disorder_chk": ["不穏", "暴言", "暴力", "拒絶", "せん妄", "注意力散漫", "落ち着きがない", "注意力", "散漫"],
            "func_memory_disorder_chk": ["記憶障害", "物忘れ", "HDS-R", "MMSE"],
            "func_higher_brain_dysfunction_chk": ["高次脳機能障害"], # 親項目
            "func_higher_brain_attention_chk": ["注意障害"], # 追加
            "func_higher_brain_apraxia_chk": ["失行", "着衣失行", "観念運動失行"], # 追加
            "func_higher_brain_agnosia_chk": ["失認", "半側空間無視", "USN"], # 追加
            "func_higher_brain_executive_chk": ["遂行機能障害"], # 追加

            # 言語・感覚
            "func_speech_aphasia_chk": ["失語", "失語症", "言葉が出にくい", "言語障害"],
            "func_speech_articulation_chk": ["構音障害", "呂律", "ろれつ"],
            "func_sensory_hearing_chk": ["難聴", "聴覚障害", "聞こえにくい"],
            "func_sensory_vision_chk": ["視力低下", "盲", "半盲", "見えにくい"],
            "func_sensory_superficial_chk": ["表在感覚", "触覚鈍麻", "しびれ", "感覚鈍麻"], # 追加
            "func_sensory_deep_chk": ["深部感覚", "位置覚", "振動覚"], # 追加

            # 排泄
            "func_excretory_disorder_chk": ["排泄障害", "尿失禁", "便秘", "バルーン", "導尿"],

            # 社会背景
            "social_care_level_status_chk": ["介護保険", "要介護", "要支援", "申請中"],
            "social_disability_certificate_physical_chk": ["身体障害者手帳"],
            "social_disability_certificate_mental_chk": ["精神障害者保健福祉手帳"], # 追加
            "social_disability_certificate_intellectual_chk": ["療育手帳", "愛の手帳"], # 追加

            # 基本動作 (実施の有無のみ検出)
            "func_basic_rolling_chk": ["寝返り"],
            "func_basic_getting_up_chk": ["起き上がり"],
            "func_basic_standing_up_chk": ["立ち上がり"],
            "func_basic_sitting_balance_chk": ["座位", "端座位"],
            "func_basic_standing_balance_chk": ["立位"],
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

        # 1. ルールベース/正規表現 (修正版)

        age_match = re.search(r'(\d{1,3})歳', text)
        if age_match:
            result['age'] = int(age_match.group(1))

        if "女性" in text or "女" in text:
            result['gender'] = "女"
        elif "男性" in text or "男" in text:
            result['gender'] = "男"

        # 名前: スペースを含めて「様」や改行の前まで取得するように修正
        # 例: "田中 太郎 様" -> "田中 太郎"
        name_match = re.search(r'(?:患者プロフィール|氏名|名前)[:：]\s*([^\r\n(（]+)', text)
        if name_match:
            # "様" を削除し、前後の空白を除去
            full_name = name_match.group(1).replace("様", "").strip()
            result['name'] = full_name

        disease_match = re.search(r'(?:診断名|病名)[:：]\s*(.+)', text)
        if disease_match:
            result['header_disease_name_txt'] = disease_match.group(1).strip()

        onset_match = re.search(r'発症日[:：]\s*([0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日|[0-9]{4}/[0-9]{1,2}/[0-9]{1,2})', text)
        if onset_match:
            result['header_onset_date'] = self._parse_date(onset_match.group(1))

        rehab_start_match = re.search(r'リハビリ開始日[:：]\s*([0-9]{4}年[0-9]{1,2}月[0-9]{1,2}日|[0-9]{4}/[0-9]{1,2}/[0-9]{1,2})', text)
        if rehab_start_match:
            result['header_rehab_start_date'] = self._parse_date(rehab_start_match.group(1))

        # 2. GLiNER2 抽出
        if self.model:
            all_labels_set = set()
            for labels in self.label_mapping.values():
                for i in labels:
                    all_labels_set.add(i)
            all_labels = list(all_labels_set)

            try:
                # 閾値を低めに維持
                extraction_output = self.model.extract_entities(text, all_labels, threshold=0.25)
                found_entities_map = extraction_output.get('entities', {})

                for schema_key, search_labels in self.label_mapping.items():
                    is_found = False
                    for label in search_labels:
                        if label in found_entities_map and found_entities_map[label]:
                            is_found = True
                            break
                    if is_found:
                        result[schema_key] = True

            except Exception as e:
                logger.error(f"GLiNER2 extraction failed: {e}")

        # 3. 重要な項目のバックアップ (ルールベース)
        # GLiNERが漏らした場合でも、特定のキーワードがあれば強制的にTrueにする
        critical_keywords = {
            "func_pain_chk": ["痛み", "疼痛"],
            "func_rom_limitation_chk": ["制限", "上がりにくい", "拘縮", "硬い"],
            "func_muscle_weakness_chk": ["筋力低下", "脱力"],
            "func_motor_paralysis_chk": ["麻痺"]
        }

        for key, keywords in critical_keywords.items():
            if not result.get(key): # GLiNERで見つかっていない場合のみチェック
                for kw in keywords:
                    if kw in text:
                        result[key] = True
                        break

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
