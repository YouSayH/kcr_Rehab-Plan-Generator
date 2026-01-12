import concurrent.futures
import json
import logging
import os
import pprint  # デバッグ表示用に追加
import time

from dotenv import load_dotenv
from pydantic import BaseModel

# from app.schemas.schemas import HYBRID_GENERATION_GROUPS, PATIENT_INFO_EXTRACTION_GROUPS
from app.schemas.schemas import (
    PATIENT_INFO_EXTRACTION_GROUPS,
    HYBRID_COMBINED_GROUPS  # <--- 新しく作った統合グループのみインポート
)
from app.services.extraction.fast_extractor import FastExtractor

# リファクタリング: ファクトリ関数のインポート
from app.services.llm import get_llm_client

load_dotenv()
GENERATION_TIMEOUT_SEC = 300

logger = logging.getLogger(__name__)

def optimize_schema_for_prompt(schema_cls: type, target_fields_pattern: str = None, filter_mode: bool = False) -> dict:
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
        # A. フィルタリング (Hybridモード用)
        if filter_mode:
            # 除外対象: _chk
            if key.endswith('_chk'):
                continue
            
            # 許可対象: _txt (文章) と _val (数値) のみ
            if not (key.endswith('_txt') or key.endswith('_val')):
                continue

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


def get_standardization_prompt(text: str) -> str:
    return f"""
あなたは熟練した診療情報管理士です。
以下の「カルテテキスト（自然言語）」を読み、そこに含まれる医学的情報を**「標準的な医学用語」と「明確なステータス」に変換して箇条書き**にしてください。

# 目的
この出力は、後段のシステムでキーワード検索に使用されます。
曖昧な表現（例：「足がおぼつかない」）は、必ず明確な医学用語（例：「歩行障害」「運動失調」）に書き換えてください。

# 変換ルール（必ず守ること）
1. **疾患・既往歴**: 「高め」「疑い」などの表現も、医学的な病名（高血圧症、糖尿病、脂質異常症など）として記載する。
2. **症状**: 「むせる」→「嚥下障害」、「言葉が出ない」→「失語症」、「しびれ」→「感覚鈍麻」のように変換する。
3. **ADL（日常生活動作）**:
   - 「自分でできる」 → 「自立」
   - 「手助けが必要」「見守り」 → 「介助」
   - 「できない」 → 「全介助」または「不可」
   と明記する。
4. **否定**: 「なし」「見られない」という情報は、「麻痺なし」「疼痛なし」のように明確に否定語をつけて記載する。

# 出力フォーマット
- 診断名: [病名]
- 既往歴: [疾患名リスト]
- 身体機能: [麻痺、筋力、痛み、関節可動域などの用語]
- 精神・認知: [認知症、高次脳機能障害などの用語]
- ADL状態: [食事・排泄・入浴・移動などの動作名] + [自立/介助]
- 社会背景: [介護保険、キーパーソンなど]

# 入力テキスト
{text}

# 標準化された要約（箇条書きのみ出力）
"""


