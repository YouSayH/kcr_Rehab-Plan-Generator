import json
import logging
import os
import re
import time
from typing import Any, Dict, Generator, Optional, Type

import ollama
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, create_model

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

# --- 設定 ---
OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "qwen3:8b")
# 構造的出力（JSONモード）を使用するかどうかのフラグ
OLLAMA_USE_STRUCTURED_OUTPUT = os.getenv("OLLAMA_USE_STRUCTURED_OUTPUT", "true").lower() == "true"
GENERATION_TIMEOUT_SEC = 60
USE_DUMMY_DATA = False


class OllamaClient(LLMClient):
    """
    Ollamaを使用したLLMクライアントの実装
    """

    def generate_plan_stream(self, patient_data: Dict[str, Any]) -> Generator[str, None, None]:
        if USE_DUMMY_DATA:
             yield self._create_event("error", {"error": "ダミーデータモードは現在サポートされていません。"})
             return

        try:
            # 1. 患者情報の整形
            patient_facts = prepare_patient_facts(patient_data)
            patient_facts_str = json.dumps(patient_facts, indent=2, ensure_ascii=False, default=str)
            generated_plan_so_far = {}

            # ユーザー入力済み項目の処理
            for field_name in USER_INPUT_FIELDS:
                if patient_data.get(field_name):
                    value = patient_data[field_name]
                    generated_plan_so_far[field_name] = value
                    yield self._create_event("update", {"key": field_name, "value": value, "model_type": "ollama_general"})

            max_retries = 10

            # 2. グループごとに生成
            for group_schema in GENERATION_GROUPS:
                logger.info(f"--- Ollama Generating Group: {group_schema.__name__} ---")

                # プロンプト構築 (Ollama用フラグON)
                prompt = build_group_prompt(
                    group_schema,
                    patient_facts_str,
                    generated_plan_so_far,
                    is_ollama=True
                )

                # JSONモードの設定
                format_param = "json" if OLLAMA_USE_STRUCTURED_OUTPUT else None
                if not OLLAMA_USE_STRUCTURED_OUTPUT:
                    prompt += "\n\nEnsure the output is a valid JSON object."

                # リトライループ
                for attempt in range(max_retries):
                    try:
                        logger.info(f"--- Group: {group_schema.__name__} (Attempt: {attempt+1}/{max_retries}) ---")

                        start_time = time.time()

                        # API呼び出し (ストリーミング)
                        stream = ollama.chat(
                            model=OLLAMA_MODEL_NAME,
                            messages=[{"role": "user", "content": prompt}],
                            format=format_param,
                            stream=True
                        )

                        accumulated_json_string = ""
                        for chunk in stream:
                            if time.time() - start_time > GENERATION_TIMEOUT_SEC:
                                raise TimeoutError(f"Generation exceeded {GENERATION_TIMEOUT_SEC} seconds.")
                            if chunk["message"]["content"]:
                                accumulated_json_string += chunk["message"]["content"]

                        logger.debug(f"Ollama Raw Response:\n{accumulated_json_string}")

                        # JSON抽出とパース
                        raw_response_dict = {}
                        if OLLAMA_USE_STRUCTURED_OUTPUT:
                            try:
                                raw_response_dict = json.loads(accumulated_json_string)
                            except json.JSONDecodeError:
                                # 構造化モードでも失敗する場合があるため、フォールバックとして抽出関数を試す
                                raw_response_dict = self._extract_and_parse_json(accumulated_json_string)
                        else:
                            raw_response_dict = self._extract_and_parse_json(accumulated_json_string)

                        # ネスト構造の解決とバリデーション
                        data_to_validate = self._resolve_nested_json(raw_response_dict, group_schema)

                        # Pydantic検証
                        group_result_obj = group_schema.model_validate(data_to_validate)
                        group_result_dict = group_result_obj.model_dump()

                        # 成功時: 結果を反映してストリーミング
                        for field_name, generated_text in group_result_dict.items():
                            final_text = self._post_process_text(field_name, generated_text, patient_data)
                            generated_plan_so_far[field_name] = final_text
                            yield self._create_event("update", {"key": field_name, "value": final_text, "model_type": "ollama_general"})

                        break  # 成功したらリトライループを抜ける

                    except (ValidationError, json.JSONDecodeError, ValueError, TimeoutError) as e:
                        logger.warning(f"Ollama generation failed (Attempt {attempt+1}): {e}")
                        if attempt == max_retries - 1:
                            logger.error(f"Group {group_schema.__name__} failed after max retries.")
                            yield self._create_event("error", {"error": f"グループ {group_schema.__name__} の生成に失敗しました: {str(e)}"})
                        else:
                            time.sleep(1)

            yield "event: general_finished\ndata: {}\n\n"

        except Exception as e:
            logger.error(f"Ollama API Error: {e}", exc_info=True)
            yield self._create_event("error", {"error": f"Ollama処理全体でエラーが発生しました: {str(e)}"})

    def regenerate_plan_item_stream(
        self,
        patient_data: Dict[str, Any],
        item_key: str,
        current_text: str,
        instruction: str,
        rag_executor: Optional[RAGExecutor] = None
    ) -> Generator[str, None, None]:

        try:
            patient_facts = prepare_patient_facts(patient_data)
            patient_facts_str = json.dumps(patient_facts, indent=2, ensure_ascii=False, default=str)

            generated_plan_so_far = patient_data.copy()
            if item_key in generated_plan_so_far:
                del generated_plan_so_far[item_key]

            # RAG検索
            rag_context_str = None
            if rag_executor:
                try:
                    rag_result = rag_executor.execute(patient_facts)
                    contexts = rag_result.get("contexts", [])
                    if contexts:
                        rag_context_str = "\n\n".join([ctx.get("content", str(ctx)) for ctx in contexts])
                        logger.info(f"--- RAG再生成: {len(contexts)}件の専門知識を発見 ---")
                except Exception as e:
                    logger.error(f"RAGExecutor error during regeneration: {e}")

            # 動的スキーマ生成
            RegenerationSchema = create_model(
                f"RegenerationSchema_{item_key}",
                **{item_key: (str, Field(..., description=f"修正指示に基づいて書き直された'{item_key}'の新しい文章。"))},
            )

            # プロンプト構築
            prompt = build_regeneration_prompt(
                patient_facts_str,
                generated_plan_so_far,
                item_key,
                current_text,
                instruction,
                rag_context_str,
                schema=RegenerationSchema # Ollamaの場合はスキーマも渡す
            )

            format_param = "json" if OLLAMA_USE_STRUCTURED_OUTPUT else None
            if not OLLAMA_USE_STRUCTURED_OUTPUT:
                prompt += "\n\nEnsure the output is a valid JSON object."

            regenerated_text = ""
            max_retries = 5

            for attempt in range(max_retries):
                try:
                    logger.info(f"--- Regenerating Item: {item_key} (Attempt: {attempt+1}) ---")

                    stream = ollama.chat(
                        model=OLLAMA_MODEL_NAME,
                        messages=[{"role": "user", "content": prompt}],
                        format=format_param,
                        stream=True
                    )

                    accumulated_json_string = ""
                    for chunk in stream:
                        if chunk["message"]["content"]:
                            accumulated_json_string += chunk["message"]["content"]

                    # パースと検証
                    json_data_raw = {}
                    if OLLAMA_USE_STRUCTURED_OUTPUT:
                        try:
                            json_data_raw = json.loads(accumulated_json_string)
                        except json.JSONDecodeError:
                            json_data_raw = self._extract_and_parse_json(accumulated_json_string)
                    else:
                        json_data_raw = self._extract_and_parse_json(accumulated_json_string)

                    # ネスト解決（簡易版）
                    data_to_validate = json_data_raw
                    if isinstance(json_data_raw, dict):
                        if "properties" in json_data_raw and item_key in json_data_raw["properties"]:
                             data_to_validate = json_data_raw["properties"]
                        elif item_key in json_data_raw:
                             data_to_validate = json_data_raw

                    validated_data = RegenerationSchema.model_validate(data_to_validate)
                    regenerated_text = validated_data.model_dump().get(item_key, "")
                    break

                except Exception as e:
                    logger.warning(f"Regeneration failed (Attempt {attempt+1}): {e}")
                    if attempt == max_retries - 1:
                        raise e
                    time.sleep(1)

            # 結果をストリーミング
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

        try:
            logger.info("--- Ollama RAGモデルによる生成を開始 ---")
            patient_facts = prepare_patient_facts(patient_data)

            # RAGExecutor実行 (内部でOllama LLMを呼ぶ)
            rag_result = rag_executor.execute(patient_facts)

            specialized_plan_dict = rag_result.get("answer", {})
            contexts = rag_result.get("contexts", [])

            if "error" in specialized_plan_dict:
                error_msg = specialized_plan_dict["error"]
                logger.error(f"RAG Executor Error: {error_msg}")

                # エラーメッセージを対象となる全項目に通知 (Gemini版と同様の修正)
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
                for key in rag_error_keys:
                    yield self._create_event("update", {
                        "key": key,
                        "value": f"RAGエラー: {error_msg}",
                        "model_type": "ollama_specialized"
                    })
            else:
                for key, value in specialized_plan_dict.items():
                    yield self._create_event("update", {"key": key, "value": str(value), "model_type": "ollama_specialized"})

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
                        })
                    yield f"event: context_update\ndata: {json.dumps(contexts_for_frontend)}\n\n"

            yield "event: finished\ndata: {}\n\n"

        except Exception as e:
            logger.error(f"Ollama RAG Stream Error: {e}", exc_info=True)
            yield self._create_event("error", {"error": f"RAG実行中にエラーが発生しました: {str(e)}"})

    # 【追加】単発JSON生成メソッド (PatientInfoParser用)
    def generate_json(self, prompt: str, schema: Type[BaseModel]) -> Dict[str, Any]:
        """
        Ollamaを使用してJSONを生成する（同期処理）
        """
        format_param = "json" if OLLAMA_USE_STRUCTURED_OUTPUT else None

        # 呼び出し (ストリーミングなし)
        # optionsでtemperature等を調整
        response = ollama.chat(
            model=OLLAMA_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            format=format_param,
            stream=False,
            options={"temperature": 0.2, "num_ctx": 8192}
        )

        raw_json_str = response["message"]["content"]

        try:
            if OLLAMA_USE_STRUCTURED_OUTPUT:
                try:
                    json_data = json.loads(raw_json_str)
                except json.JSONDecodeError:
                    # 失敗したら抽出ロジックへ
                    json_data = self._extract_and_parse_json(raw_json_str)
            else:
                json_data = self._extract_and_parse_json(raw_json_str)

            # ネスト解決
            json_data = self._resolve_nested_json(json_data, schema)

            # バリデーション
            validated_obj = schema.model_validate(json_data)
            return validated_obj.model_dump(mode="json")

        except Exception as e:
            logger.error(f"Ollama JSON generation failed: {e}\nRaw: {raw_json_str}")
            # エラー時も呼び出し元で再試行させるため例外を投げる
            raise ValueError(f"Ollama failed to generate valid JSON: {e}")

    # --- Helper Methods ---

    def _extract_and_parse_json(self, text: str) -> dict:
        """
        LLMの出力テキストからJSON部分を抽出してパースする。
        CoT（<think>タグ）やMarkdownコードブロックに対応。
        """
        # 1. <think>タグの除去
        text_cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

        # 2. Markdownコードブロック ```json ... ``` の抽出
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', text_cleaned, re.DOTALL)
        if not json_match:
            json_match = re.search(r'```\s*(\{.*?\})\s*```', text_cleaned, re.DOTALL)

        if json_match:
            json_str = json_match.group(1)
        else:
            # 3. {} の抽出を試みる
            start = text_cleaned.find('{')
            end = text_cleaned.rfind('}')
            if start != -1 and end != -1 and end > start:
                json_str = text_cleaned[start : end + 1]
            else:
                json_str = text_cleaned

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON extraction failed: {e}. Target: {json_str[:50]}...")

    def _resolve_nested_json(self, raw_data: Dict[str, Any], schema: Type[BaseModel]) -> Dict[str, Any]:
        """
        Ollamaが返すJSONのネスト構造（ルート直下か、schema名キーの下か、properties下かなど）を解決する。
        """
        if not isinstance(raw_data, dict):
            return raw_data

        schema_fields = set(schema.model_fields.keys())
        response_keys = set(raw_data.keys())

        # 1. 必要なフィールドがルートに含まれていればそのまま
        if schema_fields.issubset(response_keys):
            return raw_data

        # 2. スキーマ名でのネスト (ex. {"rehabplanschema": {...}})
        schema_name_key = schema.__name__.lower()
        if schema_name_key in raw_data and isinstance(raw_data[schema_name_key], dict):
            return raw_data[schema_name_key]

        # 3. 一般的なネストキー (ex. {"properties": {...}})
        for key in ["properties", "attributes", "data"]:
            if key in raw_data and isinstance(raw_data[key], dict):
                return raw_data[key]

        return raw_data

    def _post_process_text(self, field_name: str, generated_text: str, patient_data: Dict[str, Any]) -> str:
        """特記なしの復元処理など"""
        final_text = generated_text
        if field_name in CHECK_TO_TEXT_MAP.values():
            chk_key = next((c for c, t in CHECK_TO_TEXT_MAP.items() if t == field_name), None)
            if chk_key:
                is_checked = str(patient_data.get(chk_key)).lower() in ["true", "1", "on"]
                if not is_checked:
                    final_text = "特記なし"
                elif generated_text == "特記なし":
                    orig = patient_data.get(field_name)
                    if orig and orig != "特記なし":
                        final_text = orig
        return final_text

    def _create_event(self, event_type: str, data: Dict[str, Any]) -> str:
        return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
