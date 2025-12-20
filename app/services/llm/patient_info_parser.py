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

from app.schemas.schemas import PATIENT_INFO_EXTRACTION_GROUPS, PlanGenerationSchema # 分割したスキーマのリストをインポート
from app.services.extraction.fast_extractor import FastExtractor

load_dotenv()
GENERATION_TIMEOUT_SEC = 40

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
        
        # 指示通り、バッククォートの前に4スペースを入れています
        return f"""
    あなたはリハビリテーション専門医です。
    以下の「カルテテキスト」と、AIにより自動抽出された「患者事実情報」に基づき、リハビリ計画書の考察・方針項目を作成してください。

    # 患者事実情報（GLiNER2により抽出済み）

    この情報は正しいものとして扱ってください。
    ```json
    {facts_json}
    ```

    # 指示

    * 上記の事実情報とカルテテキストを統合し、医学的に妥当な「考察」「目標」「方針」を記述してください。
    * 専門用語を適切に使用し、かつ患者・家族にも伝わる丁寧な表現を心がけてください。
    * 出力は必ず以下のJSONスキーマに従ってください。
    * 生成対象以外のキー（チェックボックスなど）は出力に含めないでください。

    # JSONスキーマ

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

        # --- ハイブリッドモード (高速・高スペック環境) ---
        if self.use_hybrid_mode and self.fast_extractor:
            print("--- [Step 1] GLiNER2 Extraction (Facts) ---")
            start_time = time.time()
            
            # 1. 事実情報の高速抽出 (GLiNER2)
            try:
                facts = self.fast_extractor.extract_facts(text)
                final_result.update(facts)
                print(f"Extracted Facts ({len(facts)} items) in {time.time() - start_time:.2f}s")
            except Exception as e:
                logger.error(f"GLiNER2 Extraction Error: {e}")
                print(f"事実抽出エラー: {e}")

            print(f"--- [Step 2] Generation (Plan) using {self.client_type} ---")
            print("\n>>> [DEBUG] GLiNER2 Extracted Facts:")
            pprint.pprint(facts)
            print("-" * 40)
            # 2. LLMによる文章生成 (PlanGenerationSchemaを使用)
            # 生成専用のプロンプトを作成
            prompt = self._build_generation_prompt(text, final_result, PlanGenerationSchema)
            
            try:
                if self.client_type == "gemini":
                    # Geminiで生成 (1回のリクエスト)
                    generation_config = types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=PlanGenerationSchema
                    )

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            self.client.models.generate_content,
                            model=self.model_name,
                            contents=prompt,
                            config=generation_config
                        )
                        response = future.result(timeout=GENERATION_TIMEOUT_SEC)

                    if response and response.parsed:
                        final_result.update(response.parsed.model_dump(mode="json"))


                    # response = self.client.models.generate_content(
                    #     model=self.model_name, contents=prompt, config=generation_config
                    # )
                    # if response and response.parsed:
                    #     final_result.update(response.parsed.model_dump(mode="json"))
                else:
                    # Ollamaで生成 (1回のリクエスト)

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            ollama.chat,
                            model=self.model_name,
                            messages=[{"role": "user", "content": prompt}],
                            format="json",
                            options={"temperature": 0.2, "num_ctx": 8192}
                        )
                        response = future.result(timeout=GENERATION_TIMEOUT_SEC)



                    # response = ollama.chat(
                    #     model=self.model_name,
                    #     messages=[{"role": "user", "content": prompt}],
                    #     format="json",
                    #     options={"temperature": 0.2, "num_ctx": 8192}
                    # )
                    raw_json = response["message"]["content"]
                    print("\n>>> [DEBUG] Ollama Raw JSON Response:")
                    print(raw_json[:6000] + "..." if len(raw_json) > 1000 else raw_json)
                    generated_data = json.loads(raw_json)
                    final_result.update(generated_data)

            except Exception as e:
                logger.error(f"LLM Generation Error ({self.client_type}): {e}")
                print(f"LLM生成エラー: {e}")

            return final_result

        # --- 通常モード (従来の段階的抽出: クラウド/低スペック環境) ---
        else:
            print("--- Multi-Step Extraction Mode (Standard) ---")
            for group_schema in PATIENT_INFO_EXTRACTION_GROUPS:
                print(f"--- Processing group: {group_schema.__name__} ---")
                prompt = self._build_prompt(text, group_schema, final_result)

                logger.info(f"--- Parsing Group: {group_schema.__name__} --- (Client: {self.client_type})")
                
                try:
                    group_result = {}

                    if self.client_type == "gemini":
                        generation_config = types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=group_schema,
                        )
                        # リトライ処理を追加
                        max_retries = 3
                        backoff_factor = 2  # 初回待機時間（秒）
                        response = None
                        for attempt in range(max_retries):
                            try:
                                with concurrent.futures.ThreadPoolExecutor() as executor:
                                    future = executor.submit(
                                        self.client.models.generate_content,
                                        model=self.model_name,
                                        contents=prompt,
                                        config=generation_config
                                    )
                                    response = future.result(timeout=GENERATION_TIMEOUT_SEC)
                                # response = self.client.models.generate_content(
                                #     model=self.model_name, contents=prompt, config=generation_config
                                # )
                                break  # 成功した場合はループを抜ける
                            except (ResourceExhausted, ServiceUnavailable, concurrent.futures.TimeoutError) as e:
                                if attempt < max_retries - 1:
                                    wait_time = backoff_factor * (2**attempt)
                                    error_type = "タイムアウト" if isinstance(e, concurrent.futures.TimeoutError) else "APIエラー"
                                    print(
                                        f"   [警告] {error_type}。{wait_time}秒後に再試行します... ({attempt + 1}/{max_retries})"
                                    )

                                    time.sleep(wait_time)
                                else:
                                    print(f"   [エラー] API呼び出しが{max_retries}回失敗しました。")
                                    raise e  # 最終的に失敗した場合はエラーを再送出

                        if response and response.parsed:
                            group_result = response.parsed.model_dump(mode="json")
                        else:
                            print(f"   [警告] グループ {group_schema.__name__} (Gemini) の解析で有効な結果が得られませんでした。")
                    # リトライ処理ここまで

                    else:
                        # Ollama (Local)
                        # (self.client は使わず、ollamaライブラリを直接使用)
                        max_retries = 3
                        ollama_response = None


                        for attempt in range(max_retries):
                            try:
                                with concurrent.futures.ThreadPoolExecutor() as executor:
                                    future = executor.submit(
                                        ollama.chat,
                                        model=self.model_name,
                                        messages=[{"role": "user", "content": prompt}],
                                        format="json",  # ストリーミングなし
                                    )
                                    # 60秒制限
                                    ollama_response = future.result(timeout=GENERATION_TIMEOUT_SEC)
                                break # 成功したらループを抜ける

                            except (concurrent.futures.TimeoutError, Exception) as e:
                                if attempt < max_retries - 1:
                                    print(f"   [警告] Ollamaエラー/タイムアウト: {e}。再試行します... ({attempt + 1}/{max_retries})")
                                    time.sleep(1)
                                else:
                                    logger.warning(f"Ollama failed after retries: {e}")
                                    ollama_response = None

                        if ollama_response:
                            raw_json_str = ollama_response["message"]["content"]
                            logger.info(f"Ollama Raw Response (Parser, Group: {group_schema.__name__}):\n{raw_json_str}")
                            try:
                                raw_response_dict = json.loads(raw_json_str)
                                # Pydantic検証 (Ollamaのネスト対策含む簡易版)
                                data_to_validate = raw_response_dict
                                if isinstance(raw_response_dict, dict):
                                    schema_fields = set(group_schema.model_fields.keys())
                                    if not schema_fields.issubset(raw_response_dict.keys()):
                                        # ネストを探す簡易ロジック
                                        for v in raw_response_dict.values():
                                            if isinstance(v, dict) and schema_fields.intersection(v.keys()):
                                                data_to_validate = v
                                                break
                                
                                group_result_obj = group_schema.model_validate(data_to_validate)
                                group_result = group_result_obj.model_dump(mode="json")
                            except Exception as e:
                                logger.warning(f"Ollama JSON Error: {e}")
                                group_result = {}

                            # 性別の正規化など
                            if "gender" in group_result and group_result["gender"]:
                                if "男性" in group_result["gender"]:
                                    group_result["gender"] = "男"
                                elif "女性" in group_result["gender"]:
                                    group_result["gender"] = "女"

                            final_result.update(group_result)
                        
                        else:
                            # レスポンスが取れなかった場合（全リトライ失敗）
                            print(f"   [エラー] グループ {group_schema.__name__} (Ollama) の解析に失敗しました。")


                    #     ollama_response = ollama.chat(
                    #         model=self.model_name,  # (self.model_name は __init__ で 'qwen3:8b' 等に設定されている)
                    #         messages=[{"role": "user", "content": prompt}],
                    #         format="json",  # ストリーミングなし
                    #     )

                    #     raw_json_str = ollama_response["message"]["content"]
                    #     logger.info(f"Ollama Raw Response (Parser, Group: {group_schema.__name__}):\n{raw_json_str}")
                    #     try:
                    #         raw_response_dict = json.loads(raw_json_str)
                    #         # Pydantic検証 (Ollamaのネスト対策含む簡易版)
                    #         data_to_validate = raw_response_dict
                    #         if isinstance(raw_response_dict, dict):
                    #             schema_fields = set(group_schema.model_fields.keys())
                    #             if not schema_fields.issubset(raw_response_dict.keys()):
                    #                 # ネストを探す簡易ロジック
                    #                 for v in raw_response_dict.values():
                    #                     if isinstance(v, dict) and schema_fields.intersection(v.keys()):
                    #                         data_to_validate = v
                    #                         break
                            
                    #         group_result_obj = group_schema.model_validate(data_to_validate)
                    #         group_result = group_result_obj.model_dump(mode="json")
                    #     except Exception as e:
                    #         logger.warning(f"Ollama JSON Error: {e}")
                    #         group_result = {}

                    # # 性別の正規化など
                    # if "gender" in group_result and group_result["gender"]:
                    #     if "男性" in group_result["gender"]:
                    #         group_result["gender"] = "男"
                    #     elif "女性" in group_result["gender"]:
                    #         group_result["gender"] = "女"

                    # final_result.update(group_result)

                except Exception as e:
                    print(f"グループ {group_schema.__name__} の解析中にエラーが発生しました: {e}")
                    logger.error(f"Parser Error (Group: {group_schema.__name__}): {e}", exc_info=True)
                    continue
                
                # レート制限対策
                time.sleep(0.5)

            if not final_result:
                return {
                    "error": "患者情報の解析に失敗しました。",
                    "details": "どのグループからも有効な情報を抽出できませんでした。",
                }

            return final_result