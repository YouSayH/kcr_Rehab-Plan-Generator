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
GENERATION_TIMEOUT_SEC = 120

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

    def _build_hybrid_prompt(self, text: str, facts: dict, schema: type, previous_steps_data: dict) -> str:

        """ハイブリッドモード用: 段階的生成プロンプト"""
        facts_json = json.dumps(facts, indent=2, ensure_ascii=False)
        schema_json = json.dumps(schema.model_json_schema(), indent=2, ensure_ascii=False)
        
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
        if "Assessment" in schema.__name__: # Step 1
            step_instruction = "GLiNERが抽出した事実を基に、FIM/BIの点数補完、リスクの洗い出し、機能障害の詳細記述を行ってください。"
            detailed_rules = """
    - **FIM/BIスコア**: テキストから必ず数値を読み取ってください。最新値を `_current_val`、開始時を `_start_val` に入れます。
    - **基本動作**: `func_basic_` 系のレベル（自立/介助など）をテキストから判定してください。
    - **リスク・機能**: `_txt` 項目には、具体的な症状や程度を記述してください。
            """

        elif "DetailedGoals" in schema.__name__: # Step 2
            step_instruction = "現状評価（Step 1）に基づき、各活動項目（排泄、入浴、移動など）や環境因子の具体的な到達目標レベルを設定してください。"
            detailed_rules = """
    - **活動目標 (`goal_a_`)**: 現在のADL能力よりも「少し高い」または「維持」となる現実的な目標レベルを設定してください。
    - **チェックボックス**: 目標とする動作レベル（例: `goal_a_toileting_independent_chk`）を積極的に `True` にしてください。
    - **環境・人的因子**: 家屋改修や家族指導が必要と思われる場合は、該当する項目を `True` にしてください。
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
                                response = future.result(timeout=current_remaining)

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

                        else: # Ollama
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(
                                    ollama.chat,
                                    model=self.model_name,
                                    messages=[{"role": "user", "content": prompt}],
                                    format="json",
                                    options={"temperature": 0.2, "num_ctx": 8192}
                                )
                                response = future.result(timeout=current_remaining)

                            raw_json = response["message"]["content"]
                            generated_data = json.loads(raw_json)
                            final_result.update(generated_data)

                            # --- [DEBUG] 出力結果の表示 ---
                            # print(f"\n>>> [DEBUG] Step {i+1} Generated Data ({group_schema.__name__}):")
                            # pprint.pprint(generated_data)
                            # print("-" * 40)
                            # ----------------------------
                            log_output = json.dumps(step_data, indent=2, ensure_ascii=False) # または generated_data
                            logger.info(f"\n>>> [Step {i+1}] Generated Data ({group_schema.__name__}):\n{log_output}\n{'-'*40}")

                            step_success = True
                            break  # 成功したらリトライループを抜ける

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