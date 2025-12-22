import json
import logging
import os
import time
import concurrent.futures
import pprint  # デバッグ表示用に追加

import ollama
from dotenv import load_dotenv
from google import genai
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable
from google.genai import types
from pydantic import BaseModel, ValidationError

from app.schemas.schemas import PATIENT_INFO_EXTRACTION_GROUPS, HYBRID_GENERATION_GROUPS
from app.services.extraction.fast_extractor import FastExtractor

load_dotenv()
GENERATION_TIMEOUT_SEC = 240

# ログ設定 (gemini_client.pyと同じファイルに出力)
log_directory = "logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)
log_file_path = os.path.join(log_directory, "gemini_prompts.log")

# ロガーの設定 (ファイル出力のみ、フォーマット指定)
# すでにgemini_client.pyで設定されている場合は不要だが、念のため追加
logger = logging.getLogger(__name__)  # 新しいロガーインスタンスを取得
if not logger.hasHandlers():  # ハンドラが未設定の場合のみ設定
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

def optimize_schema_for_prompt(schema_cls: type, target_fields_pattern: str = None) -> dict:
    """
    LLMプロンプト用にJSONスキーマを最適化する。
    1. Optional (anyOf: [type, null]) を削除し、シンプルな型定義にする。
    2. 生成させたいフィールドを全て 'required' に追加する。
    3. (オプション) target_fields_pattern に一致しないフィールドを除外する（ノイズ削減）。
    """
    raw_schema = schema_cls.model_json_schema()
    properties = raw_schema.get("properties", {})
    new_properties = {}
    required_fields = []

    for key, prop in properties.items():
        # A. 不要なフィールドの除外 (例: GLiNERが抽出済みの _chk は除外する)
        # Step 1では '_val' (数値) と '_txt' (記述) と '_level' だけ生成させたい場合など
        if target_fields_pattern:
             # 例: "_chk" を除外したい場合など。
             # ここでは簡易的に「全てのプロパティを処理する」が、必要に応じてフィルタリングしてください。
             pass

        # B. 型定義の簡略化 (anyOf -> type)
        if "anyOf" in prop:
            # anyOfの中から 'null' でない方の型定義を探す
            real_type = next((x for x in prop["anyOf"] if x.get("type") != "null"), None)
            if real_type:
                # descriptionやtitleは元のpropから引き継ぐ
                new_prop = {k: v for k, v in prop.items() if k != "anyOf" and k != "default"}
                new_prop.update(real_type)
                new_properties[key] = new_prop
        else:
            new_properties[key] = prop

        # C. 全フィールドを必須(required)にする
        # LLMに「不明ならnull」と指示してあるので、スキーマ上は必須にして
        # キー自体は必ず出力させたほうが安定する。
        required_fields.append(key)

    return {
        "type": "object",
        "properties": new_properties,
        "required": required_fields, # ここで強力に指定
        "description": raw_schema.get("description", "")
    }