class PatientInfoParser:
    """
    LLMを使用して、非構造化テキストから構造化された患者情報を抽出するクラス。
    Refactoring: 共通のLLMClientを使用し、Gemini/Ollamaの差異を吸収しています。

    モード:
    1. 通常モード (Gemini/Ollama): スキーマをグループに分割して段階的に抽出する（高精度・低スペック環境向け）。
    2. ハイブリッドモード (Local GPU): GLiNER2で事実を高速抽出し、LLMで考察のみを生成する（高速・高スペック環境向け）。
    """

    def __init__(self, use_hybrid_mode: bool = False):
        self.llm_client = get_llm_client()

        # ログ出力用にクラス名から判定
        client_class_name = self.llm_client.__class__.__name__
        self.client_type = "gemini" if "Gemini" in client_class_name else "ollama"

        self.use_hybrid_mode = use_hybrid_mode

        # 設定がない場合は、メインのモデル(OLLAMA_MODEL_NAME)を使用する。
        default_ollama_model = os.getenv("OLLAMA_MODEL_NAME", "qwen3:8b")
        self.ollama_model_name = os.getenv("OLLAMA_EXTRACTION_MODEL_NAME", default_ollama_model)

        print(f"PatientInfoParser: {client_class_name} を使用します。")

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
        LLMが生成した軽量データからDB保存用のチェックボックスを復元する後処理
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

    def _build_hybrid_prompt(self, text: str, facts: dict, schema_json: str) -> str:        
        """ハイブリッドモード用: 段階的生成プロンプト"""
        facts_json = json.dumps(facts, indent=2, ensure_ascii=False)
        
        return f"""
    あなたは日本のリハビリテーション専門医です。
    **必ず日本語で出力してください。** (Output MUST be in Japanese.)

    臨床推論プロセスに基づき、以下のステップを実行してください。

    # 入力テキスト (ここから数値や詳細情報を読み取ってください)
    {text}

    # AI抽出済み事実 (GLiNER - キーワードのみ)
    ※ここにはFIM点数や具体的な目標文は含まれていません。これらは入力テキストから補完してください。
    ```json
    {facts_json}
    ```

    # 重要事項 (Strict Rules)
    1. **出力言語**: JSONの値(value)は**すべて日本語**で記述してください。
    2. **FIM採点基準**: テキストの記述を以下の基準で数値（1-7）に変換してください。
       - **7点 (完全自立)**: 補助具なし、時間内、安全。
       - **6点 (修正自立)**: 補助具使用、時間がかかる、投薬など。
       - **5点 (監視・準備)**: 監視、指示、準備が必要。触れてはいない。
       - **4点 (最小介助)**: 75%以上自分でできる。軽く触れる程度。
       - **3点 (中等度介助)**: 50%〜75%自分でできる。
       - **2点 (最大介助)**: 25%〜50%自分でできる。引き上げなど強い介助。
       - **1点 (全介助)**: 25%未満しかできない。2人介助。
    3. **値の補完**: テキストに明記がない項目は無理に埋めず `null` にしてください。
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

    def _standardize_text(self, text: str) -> str:
        """
        LLMを使って、生テキストを「FastExtractorが抽出しやすい標準用語」に変換する。
        """
        prompt = f"""
あなたは熟練した診療情報管理士です。
以下の「カルテテキスト」を読み、含まれる情報を**「標準的な医学用語」に変換して箇条書き**にしてください。
JSONではなく、プレーンテキストで出力してください。

# 変換の指針
- **病名**: 「血圧高め」→「既往歴に高血圧症あり」、「糖尿の気がある」→「糖尿病あり」
- **症状**: 「むせる」→「嚥下障害あり」、「呂律が回らない」→「構音障害あり」、「言葉が出にくい」→「失語症あり」
- **ADL**: 「一人でできる」→「自立」、「手伝い」→「介助」
- **否定**: 「特に問題なし」→「障害なし」

# 入力テキスト
{text}

