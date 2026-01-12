from abc import ABC, abstractmethod
from typing import Any, Dict, Generator, Optional, Type

from pydantic import BaseModel

from app.services.llm.rag_executor import RAGExecutor


class LLMClient(ABC):
    """
    LLMクライアントの抽象基底クラス。
    全ての具体的なLLM実装（GeminiClient, OllamaClientなど）はこのクラスを継承し、
    以下のメソッドを実装する必要があります。
    """

    @abstractmethod
    def generate_plan_stream(self, patient_data: Dict[str, Any]) -> Generator[str, None, None]:
        """
        患者データから計画書を生成し、Server-Sent Events (SSE) 形式の文字列をストリーミングでyieldします。

        Args:
            patient_data: 患者情報の辞書

        Yields:
            str: "event: update\ndata: {...}\n\n" 形式のSSE文字列
        """
        pass

    @abstractmethod
    def regenerate_plan_item_stream(
        self,
        patient_data: Dict[str, Any],
        item_key: str,
        current_text: str,
        instruction: str,
        rag_executor: Optional[RAGExecutor] = None
    ) -> Generator[str, None, None]:
        """
        指定された単一項目を、ユーザーの指示に基づいて再生成し、SSE形式でyieldします。

        Args:
            patient_data: 患者情報の辞書
            item_key: 再生成対象の項目キー（例: 'main_risks_txt'）
            current_text: 現在の（修正前の）テキスト
            instruction: ユーザーからの修正指示
            rag_executor: 専門知識検索用のRAGExecutor（任意）

        Yields:
            str: SSE形式の文字列（文字単位のチャンクなど）
        """
        pass

    @abstractmethod
    def generate_rag_plan_stream(
        self,
        patient_data: Dict[str, Any],
        rag_executor: RAGExecutor
    ) -> Generator[str, None, None]:
        """
        RAGExecutorを使用して、専門知識に基づいた計画書を生成し、SSE形式でyieldします。
        このメソッドは、LLMがRAGExecutorの結果を受け取り、整形してクライアントに返す役割を担います。

        Args:
            patient_data: 患者情報の辞書
            rag_executor: 実行するRAGExecutorインスタンス

        Yields:
            str: SSE形式の文字列
        """
        pass

    @abstractmethod
    def generate_json(self, prompt: str, schema: Type[BaseModel]) -> Dict[str, Any]:
        """
        プロンプトに基づいて構造化データ(JSON)を生成し、辞書として返す（ストリーミングなし）。
        PatientInfoParserなどの解析処理で使用。
        """
        pass
