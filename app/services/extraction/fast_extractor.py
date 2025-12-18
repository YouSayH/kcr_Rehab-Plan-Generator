# app/services/extraction/fast_extractor.py
import re
import torch
import logging

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
        """
        GLiNER2モデルを初期化します。
        RTX 4070 Super搭載機のため、デフォルトで大型モデル(large)を使用します。
        """
        self.model = None
        if HAS_GLINER:
            # GPUが使えるか確認
            if use_gpu and torch.cuda.is_available():
                # GLiNER2は内部でdevice指定が可能であればするが、
                # ライブラリの仕様に合わせてロード後に .to("cuda") するか、
                # ライブラリが自動判定する場合もあります。
                # READMEによると from_pretrained でロードします。
                print(f"Loading GLiNER2 ({model_name}) on CUDA...")
                self.model = GLiNER2.from_pretrained(model_name)
                # もしライブラリが .to() メソッドを持っていればGPUへ転送
                if hasattr(self.model, "to"):
                    self.model.to("cuda")
            else:
                print(f"Loading GLiNER2 ({model_name}) on CPU...")
                self.model = GLiNER2.from_pretrained(model_name)
            
        # マッピング定義: {スキーマのキー: [GLiNERに探させるラベル名のリスト]}
        # これらはカルテ内に「この言葉があればフラグON」と判断したいキーワード群です。
        self.label_mapping = {
            # リスク因子
            "func_risk_hypertension_chk": ["高血圧", "高血圧症", "HT", "Hypertension"],
            "func_risk_diabetes_chk": ["糖尿病", "DM", "Diabetes", "2型糖尿病"],
            "func_risk_dyslipidemia_chk": ["脂質異常症", "高脂血症", "DL", "Dyslipidemia"],
            "func_risk_ckd_chk": ["CKD", "慢性腎臓病", "腎不全"],
            "func_risk_angina_chk": ["狭心症", "AP"],
            "func_risk_omi_chk": ["陳旧性心筋梗塞", "OMI"],
            
            # 機能障害
            "func_motor_paralysis_chk": ["麻痺", "片麻痺", "対麻痺", "四肢麻痺", "運動麻痺"],
            "func_pain_chk": ["疼痛", "痛み", "Pain", "自発痛", "運動時痛"],
            "func_rom_limitation_chk": ["可動域制限", "ROM制限", "拘縮"],
            "func_muscle_weakness_chk": ["筋力低下", "脱力", "MMT低下"],
            "func_swallowing_disorder_chk": ["嚥下障害", "誤嚥", "ムセ", "Dysphagia"],
            "func_disorientation_chk": ["見当識障害"],
            "func_behavioral_psychiatric_disorder_chk": ["不穏", "暴言", "暴力", "拒絶", "せん妄"],
            "func_speech_aphasia_chk": ["失語", "失語症"],
            "func_speech_articulation_chk": ["構音障害"],
            
            # 感覚
            "func_sensory_hearing_chk": ["難聴", "聴覚障害"],
            "func_sensory_vision_chk": ["視力低下", "盲", "半盲"],
            
            # 社会的背景
            "social_care_level_status_chk": ["介護保険"],
            "social_disability_certificate_physical_chk": ["身体障害者手帳"],
        }

    def extract_facts(self, text: str) -> dict:
        """カルテテキストから事実情報（チェックボックスなど）を抽出する"""
        result = {}
        
        # 1. 基本的なRegex抽出 (年齢、性別など)
        # 年齢: "85歳" などのパターン
        age_match = re.search(r'(\d{1,3})歳', text)
        if age_match:
            result['age'] = int(age_match.group(1))
            
        # 性別: 文脈依存だが簡易判定
        if "女性" in text or "女" in text:
            result['gender'] = "女"
        elif "男性" in text or "男" in text:
            result['gender'] = "男"

        # 2. GLiNER2 によるエンティティ抽出
        if self.model:
            # 検索対象の全ラベルリストを作成（重複排除）
            all_labels_set = set()
            for labels in self.label_mapping.values():
                for l in labels:
                    all_labels_set.add(l)
            all_labels = list(all_labels_set)
            
            # 一括推論
            # batch_extract_entities はリストを受け取る仕様のためリスト化
            # extract_entities を使う場合: result_raw = self.model.extract_entities(text, all_labels)
            
            try:
                # READMEに基づく extract_entities の使用
                # 結果は {'entities': {'LabelName': ['text', ...], ...}} 形式
                extraction_output = self.model.extract_entities(text, all_labels)
                
                # 抽出されたエンティティの辞書を取得
                found_entities_map = extraction_output.get('entities', {})
                
                # スキーマへのマッピング
                for schema_key, search_labels in self.label_mapping.items():
                    is_found = False
                    for label in search_labels:
                        # そのラベルが抽出結果に含まれているか（リストが空でなければTrue）
                        if label in found_entities_map and found_entities_map[label]:
                            is_found = True
                            break
                    
                    if is_found:
                        result[schema_key] = True
                        
            except Exception as e:
                logger.error(f"GLiNER2 extraction failed: {e}")
                # 失敗時はキーワードマッチなどのフォールバックを行うか、空の結果を返す
        
        return result