# 標準化された要約
"""
        try:
            # generate_textメソッドを使用 (JSONモードではない)
            # ※ llm_clientに generate_text が実装されている前提
            # もし generate_json しかない場合は、単一キーのJSONを作らせるか、generate_contentを呼ぶ
            if hasattr(self.llm_client, 'generate_text'):
                return self.llm_client.generate_text(prompt)
            elif hasattr(self.llm_client, 'generate_content'):
                return self.llm_client.generate_content(prompt)
            else:
                # フォールバック: 単純なテキスト生成がなければそのまま返す（または実装する）
                return text
        except Exception as e:
            logger.error(f"Standardization failed: {e}")
            return text


    # def parse_text(self, text: str) -> dict:
    #     """
    #     与えられたテキストを解析し、複数のスキーマグループに基づいて段階的に情報を抽出し、結果をマージして返す。
    #     ハイブリッドモードが有効な場合はGLiNER2+LLMを使用し、
    #     そうでない場合は従来の段階的抽出を行う。
    #     """
    #     final_result = {}
    #     total_start_time = time.time()
    #     def get_remaining_time():
    #         elapsed = time.time() - total_start_time
    #         return max(0.1, GENERATION_TIMEOUT_SEC - elapsed)


    #     # --- ハイブリッドモード ---
    #     target_groups = []
    #     is_hybrid = False
    #     if self.use_hybrid_mode and self.fast_extractor:
    #         print("--- [Step 1] GLiNER2 Extraction (Facts) ---")

    #         standardized_text = self._standardize_text(text)
    #         print(f">>> Standardized Text Preview:\n{standardized_text[:200]}...")
            
    #         # 2. 原文と撒き餌を結合
    #         # 区切り線を入れておくことで、NegExが文脈を混同するのを防ぐ（改行重要）
    #         combined_text = text + "\n\n" + ("="*20) + "\n[AI補完情報]\n" + standardized_text
            
    #         print("--- [Step 1] FastExtractor (Regex+NegEx) ---")

    #         # 1. 事実情報の高速抽出 (GLiNER2)
    #         try:
    #             facts = self.fast_extractor.extract_facts(text)
    #             final_result.update(facts)
    #             # print(f"Extracted Facts ({len(facts)} items) in {time.time() - start_time:.2f}s")
    #         except Exception as e:
    #             logger.error(f"GLiNER2 Extraction Error: {e}")
    #             print(f"事実抽出エラー: {e}")

    #         print(f"--- [Step 1-3] Multi-stage Generation ({self.client_type}) ---")
    #         print("\n>>> [DEBUG] GLiNER2 Extracted Facts:")
    #         pprint.pprint(facts)
    #         target_groups = HYBRID_GENERATION_GROUPS
    #         is_hybrid = True
    #     else:
    #         print("--- Multi-Step Extraction Mode (Standard) ---")
    #         target_groups = PATIENT_INFO_EXTRACTION_GROUPS

    #     # ----------------------------------------------------
    #     # 共通の生成ループ (Gemini/Ollamaの違いはLLMClientで吸収)
    #     # ----------------------------------------------------
    #     max_retries = 5

    #     for i, group_schema in enumerate(target_groups):
    #         # 全体タイムアウトチェック
    #         if get_remaining_time() <= 1.0:
    #             print(f"--- Time Limit Exceeded. Stopping before Step {i+1}. ---")
    #             break

    #         # --- スキーマ最適化 & フィルタリング ---
    #         # ハイブリッドモードなら _chk, _level, _slct を除外
    #         optimized_schema = optimize_schema_for_prompt(group_schema, filter_mode=is_hybrid)
            
    #         # プロパティが空（生成すべき項目がない）場合はスキップ
    #         if not optimized_schema["properties"]:
    #             print(f"--- Skipping Step {i+1}: {group_schema.__name__} (All fields handled by GLiNER) ---")
    #             continue

    #         print(f"--- Processing Step {i+1}: {group_schema.__name__} ---")
    #         schema_json = json.dumps(optimized_schema, indent=2, ensure_ascii=False)

    #         # プロンプト作成
    #         if is_hybrid:
    #             prompt = self._build_hybrid_prompt(text, final_result, schema_json)
    #         else:
    #             prompt = self._build_prompt(text, group_schema, final_result)


    #         logger.info(f"\n{'='*20} [Step {i+1}] Prompt ({group_schema.__name__}) {'='*20}\n{prompt}\n{'='*60}")

    #         step_success = False

    #         # リトライループ
    #         for attempt in range(max_retries):
    #             current_remaining = get_remaining_time()
    #             if current_remaining <= 1.0:
    #                 print("--- Time Limit Exceeded during retry. Stopping. ---")
    #                 break

    #             try:
    #                 # リファクタリング: llm_client.generate_json を呼び出す
    #                 # タイムアウト制御のためにThreadPoolExecutorでラップする
    #                 with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
    #                     future = executor.submit(
    #                         self.llm_client.generate_json,
    #                         prompt=prompt,
    #                         schema=group_schema
    #                     )
    #                     # API呼び出し自体のタイムアウトを全体残り時間に合わせる
    #                     step_data = future.result(timeout=min(120, current_remaining))

    #                 final_result.update(step_data)

    #                 log_output = json.dumps(step_data, indent=2, ensure_ascii=False)
    #                 logger.info(f"\n>>> [Step {i+1}] Generated Data ({group_schema.__name__}):\n{log_output}\n{'-'*40}")

    #                 step_success = True
    #                 break  # 成功したらリトライループを抜ける

    #             except concurrent.futures.TimeoutError:
    #                 error_msg = f"Step {i+1} Timed Out (Remaining: {current_remaining:.1f}s)"
    #                 logger.error(error_msg)
    #                 print(error_msg)
    #                 break

    #             except Exception as e:
    #                 error_msg = f"LLM Generation Error (Step {i+1}, Attempt {attempt+1}/{max_retries}): {e}"
    #                 logger.error(error_msg)
    #                 print(error_msg)

    #                 if attempt < max_retries - 1:
    #                     time.sleep(1)
    #                 else:
    #                     print(f"--- Failed Step {i+1} after {max_retries} attempts. ---")

    #         if not step_success and get_remaining_time() <= 1.0:
    #             print(f"--- Aborting generation process due to timeout in Step {i+1} ---")
    #             break

    #     # 後処理
    #     if self.use_hybrid_mode:
    #         final_result = self._restore_checkboxes(final_result)

    #     if not final_result:
    #         return {
    #             "error": "患者情報の解析に失敗しました。",
    #             "details": "どのグループからも有効な情報を抽出できませんでした。",
    #         }

    #     return final_result


    def parse_text(self, text: str) -> dict:
        """
        ハイブリッドモード: 標準化 -> Regex -> LLM(統合スキーマで2回実行)
        通常モード: 順次抽出
        """
        final_result = {}
        total_start_time = time.time()
        
        # --- Step 1 & 2: Standardization & Fast Extraction ---
        if self.use_hybrid_mode and self.fast_extractor:
            print("--- [Step 1] Standardizing Text (LLM) ---")
            standardized_text = self._standardize_text(text)
            print(f">>> Standardized Text Preview:\n{standardized_text[:100]}...")
            
            # 原文と標準化テキストを結合
            combined_text = text + "\n\n" + ("="*20) + "\n[AI補完情報]\n" + standardized_text
            
            print("--- [Step 2] FastExtractor (Regex+NegEx) ---")
            try:
                facts = self.fast_extractor.extract_facts(combined_text)
                final_result.update(facts)
                pprint.pprint(facts)
            except Exception as e:
                logger.error(f"FastExtractor Error: {e}")

        # --- Step 3: LLM Detailed Extraction (Batched) ---
        print(f"--- [Step 3] Detailed Extraction (LLM: {self.client_type}) ---")

        # バッチ定義: 統合スキーマを使用することで呼び出し回数を削減 (実質2回)
        extraction_batches = []
        if self.use_hybrid_mode:
            # HYBRID_COMBINED_GROUPS = [HybridCombined_Extraction, HybridCombined_Plan]
            # 各要素を1つのリストに入れることで、依存関係(Extraction -> Plan)を順次処理として表現
            extraction_batches = [[group] for group in HYBRID_COMBINED_GROUPS]
        else:
            # 通常モードは順次実行
            extraction_batches = [[g] for g in PATIENT_INFO_EXTRACTION_GROUPS]

        # バッチ実行ループ
        for batch_index, batch in enumerate(extraction_batches):
            print(f"--- Processing Batch {batch_index + 1}/{len(extraction_batches)} ---")
            batch_results = {}

            # ThreadPoolExecutorによる並列実行
            # (現在は1バッチ1アイテムだが、将来的に分割した場合に対応可能な構造)
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(batch)) as executor:
                future_to_schema = {}
                for schema in batch:
                    # プロンプト作成
                    if self.use_hybrid_mode:
                        # フィルタリング有効化 (True: _chk除外, _val/_level/_txtなどは残す)
                        opt_schema = optimize_schema_for_prompt(schema, filter_mode=True)
                        if not opt_schema["properties"]: continue
                        
                        prompt = self._build_hybrid_prompt(
                            text, # 数値抽出のために原文を渡す
                            final_result, # 直前のバッチまでの結果をコンテキストとして渡す
                            json.dumps(opt_schema, indent=2, ensure_ascii=False)
                        )
                    else:
                        prompt = self._build_prompt(text, schema, final_result)

                    future = executor.submit(
                        self.llm_client.generate_json,
                        prompt=prompt,
                        schema=schema
                    )
                    future_to_schema[future] = schema

                # 結果収集
                for future in concurrent.futures.as_completed(future_to_schema):
                    schema = future_to_schema[future]
                    try:
                        # 統合スキーマは生成量が多いのでタイムアウトを長めに設定(180秒)
                        data = future.result(timeout=180)
                        if data:
                            batch_results.update(data)
                            logger.info(f"Finished: {schema.__name__}")
                    except Exception as e:
                        logger.error(f"Error in {schema.__name__}: {e}")

            # バッチ完了後に結果を統合
            final_result.update(batch_results)

        # 後処理
        if self.use_hybrid_mode:
            final_result = self._restore_checkboxes(final_result)

        if not final_result:
            return {"error": "抽出に失敗しました。"}


        print("\n" + "="*30 + " FINAL EXTRACTION RESULT " + "="*30)
        try:
            # pprintで整形して表示（日本語も崩れにくい設定）
            pprint.pprint(final_result, width=120, sort_dicts=True)
        except Exception as e:
            print(f"Result printing failed: {e}")
        print("="*85 + "\n")

        return final_result