class PatientInfoParser:
    """
    Gemini APIまたはローカルLLMを使用して、非構造化テキストから構造化された患者情報を抽出するクラス。
    
    モード:
    1. 通常モード (Gemini/Ollama): スキーマをグループに分割して段階的に抽出する（高精度・低スペック環境向け）。
    2. ハイブリッドモード (Local GPU): GLiNER2で事実を高速抽出し、LLMで考察のみを生成する（高速・高スペック環境向け）。
    """

    def __init__(self, client_type: str = "gemini", use_hybrid_mode: bool = False):
        # gemini_client.py と同様に、環境変数から自動でキーを読み込む方式に変更
        self.client_type = client_type
        self.use_hybrid_mode = use_hybrid_mode

        # 設定がない場合は、メインのモデル(OLLAMA_MODEL_NAME)を使用する。
        default_ollama_model = os.getenv("OLLAMA_MODEL_NAME", "qwen3:8b")
        self.ollama_model_name = os.getenv("OLLAMA_EXTRACTION_MODEL_NAME", default_ollama_model)

        # Geminiクライアント設定
        if self.client_type == "gemini":
            if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
                raise ValueError(
                    "APIキーが設定されていません。環境変数 'GOOGLE_API_KEY' または 'GEMINI_API_KEY' を設定してください。"
                )
            self.client = genai.Client()
            self.model_name = "gemini-2.5-flash-lite"
            print("PatientInfoParser: Geminiクライアントを使用します。")
        else:
            self.client = None  # Ollamaは `ollama.chat` を直接呼ぶため不要
            self.model_name = self.ollama_model_name
            print(f"PatientInfoParser: Ollamaクライアントを使用します (Model: {self.model_name})。")

        # ハイブリッドモード設定 (GLiNER2)
        self.fast_extractor = None
        if self.use_hybrid_mode:
            # GPU利用を前提としてFastExtractorを初期化
            try:
                self.fast_extractor = FastExtractor(use_gpu=True)
                print(f"PatientInfoParser: Hybrid Mode Enabled (GLiNER2 + {self.client_type}).")
            except Exception as e:
                print(f"PatientInfoParser: GLiNER2の初期化に失敗しました。通常モードで動作します。Error: {e}")
                self.use_hybrid_mode = False
        
    
    def _restore_checkboxes(self, data: dict) -> dict:
        """
        LLMが生成した軽量データ(level文字列など)から、
        DB保存用のチェックボックス(True/False)を復元する後処理
        """
        # 1. 基本動作の復元
        basic_move_map = {
            "rolling": "func_basic_rolling",
            "getting_up": "func_basic_getting_up",
            "standing_up": "func_basic_standing_up",
            "sitting_balance": "func_basic_sitting_balance",
            "standing_balance": "func_basic_standing_balance"
        }
        
        for key, prefix in basic_move_map.items():
            level_key = f"{prefix}_level"
            if level_key in data and data[level_key]:
                val = data[level_key]
                data[f"{prefix}_chk"] = True # 親項目のチェック
                
                # 値に応じた詳細チェックボックスをON
                if val == 'independent':
                    data[f"{prefix}_independent_chk"] = True
                elif val == 'partial_assist':
                    data[f"{prefix}_partial_assistance_chk"] = True
                elif val == 'assist':
                    data[f"{prefix}_assistance_chk"] = True
                elif val == 'not_performed':
                    data[f"{prefix}_not_performed_chk"] = True

        # 2. 介護度の復元
        if "social_care_level_status_slct" in data and data["social_care_level_status_slct"]:
            slct = data["social_care_level_status_slct"]
            data["social_care_level_status_chk"] = True
             
            if slct == 'applying':
                data["social_care_level_applying_chk"] = True
            elif 'care_' in slct: # care_1 〜 care_5
                data["social_care_level_care_slct"] = True
                num = slct.split('_')[1] 
                data[f"social_care_level_care_num{num}_slct"] = True
            elif 'support_' in slct: # support_1, support_2
                data["social_care_level_support_chk"] = True
                num = slct.split('_')[1]
                data[f"social_care_level_support_num{num}_slct"] = True

        return data

    def _build_hybrid_prompt(self, text: str, facts: dict, schema: type, previous_steps_data: dict) -> str:

        """ハイブリッドモード用: 段階的生成プロンプト"""
        facts_json = json.dumps(facts, indent=2, ensure_ascii=False)
        if "Assessment" in schema.__name__:
            optimized_schema = optimize_schema_for_prompt(schema)
            
            # _chk フィールドをプロパティと必須リストから削除する
            props = optimized_schema.get("properties", {})
            required = optimized_schema.get("required", [])
            
            # 削除対象のキーを特定
            keys_to_remove = [k for k in props.keys() if k.endswith("_chk")]
            
            for k in keys_to_remove:
                del props[k]
                if k in required:
                    required.remove(k)
            
            schema_json = json.dumps(optimized_schema, indent=2, ensure_ascii=False)
            
        else:
            # その他のステップ: 通常の最適化（Optional削除・全必須化）のみ適用
            optimized_schema = optimize_schema_for_prompt(schema)
            schema_json = json.dumps(optimized_schema, indent=2, ensure_ascii=False)
        # ------------------------------------
        
        # 過去のステップで生成された情報をコンテキストとして渡す
        context_str = ""
        if previous_steps_data:
            context_str = f"""
    # これまでの検討結果（決定事項として扱うこと）
    以下の情報は既に確定しています。これと矛盾しないようにしてください。
    ```json
    {json.dumps(previous_steps_data, indent=2, ensure_ascii=False)}
    ```
            """

        step_instruction = ""
        detailed_rules = ""

        # クラス名による分岐 (部分一致で判定)

        if "ADL" in schema.__name__: # 【追加】Step 1-A: 数値抽出
            step_instruction = "カルテテキストから、FIM/BIの各項目スコア（数値）を読み取って補完してください。"
            detailed_rules = """
    - **FIM/BIスコア**: テキストに記載されている数値を正確に抽出してください。
    - **時系列**: 日付が複数ある場合、最新の値を `_current_val`、その前を `_start_val` に入れます。
    - **記述の解釈**: 「自立」=7点、「見守り」=5点、「全介助」=1点のように、テキストの記述を適切な点数に変換して入力してください。
            """

        elif "Assessment" in schema.__name__: # 【変更】Step 1-B: 記述・レベル判定
            step_instruction = "GLiNERが抽出した事実を基に、基本動作レベルの判定、リスクの洗い出し、機能障害の詳細記述を行ってください。"
            detailed_rules = """
    - **基本動作**: `func_basic_` 系のレベル（自立/介助など）をテキストから判定し、最も適切な `level` (independent等) を選択してください。
    - **リスク・機能**: `_txt` 項目には、具体的な症状や程度を日本語で記述してください。
            """
        elif "Goal" in schema.__name__ and "Texts" not in schema.__name__: # Step 2 (Goal A & S)
            # "Goal_Social_Env" や "Goal_Activity" にマッチさせる
            step_instruction = "現状評価に基づき、具体的な到達目標レベルや環境因子の設定を行ってください。"
            detailed_rules = """
    - **最重要: JSON構造について**:
      - 出力JSONは**絶対にネスト（階層化）させないでください**。すべてのキーをトップレベル（ルート）に配置してください。
      - ❌ 悪い例: `{"goal_a": {"bed_mobility": ...}}`
      - ✅ 良い例: `{"goal_a_bed_mobility_chk": true, ...}`
    - **目標設定**: 現状のADL能力よりも「少し高い」または「維持」となる現実的な目標を設定してください。
    - **チェックボックス**: 該当する項目を積極的に `True` にしてください。
            """

        elif "GoalTexts" in schema.__name__: # Step 3 (新設)
            step_instruction = "これまでの評価と詳細目標に基づき、退院時の状態像（長期目標）と1ヶ月後の目標（短期目標）を文章で記述してください。"
            detailed_rules = """
    - **整合性**: Step 1のADL評価、Step 2の活動目標と矛盾しない目標文を作成してください。
    - **参加目標 (`goal_p_`)**: 復職や復学、家庭内役割などの目標があれば選択してください。不明な場合は予測で埋めず `null` でも構いませんが、テキストに記述がある場合は必ず反映してください。
            """

        elif "Plan" in schema.__name__: # Step 4
            step_instruction = "目標と現状のギャップを埋めるための具体的な治療プログラムとアプローチを立案してください。"
            detailed_rules = """
    - **具体性**: 「歩行訓練」だけでなく、「屋外歩行訓練」「階段昇降訓練」など具体的に記述してください。
    - **Action Plan**: 目標達成のために、患者本人、家族、環境に対してどのような働きかけを行うか記述してください。
            """

        return f"""
あなたは日本のリハビリテーション専門医です。
    **必ず日本語で出力してください。** (Output MUST be in Japanese.)

    臨床推論プロセスに基づき、以下のステップを実行してください。

    **現在のステップ: {step_instruction}**

    # 入力テキスト (ここから数値や詳細情報を読み取ってください)
    {text}

    # AI抽出済み事実 (GLiNER - キーワードのみ)
    ※ここにはFIM点数や具体的な目標文は含まれていません。これらは入力テキストから補完してください。
    {facts_json}
    
    {context_str}

    # 重要事項 (Strict Rules)
    1. **出力言語**: JSONの値(value)は**すべて日本語**で記述してください。英語は禁止です。
    2. **スキーマ遵守**: 以下の「出力スキーマ」で定義されている**キー名のみ**を絶対に使用してください。
       - `func_balance_txt` や `adl_ambulation_...` のような**勝手なキーを作成することは厳禁**です。
       - JSONスキーマにない情報は無視してください。
    3. **値の補完**: テキストに明記がない項目は無理に埋めず `null` にしてください。

    # ステップ固有のルール
    {detailed_rules}

    # 出力スキーマ (この構造を守ること)
    ```json
    {schema_json}
    ```
    """
   
    def _build_prompt(self, text: str, group_schema: type[BaseModel], extracted_data_so_far: dict) -> str:
        """通常モード（段階的抽出）のためのプロンプト構築"""

        # これまでに抽出されたデータを簡潔なサマリーにする
        summary = (
            json.dumps(extracted_data_so_far, indent=2, ensure_ascii=False) if extracted_data_so_far else "まだありません。"
        )

        # 今回の抽出対象スキーマをJSON形式の文字列としてプロンプトに含める
        schema_json = json.dumps(group_schema.model_json_schema(), indent=2, ensure_ascii=False)

        return f"""あなたは医療情報抽出の専門家です。以下の「カルテテキスト」から患者の最新の状態を抽出し、後述する「JSONスキーマ」に従って構造化データを作成してください。

# 指示事項
- テキスト内には、異なる日付の情報が混在している可能性があります。**必ず最も新しい日付の情報や、文脈上最新と思われる情報（例：「現在」「本日」）を優先して抽出してください。**
- 古い情報（例：「初回評価時」「〇月〇日時点では」）は、新しい情報で上書きしてください。
- 例えば、「7/1に疼痛NRS 5/10だったが、7/10にはNRS 3/10に軽減」という記述があれば、疼痛は「NRS 3/10」としてください。
- **最重要**: 今回のタスクでは、以下の「JSONスキーマ」で定義されている項目のみを抽出対象とします。
- **ADLスコアの時系列解釈**: テキスト内に複数の日付のADLスコア（FIMやBI）がある場合、**最も新しいスコアを `_current_val`** に、**その直前のスコア（2番目に新しいスコア）を `_start_val`** に設定してください。スコアが1つしか記録されていない場合は、`_current_val` と `_start_val` の両方に同じ値を設定してください。
- **ADLの記述をFIMスコアに変換してください。** 具体的には、「自立」は7点、「監視・準備」は6点、「最小介助」は5点、「中等度介助」は3点、「全介助」は1点として解釈し、対応する`_fim_current_val`項目に数値を設定してください。
- **基本動作・活動目標のレベル解釈**: テキスト内の記述（例：「寝返りは自立」）を解釈し、対応するラジオボタン用のフィールド（例：`func_basic_rolling_level`）に適切な選択肢の文字列（例：`'independent'`）を設定してください。同時に、関連するチェックボックス（例：`func_basic_rolling_chk` と `func_basic_rolling_independent_chk`）も `true` に設定してください。「一部介助」や「軽介助」は `'partial_assist'` と解釈してください。
- テキストから情報が読み取れない項目は、無理に推測せず、`null`値としてください。
- **`True`の値の保持**: 「これまでに抽出された情報」で既に `True` になっているチェックボックス項目は、カルテテキストから反証（例：「意識障害なし」という明確な記述）が見つからない限り、`True` のまま保持してください。`null` で上書きしないでください。
- **障害者手帳の情報を解釈してください。** 例えば、「右上肢機能障害3級」という記述があれば、`social_disability_certificate_physical_chk`を`true`に、`social_disability_certificate_physical_type_txt`に「上肢」と設定し、`social_disability_certificate_physical_rank_val`に`3`を設定してください。`social_disability_certificate_physical_type_txt`に設定する値は、['視覚', '聴覚', '平衡機能', '言語機能', '音声機能', '咀嚼機能', '上肢', '下肢', '体幹', '心臓機能', '腎臓機能', '呼吸器機能', 'ぼうこう又は直腸機能', '小腸機能', 'ヒト免疫不全ウイルスによる免疫機能', '肝臓機能']の中から最も適切なものを選択してください。
- **嚥下調整食の必要性**: 「嚥下調整食の必要性あり」という記述があれば `nutrition_swallowing_diet_slct` を `'True'` に、「必要性なし」なら `'None'` に設定してください。 `学会分類コード` の情報があれば `nutrition_swallowing_diet_code_txt` に設定してください。
- **栄養状態の評価**: テキスト内の「栄養状態は低栄養リスク」などの記述を解釈し、`nutrition_status_assessment_slct` フィールドに `['no_problem', 'malnutrition', 'malnutrition_risk', 'overnutrition', 'other']` の中から最も適切な値を設定してください。
- **栄養補給方法の親子関係**: 「経口摂取」や「食事」という記述があれば、`nutrition_method_oral_chk`と`nutrition_method_oral_meal_chk`の両方を`true`にしてください。「経管栄養」や「経鼻栄養」という記述があれば`nutrition_method_tube_chk`を`true`にしてください。
- **不整脈の有無**: `func_circulatory_arrhythmia_status_slct` には、不整脈の有無を `'yes'` または `'no'` で設定してください。

## これまでに抽出された情報（今回の抽出の参考にしてください）
```json
{summary}
```

## jsonスキーマ
```json
{schema_json}
```

最重要: スキーマで定義されたキー名（例: "func_pain_txt"）を絶対に変更せず、そのまま使用してJSONを生成してください。

## カルテテキスト (全文)
---
{text}
---
"""

    def _build_generation_prompt(self, text: str, facts: dict, schema: type) -> str:
        """ハイブリッドモード用: 文章生成専用プロンプト"""
        facts_json = json.dumps(facts, indent=2, ensure_ascii=False)
        schema_json = json.dumps(schema.model_json_schema(), indent=2, ensure_ascii=False)
        
        return f"""
    あなたはリハビリテーション専門医です。
    以下の「カルテテキスト」から、AIが見落とした情報の補完と、医学的な考察を行ってください。

    # 入力情報
    1. **AI抽出済み事実 (GLiNER)**: これはキーワードベースで抽出された情報です。基本的に正しいですが、文脈（「～なし」）を考慮していない場合があります。
    2. **カルテテキスト**: 元のテキストです。

    # あなたのタスク
    1. **数値とレベルの判定 (最重要)**:
       - GLiNERは数値を抽出できません。**FIM/BIの点数、ADLの自立度(independent/assistance等)、関節可動域の角度**などをテキストから読み取り、JSONに入力してください。
       - 特に `adl_` で始まるFIM/BIスコアと、`func_basic_` で始まる基本動作レベルは必ず埋めてください。
       
    2. **記述の作成**:
       - `_txt` で終わるフィールドに、専門的な考察記述を作成してください。

    3. **事実の補完**:
       - 「AI抽出済み事実」に含まれていないが、テキストに記載がある情報（例：GLiNERが漏らした疾患名や症状）があれば、それも追加してください。

    # AI抽出済み事実
    ```json
    {facts_json}
    ```

    # JSONスキーマ (この形式で出力)
    ```json
    {schema_json}
    ```

    # カルテテキスト
    {text}
    """

    def parse_text(self, text: str) -> dict:
        """
        与えられたテキストを解析し、複数のスキーマグループに基づいて段階的に情報を抽出し、結果をマージして返す。
        ハイブリッドモードが有効な場合はGLiNER2+LLMを使用し、
        そうでない場合は従来の段階的抽出を行う。
        """
        final_result = {}
        total_start_time = time.time()
        def get_remaining_time():
            elapsed = time.time() - total_start_time
            return max(0.1, GENERATION_TIMEOUT_SEC - elapsed)
        

        # --- ハイブリッドモード (高速・高スペック環境) ---
        if self.use_hybrid_mode and self.fast_extractor:
            print("--- [Step 1] GLiNER2 Extraction (Facts) ---")
            
            # 1. 事実情報の高速抽出 (GLiNER2)
            try:
                facts = self.fast_extractor.extract_facts(text)
                final_result.update(facts)
                # print(f"Extracted Facts ({len(facts)} items) in {time.time() - start_time:.2f}s")
            except Exception as e:
                logger.error(f"GLiNER2 Extraction Error: {e}")
                print(f"事実抽出エラー: {e}")

            print(f"--- [Step 1-3] Multi-stage Generation ({self.client_type}) ---")
            print("\n>>> [DEBUG] GLiNER2 Extracted Facts:")
            pprint.pprint(facts)
            print("-" * 40)

            # 2. LLMによる3段階生成 (HYBRID_GENERATION_GROUPSを使用)
            # 生成専用のプロンプトを作成

            # 2. LLMによる3段階生成 (HYBRID_GENERATION_GROUPSを使用)
            max_retries = 5  # 最大リトライ回数を設定

            for i, group_schema in enumerate(HYBRID_GENERATION_GROUPS):
                # 全体タイムアウトチェック
                if get_remaining_time() <= 1.0:
                    print(f"--- Time Limit Exceeded. Stopping before Step {i+1}. ---")
                    break

                print(f"--- Processing Hybrid Step {i+1}: {group_schema.__name__} ---")
                
                # プロンプト作成 (これまでの結果 final_result を渡す)
                prompt = self._build_hybrid_prompt(text, facts, group_schema, final_result)

                logger.info(f"\n{'='*20} [Step {i+1}] Prompt ({group_schema.__name__}) {'='*20}\n{prompt}\n{'='*60}")

                # --- [DEBUG] プロンプトの表示 ---
                # print(f"\n>>> [DEBUG] Step {i+1} Prompt ({group_schema.__name__}):")
                # print(prompt)
                # print("-" * 40)
                # ------------------------------
                
                step_success = False  # このステップが成功したかどうかのフラグ

                # リトライループ (最大5回)
                for attempt in range(max_retries):
                    current_remaining = get_remaining_time()
                    if current_remaining <= 1.0:
                        print(f"--- Time Limit Exceeded during retry. Stopping. ---")
                        break

                    try:
                        if self.client_type == "gemini":
                            generation_config = types.GenerateContentConfig(
                                response_mime_type="application/json",
                                response_schema=group_schema
                            )
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(
                                    self.client.models.generate_content,
                                    model=self.model_name,
                                    contents=prompt,
                                    config=generation_config
                                )
                                # response = future.result(timeout=current_remaining)
                                response = future.result(timeout=120)
                            if response and response.parsed:
                                step_data = response.parsed.model_dump(mode="json")
                                final_result.update(step_data)

                                # --- [DEBUG] 出力結果の表示 ---
                                # print(f"\n>>> [DEBUG] Step {i+1} Generated Data ({group_schema.__name__}):")
                                # pprint.pprint(step_data)
                                # print("-" * 40)
                                # ----------------------------
                                log_output = json.dumps(step_data, indent=2, ensure_ascii=False) # または generated_data
                                logger.info(f"\n>>> [Step {i+1}] Generated Data ({group_schema.__name__}):\n{log_output}\n{'-'*40}")

                                step_success = True
                                break  # 成功したらリトライループを抜ける
                            
                        else: # Ollama (Local)
                            # 1. 毎回新しいExecutorを作成 (タイムアウト時に即座に中断するため)
                            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
                            try:
                                future = executor.submit(
                                    ollama.chat,
                                    model=self.model_name,
                                    messages=[{"role": "user", "content": prompt}],
                                    format="json",
                                    options={"temperature": 0.2, "num_ctx": 8192}
                                )
                                
                                # 2. 設定した制限時間で結果を待つ
                                # response = future.result(timeout=current_remaining)
                                response = future.result(timeout=120)
                                raw_json = response["message"]["content"]
                                generated_data = json.loads(raw_json)

                                # =====================================================
                                # 【追加】即時構造チェック (Self-Correction Logic)
                                # =====================================================
                                
                                # A. ネスト（階層化）の禁止チェック
                                for key, value in generated_data.items():
                                    if isinstance(value, dict):
                                        raise ValueError(f"不正なネスト構造を検出しました (Key: {key})。フラットなJSONが必要です。")

                                # B. Pydanticスキーマによる厳密なバリデーション
                                try:
                                    # バリデーションのみ実行
                                    group_schema.model_validate(generated_data)
                                except ValidationError as ve:
                                    raise ValueError(f"スキーマ検証エラー: {ve}")

                                # =====================================================

                                final_result.update(generated_data)

                                log_output = json.dumps(generated_data, indent=2, ensure_ascii=False)
                                logger.info(f"\n>>> [Step {i+1}] Generated Data ({group_schema.__name__}):\n{log_output}\n{'-'*40}")

                                step_success = True
                                executor.shutdown(wait=False)
                                break  # 成功したらリトライループを抜ける

                            except Exception as e:
                                error_msg = f"LLM Generation Error (Step {i+1}, Attempt {attempt+1}/{max_retries}): {e}"
                                logger.error(error_msg)
                                print(error_msg)
                                
                                # 失敗時、即座にスレッドを破棄してリトライへ
                                executor.shutdown(wait=False)
                                
                                if attempt < max_retries - 1:
                                    print(f"--- Retrying Step {i+1}... ---")
                                    time.sleep(1)
                                else:
                                    print(f"--- Failed Step {i+1} after {max_retries} attempts. ---")

                    except Exception as e:
                        error_msg = f"LLM Generation Error (Step {i+1}, Attempt {attempt+1}/{max_retries}): {e}"
                        logger.error(error_msg)
                        print(error_msg)
                        
                        # リトライ上限に達していない場合は少し待機して次へ
                        if attempt < max_retries - 1:
                            time.sleep(1)
                        else:
                            print(f"--- Failed Step {i+1} after {max_retries} attempts. ---")

                # 5回失敗した場合、このステップでの生成を諦め、処理全体を中断する（「やめる」）
                if not step_success:
                    print(f"--- Aborting generation process due to repeated errors in Step {i+1} ---")
                    break
            if self.use_hybrid_mode:
                final_result = self._restore_checkboxes(final_result)
            return final_result


        else:
            print("--- Multi-Step Extraction Mode (Standard) ---")
            for i, group_schema in enumerate(PATIENT_INFO_EXTRACTION_GROUPS):
                if get_remaining_time() <= 1.0:
                    print(f"--- Time Limit Exceeded ({GENERATION_TIMEOUT_SEC}s). Stopping extraction. ---")
                    break

                print(f"--- Processing group {i+1}: {group_schema.__name__} ---")

                prompt = self._build_prompt(text, group_schema, final_result)

                logger.info(f"--- Parsing Group: {group_schema.__name__} --- (Client: {self.client_type})")
                
                try:
                    group_result = {}

                    if self.client_type == "gemini":
                        generation_config = types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=group_schema,
                        )
                        # リトライ処理
                        max_retries = 3
                        backoff_factor = 2
                        response = None
                        for attempt in range(max_retries):
                            # 【修正】試行ごとに残り時間を再計算
                            current_timeout = get_remaining_time()
                            if current_timeout <= 1.0:
                                break

                            try:
                                with concurrent.futures.ThreadPoolExecutor() as executor:
                                    future = executor.submit(
                                        self.client.models.generate_content,
                                        model=self.model_name,
                                        contents=prompt,
                                        config=generation_config
                                    )
                                    # 【修正】残り時間をタイムアウトに設定
                                    response = future.result(timeout=current_timeout)
                                break
                            except (ResourceExhausted, ServiceUnavailable, concurrent.futures.TimeoutError) as e:
                                if attempt < max_retries - 1:
                                    wait_time = backoff_factor * (2**attempt)
                                    time.sleep(min(wait_time, get_remaining_time())) # 待機時間も残り時間以内にする
                                else:
                                    raise e

                        if response and response.parsed:
                            group_result = response.parsed.model_dump(mode="json")

                    else:
                        # Ollama (Local)
                        max_retries = 3
                        ollama_response = None

                        for attempt in range(max_retries):
                            current_timeout = get_remaining_time()
                            if current_timeout <= 1.0:
                                break

                            try:
                                with concurrent.futures.ThreadPoolExecutor() as executor:
                                    future = executor.submit(
                                        ollama.chat,
                                        model=self.model_name,
                                        messages=[{"role": "user", "content": prompt}],
                                        format="json",
                                    )
                                    # 【修正】残り時間をタイムアウトに設定
                                    ollama_response = future.result(timeout=current_timeout)
                                break

                            except (concurrent.futures.TimeoutError, Exception) as e:
                                if attempt < max_retries - 1:
                                    time.sleep(1)
                                else:
                                    logger.warning(f"Ollama failed after retries: {e}")
                                    ollama_response = None

                        if ollama_response:
                            raw_json_str = ollama_response["message"]["content"]
                            try:
                                raw_response_dict = json.loads(raw_json_str)
                                # (以下、バリデーションロジックは既存と同じなので省略可だが記述しておく)
                                data_to_validate = raw_response_dict
                                if isinstance(raw_response_dict, dict):
                                    schema_fields = set(group_schema.model_fields.keys())
                                    if not schema_fields.issubset(raw_response_dict.keys()):
                                        for v in raw_response_dict.values():
                                            if isinstance(v, dict) and schema_fields.intersection(v.keys()):
                                                data_to_validate = v
                                                break
                                group_result_obj = group_schema.model_validate(data_to_validate)
                                group_result = group_result_obj.model_dump(mode="json")
                            except Exception as e:
                                logger.warning(f"Ollama JSON Error: {e}")
                                group_result = {}

                            # 性別の正規化
                            if "gender" in group_result and group_result["gender"]:
                                if "男性" in group_result["gender"]:
                                    group_result["gender"] = "男"
                                elif "女性" in group_result["gender"]:
                                    group_result["gender"] = "女"

                            final_result.update(group_result)
                except concurrent.futures.TimeoutError:
                    current_remaining = get_remaining_time()
                    error_msg = f"Group {i+1} Timed Out (Remaining: {current_remaining:.1f}s)"
                    logger.error(error_msg)
                    print(f"LLM生成エラー(Group {i+1}): {error_msg}")
                    continue
                
                except Exception as e:
                    print(f"グループ {group_schema.__name__} の解析中にエラーが発生しました: {e}")
                    logger.error(f"Parser Error (Group: {group_schema.__name__}): {e}", exc_info=True)
                    continue
                
                # レート制限対策 (残り時間がある場合のみ)
                if get_remaining_time() > 1.0:
                    time.sleep(0.5)

            if not final_result:
                return {
                    "error": "患者情報の解析に失敗しました。",
                    "details": "どのグループからも有効な情報を抽出できませんでした。",
                }

            return final_result