import json
import logging
import os
import time
from typing import Any, Dict, Generator, Optional, Type

from dotenv import load_dotenv
from google import genai
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable
from google.genai import types
from pydantic import BaseModel, Field, create_model

from app.schemas.schemas import GENERATION_GROUPS
from app.services.llm.base import LLMClient
from app.services.llm.context_builder import (
    CHECK_TO_TEXT_MAP,
    USER_INPUT_FIELDS,
    prepare_patient_facts,
)
from app.services.llm.prompts import build_group_prompt, build_regeneration_prompt
from app.services.llm.rag_executor import RAGExecutor

load_dotenv()
logger = logging.getLogger(__name__)

# --- 初期設定 ---
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    # 警告を出すが、実行時エラーにはしない（テスト環境等のため）
    logger.warning("GOOGLE_API_KEYが設定されていません。")

# 新しいGeminiライブラリのクライアント初期化
# APIキーは環境変数 `GOOGLE_API_KEY` から自動で読み込まれる
try:
    client = genai.Client()
except Exception as e:
    logger.error(f"Gemini Client initialization failed: {e}")
    client = None

# プロトタイプ開発用の設定
USE_DUMMY_DATA = False


class GeminiClient(LLMClient):
    """
    Google Gemini APIを使用したLLMクライアントの実装
    """

    def generate_plan_stream(self, patient_data: Dict[str, Any]) -> Generator[str, None, None]:
        """
        Geminiモデルを使用して計画案をストリーミングで生成する。
        """
        if USE_DUMMY_DATA:
            yield self._create_event("error", {"error": "ダミーデータモードは現在サポートされていません。"})
            return

        try:
            # 1. 患者情報の整形 (共通ロジック使用)
            patient_facts = prepare_patient_facts(patient_data)
            patient_facts_str = json.dumps(patient_facts, indent=2, ensure_ascii=False)
            generated_plan_so_far = {}

            # ユーザーが既に入力済みの項目を先に処理
            for field_name in USER_INPUT_FIELDS:
                if patient_data.get(field_name):
                    value = patient_data[field_name]
                    generated_plan_so_far[field_name] = value
                    yield self._create_event("update", {"key": field_name, "value": value, "model_type": "general"})

            # 2. グループごとに生成
            for group_schema in GENERATION_GROUPS:
                # プロンプト構築 (共通ロジック使用)
                prompt = build_group_prompt(
                    group_schema,
                    patient_facts_str,
                    generated_plan_so_far,
                    is_ollama=False
                )

                logger.info(f"--- Generating Group: {group_schema.__name__} ---")

                # API呼び出し設定 (JSONモード)
                generation_config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=group_schema,
                )

                # API呼び出し (リトライ付き)
                response = self._call_api_with_retry(prompt, generation_config)

                if not response or not response.parsed:
                    raise Exception(f"グループ {group_schema.__name__} のJSON生成に失敗しました。")

                group_result = response.parsed.model_dump()

                # 3. 結果の処理とストリーミング
                for field_name, generated_text in group_result.items():
                    # チェックボックスとの整合性チェックなどを行う
                    final_text = self._post_process_text(field_name, generated_text, patient_data)

                    generated_plan_so_far[field_name] = final_text

                    yield self._create_event("update", {"key": field_name, "value": final_text, "model_type": "general"})

            logger.info("--- Gemini汎用項目の生成完了 ---")
            yield "event: general_finished\ndata: {}\n\n"

        except Exception as e:
            logger.error(f"Gemini API Error: {e}", exc_info=True)
            yield self._create_event("error", {"error": f"AIとの通信中にエラーが発生しました: {str(e)}"})

    def regenerate_plan_item_stream(
        self,
        patient_data: Dict[str, Any],
        item_key: str,
        current_text: str,
        instruction: str,
        rag_executor: Optional[RAGExecutor] = None
    ) -> Generator[str, None, None]:
        """
        指定された単一項目を再生成する。
        """
        try:
            # 1. 患者情報の整形
            patient_facts = prepare_patient_facts(patient_data)
            patient_facts_str = json.dumps(patient_facts, indent=2, ensure_ascii=False)

            # これまでの生成結果（対象項目以外）
            generated_plan_so_far = patient_data.copy()
            if item_key in generated_plan_so_far:
                del generated_plan_so_far[item_key]

            # 2. RAG検索（オプション）
            rag_context_str = None
            if rag_executor:
                logger.info("--- RAG再生成: 専門知識の検索を開始 ---")
                try:
                    rag_result = rag_executor.execute(patient_facts)
                    contexts = rag_result.get("contexts", [])
                    if contexts:
                        rag_context_str = "\n\n".join([ctx.get("content", "") for ctx in contexts])
                        logger.info(f"--- RAG再生成: {len(contexts)}件の専門知識を発見 ---")
                except Exception as e:
                    logger.error(f"RAG execution failed during regeneration: {e}")

            # 3. 動的スキーマ生成 (再生成対象の1項目のみを含むスキーマ)
            RegenerationSchema = create_model(
                f"RegenerationSchema_{item_key}",
                **{item_key: (str, Field(..., description=f"修正指示に基づいて書き直された'{item_key}'の新しい文章。"))},
            )

            # 4. プロンプト構築
            prompt = build_regeneration_prompt(
                patient_facts_str,
                generated_plan_so_far,
                item_key,
                current_text,
                instruction,
                rag_context_str
            )

            logger.info(f"--- Regenerating Item: {item_key} ---")

            generation_config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=RegenerationSchema,
            )

            # 5. API呼び出し
            response = self._call_api_with_retry(prompt, generation_config)

            if not response or not response.parsed:
                raise Exception(f"項目 '{item_key}' の再生成に失敗しました。")

            regenerated_text = response.parsed.model_dump().get(item_key, "")

            # 6. 文字単位でストリーミング風に返す
            if regenerated_text:
                for char in regenerated_text:
                    yield self._create_event("update", {"key": item_key, "chunk": char})

            yield "event: finished\ndata: {}\n\n"

        except Exception as e:
            logger.error(f"Regeneration Error: {e}", exc_info=True)
            yield self._create_event("error", {"error": f"再生成中にエラーが発生しました: {str(e)}"})

    def generate_rag_plan_stream(
        self,
        patient_data: Dict[str, Any],
        rag_executor: RAGExecutor
    ) -> Generator[str, None, None]:
        """
        RAGExecutorを使用して特化モデルによる計画案を生成する。
        注: GeminiClient内ではありますが、rag_executor.execute() が内部でGemini (または設定されたLLM) を呼び出します。
        このメソッドは主に結果の整形とストリーミングを担当します。
        """
        try:
            logger.info("--- RAGモデルによる生成を開始 ---")

            # 1. 患者情報の整形
            patient_facts = prepare_patient_facts(patient_data)

            # 2. RAGExecutorの実行
            # rag_executor.execute は { "answer": {...}, "contexts": [...] } を返す想定
            rag_result = rag_executor.execute(patient_facts)

            specialized_plan_dict = rag_result.get("answer", {})
            contexts = rag_result.get("contexts", [])

            # 3. エラーハンドリング
            if "error" in specialized_plan_dict:
                error_msg = specialized_plan_dict["error"]
                logger.error(f"RAG Executor Error: {error_msg}")
                # RAGが担当する主要な項目に対してエラーを表示
                rag_error_keys = [
                    "main_risks_txt",
                    "main_contraindications_txt",
                    "func_pain_txt",
                    "func_rom_limitation_txt",
                    "func_muscle_weakness_txt",
                    "func_swallowing_disorder_txt",
                    "func_behavioral_psychiatric_disorder_txt",
                    "adl_equipment_and_assistance_details_txt",
                    "goals_1_month_txt",
                    "goals_at_discharge_txt",
                    "policy_treatment_txt",
                    "policy_content_txt",
                    "goal_p_action_plan_txt",
                    "goal_a_action_plan_txt",
                    "goal_s_psychological_action_plan_txt",
                    "goal_s_env_action_plan_txt",
                    "goal_s_3rd_party_action_plan_txt",
                ]

                # 定義したキーを使って、各項目にエラーメッセージを送信する
                for key in rag_error_keys:
                     yield self._create_event("update", {
                         "key": key,
                         "value": f"RAGエラー: {error_msg}",
                         "model_type": "specialized"
                     })
            else:
                # 4. 成功時のストリーミング
                for key, value in specialized_plan_dict.items():
                    yield self._create_event("update", {"key": key, "value": value, "model_type": "specialized"})

                # 5. 根拠情報の送信
                if contexts:
                    contexts_for_frontend = []
                    for i, ctx in enumerate(contexts):
                        metadata = ctx.get("metadata", {})
                        contexts_for_frontend.append({
                            "id": i + 1,
                            "content": ctx.get("content", ""),
                            "source": metadata.get("source", "N/A"),
                            "disease": metadata.get("disease", "N/A"),
                            "section": metadata.get("section", "N/A"),
                            # 必要に応じて他のメタデータも含める
                        })

                    yield f"event: context_update\ndata: {json.dumps(contexts_for_frontend)}\n\n"

            yield "event: finished\ndata: {}\n\n"

        except Exception as e:
            logger.error(f"RAG Stream Error: {e}", exc_info=True)
            # 致命的なエラーの場合
            yield self._create_event("update", {"key": "main_risks_txt", "value": f"RAG実行エラー: {e}", "model_type": "specialized"})
            yield "event: finished\ndata: {}\n\n"

    # 【追加】単発JSON生成メソッド
    def generate_json(self, prompt: str, schema: Type[BaseModel]) -> Dict[str, Any]:
        """
        Geminiを使用してJSONを生成する (同期処理)
        """
        if not client:
             raise RuntimeError("Gemini Client is not initialized.")

        generation_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
        )

        # リトライロジック込みでAPI呼び出し
        response = self._call_api_with_retry(prompt, generation_config)

        if response and response.parsed:
            return response.parsed.model_dump(mode="json")
        elif response and response.text:
            # 万が一SDKのパースが失敗した場合のフォールバック
            try:
                # マークダウンの ```json ... ``` を除去する簡易処理
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.endswith("```"):
                    text = text[:-3]
                return json.loads(text)
            except json.JSONDecodeError:
                pass

        raise ValueError("Gemini failed to generate valid JSON.")

    # --- Helper Methods ---

    def _call_api_with_retry(self, prompt: str, config: types.GenerateContentConfig, max_retries: int = 3):
        """API呼び出しのリトライロジック"""
        if not client:
            raise RuntimeError("Gemini Client is not initialized.")

        backoff_factor = 2
        for attempt in range(max_retries):
            try:
                return client.models.generate_content(
                    model="gemini-2.5-flash-lite",
                    contents=prompt,
                    config=config
                )
            except (ResourceExhausted, ServiceUnavailable) as e:
                if attempt < max_retries - 1:
                    wait_time = backoff_factor * (2**attempt)
                    logger.warning(f"API Error: {e}. Retrying in {wait_time}s... ({attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API call failed after {max_retries} attempts.")
                    raise e
        return None

    def _post_process_text(self, field_name: str, generated_text: str, patient_data: Dict[str, Any]) -> str:
        """
        生成されたテキストの後処理。
        チェックボックスがOFFなのにテキストが生成された場合や、
        ONなのに「特記なし」と生成された場合の補正を行う。
        """
        final_text = generated_text

        # このフィールドが「詳細テキスト」側であるか確認
        # 例: field_name="func_pain_txt" -> chk_key="func_pain_chk"
        if field_name in CHECK_TO_TEXT_MAP.values():
            chk_key = next((chk for chk, txt in CHECK_TO_TEXT_MAP.items() if txt == field_name), None)

            if chk_key:
                is_checked_in_db = patient_data.get(chk_key)
                is_truly_checked = str(is_checked_in_db).lower() in ["true", "1", "on"]

                if not is_truly_checked:
                    # チェックがないなら強制的に「特記なし」
                    final_text = "特記なし"
                elif is_truly_checked and generated_text == "特記なし":
                    # チェックがあるのにAIが「特記なし」と返した場合、
                    # 元データに何か記述があればそれを復元する（安全策）
                    original_text = patient_data.get(field_name)
                    if original_text and original_text != "特記なし":
                        final_text = original_text

        return final_text

    def _create_event(self, event_type: str, data: Dict[str, Any]) -> str:
        """SSEイベント形式の文字列を作成"""
        return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
