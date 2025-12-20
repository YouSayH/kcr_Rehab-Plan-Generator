# app/services/extraction/fast_extractor.py
import re
import logging
from datetime import datetime
import torch

# ロガー設定
logger = logging.getLogger(__name__)

try:
    from gliner2 import GLiNER2
    HAS_GLINER = True
except ImportError:
    HAS_GLINER = False
    logger.warning("gliner2 library not found. Install with `pip install gliner2`")

class FastExtractor:
    def __init__(self, use_gpu=True, model_name="fastino/gliner2-large-v1"):
        self.model = None
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
            "func_risk_hypertension_chk": ["高血圧", "高血圧症", "HT", "Hypertension"],
            "func_risk_diabetes_chk": ["糖尿病", "DM", "Diabetes", "2型糖尿病"],
            "func_risk_dyslipidemia_chk": ["脂質異常症", "高脂血症", "DL", "Dyslipidemia"],
            "func_risk_ckd_chk": ["CKD", "慢性腎臓病", "腎不全"],
            "func_risk_angina_chk": ["狭心症", "AP"],
            "func_risk_omi_chk": ["陳旧性心筋梗塞", "OMI"],
            
            "func_motor_paralysis_chk": ["麻痺", "片麻痺", "対麻痺", "四肢麻痺", "運動麻痺", "右片麻痺", "左片麻痺"],
            "func_pain_chk": ["疼痛", "痛み", "Pain", "自発痛", "運動時痛", "激痛"],
            "func_rom_limitation_chk": ["可動域制限", "ROM制限", "拘縮", "関節拘縮", "上がりにくい", "動かしにくい"],
            "func_muscle_weakness_chk": ["筋力低下", "脱力", "MMT低下", "力が入らない"],
            "func_swallowing_disorder_chk": ["嚥下障害", "誤嚥", "ムセ", "Dysphagia", "飲み込みにくい"],
            "func_disorientation_chk": ["見当識障害"],
            "func_behavioral_psychiatric_disorder_chk": ["不穏", "暴言", "暴力", "拒絶", "せん妄", "注意力散漫", "落ち着きがない"],
            "func_speech_aphasia_chk": ["失語", "失語症", "言葉が出にくい"],
            "func_speech_articulation_chk": ["構音障害", "呂律", "ろれつ"],
            "func_memory_disorder_chk": ["記憶障害", "物忘れ"],
            "func_excretory_disorder_chk": ["排泄障害", "尿失禁", "便秘"],
            
            "func_sensory_hearing_chk": ["難聴", "聴覚障害", "聞こえにくい"],
            "func_sensory_vision_chk": ["視力低下", "盲", "半盲", "見えにくい"],
            
            "social_care_level_status_chk": ["介護保険", "要介護", "要支援", "申請中"],
            "social_disability_certificate_physical_chk": ["身体障害者手帳"],
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
        
        # --- 1. ルールベース/正規表現 (修正版) ---
        
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

        # --- 2. GLiNER2 抽出 ---
        if self.model:
            all_labels_set = set()
            for labels in self.label_mapping.values():
                for l in labels:
                    all_labels_set.add(l)
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

        # --- 3. 重要な項目のバックアップ (ルールベース) ---
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