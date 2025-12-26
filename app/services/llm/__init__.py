import logging
import os

from dotenv import load_dotenv

from app.services.llm.base import LLMClient

load_dotenv()
logger = logging.getLogger(__name__)

def get_llm_client() -> LLMClient:
    """
    環境変数 LLM_CLIENT_TYPE に基づいて適切なLLMクライアントインスタンスを返すファクトリ関数。

    Returns:
        LLMClient: GeminiClient または OllamaClient のインスタンス
    """
    # デフォルトは gemini とする
    client_type = os.getenv("LLM_CLIENT_TYPE", "gemini").lower()

    logger.info(f"Initializing LLM Client type: {client_type}")

    if client_type == "ollama":
        from app.services.llm.ollama import OllamaClient
        return OllamaClient()
    else:
        # gemini またはその他の値の場合
        from app.services.llm.gemini import GeminiClient
        return GeminiClient()
