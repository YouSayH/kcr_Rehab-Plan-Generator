import json
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel, Field

from app.services.llm.context_builder import prepare_patient_facts

# テスト対象のモジュール
from app.services.llm.gemini import GeminiClient
from app.services.llm.ollama import OllamaClient
from app.services.llm.prompts import build_group_prompt


# テスト用のダミースキーマ
class MockSchema(BaseModel):
    summary: str = Field(..., description="概要")
    score: int = Field(..., description="スコア")

@pytest.fixture
def mock_patient_data():
    return {
        "name": "テスト患者",
        "age": 80,
        "gender": "女性",
        "therapist_notes": "特記事項あり",
        "func_pain_chk": True,
        "func_pain_txt": "腰痛あり"
    }

# --- 1. Geminiクライアントの詳細テスト ---

@patch("app.services.llm.gemini.client")
def test_gemini_api_call_structure(mock_genai_client, mock_patient_data):
    """
    [Gemini] API呼び出し時の設定(Config)と渡すプロンプトが正しいか検証
    """
    client = GeminiClient()

    # モックの応答設定
    mock_response = MagicMock()
    mock_response.parsed.model_dump.return_value = {"summary": "OK", "score": 10}
    mock_genai_client.models.generate_content.return_value = mock_response

    # テスト実行 (generate_json)
    prompt_text = "テスト用プロンプト"
    client.generate_json(prompt_text, MockSchema)

    # 検証: generate_content が正しい引数で呼ばれたか
    args, kwargs = mock_genai_client.models.generate_content.call_args

    # モデル名の確認
    assert kwargs["model"] == "gemini-2.5-flash-lite"

    # プロンプトの内容確認
    assert kwargs["contents"] == prompt_text

    # Configの確認 (JSONモードとスキーマ)
    config = kwargs["config"]
    assert config.response_mime_type == "application/json"
    assert config.response_schema == MockSchema

@patch("app.services.llm.gemini.client")
def test_gemini_retry_logic(mock_genai_client):
    """
    [Gemini] エラー時のリトライロジックが機能しているか検証
    """
    from google.api_core.exceptions import ResourceExhausted

    client = GeminiClient()

    # 1回目と2回目はエラー、3回目で成功するようにサイドエフェクトを設定
    mock_response = MagicMock()
    mock_response.parsed.model_dump.return_value = {"summary": "Retry OK", "score": 10}

    mock_genai_client.models.generate_content.side_effect = [
        ResourceExhausted("Quota exceeded"), # 1回目
        ResourceExhausted("Quota exceeded"), # 2回目
        mock_response                        # 3回目 (成功)
    ]

    # 時間待ちを短縮するためにtime.sleepをモック
    with patch("time.sleep") as mock_sleep:
        client.generate_json("prompt", MockSchema)

        # 3回呼ばれたか確認
        assert mock_genai_client.models.generate_content.call_count == 3
        # sleepが呼ばれたか確認 (バックオフの検証)
        assert mock_sleep.call_count == 2

# --- 2. Ollamaクライアントの詳細テスト ---

@patch("app.services.llm.ollama.ollama.chat")
def test_ollama_api_parameters(mock_ollama_chat):
    """
    [Ollama] API呼び出し時のパラメータ(options, format)が正しいか検証
    """
    client = OllamaClient()

    # モックの応答
    mock_ollama_chat.return_value = {
        "message": {"content": json.dumps({"summary": "Local OK", "score": 5})}
    }

    # テスト実行
    prompt_text = "Ollamaテスト"

    # 環境変数を操作してJSONモードをONにするケース
    with patch("app.services.llm.ollama.OLLAMA_USE_STRUCTURED_OUTPUT", True):
        client.generate_json(prompt_text, MockSchema)

        args, kwargs = mock_ollama_chat.call_args

        # モデル名 (デフォルト値または環境変数)
        assert "model" in kwargs

        # フォーマット指定
        assert kwargs["format"] == "json"

        # オプション設定 (temperatureなど)
        assert "options" in kwargs
        assert kwargs["options"]["temperature"] == 0.2
        assert kwargs["options"]["num_ctx"] == 8192

        # プロンプト
        assert kwargs["messages"][0]["content"] == prompt_text

@patch("app.services.llm.ollama.ollama.chat")
def test_ollama_response_parsing(mock_ollama_chat):
    """
    [Ollama] 返されたJSONのパース処理（思考タグの除去など）を検証
    """
    client = OllamaClient()

    # DeepSeek R1などの思考タグ(<think>...</think>)が含まれるケース
    raw_response = """
    <think>
    ユーザーは要約を求めている...
    </think>
    ```json
    {
        "summary": "思考タグ除去テスト",
        "score": 100
    }
    ```
    """
    mock_ollama_chat.return_value = {"message": {"content": raw_response}}

    # テスト実行
    result = client.generate_json("prompt", MockSchema)

    # 検証
    assert result["summary"] == "思考タグ除去テスト"
    assert result["score"] == 100

# --- 3. プロンプト内容の整合性テスト ---

def test_prompt_content_integrity(mock_patient_data):
    """
    [共通] プロンプトに必要な情報がすべて含まれているか詳細に検証
    """
    facts = prepare_patient_facts(mock_patient_data)
    facts_str = json.dumps(facts, indent=2, ensure_ascii=False)

    # Gemini向けプロンプト
    prompt_gemini = build_group_prompt(MockSchema, facts_str, {}, is_ollama=False)

    # 必須要素のチェック
    assert "役割" in prompt_gemini
    assert "リハビリテーション科の専門医" in prompt_gemini
    assert "FIM（機能的自立度評価法）" in prompt_gemini # ガイドライン
    assert "腰痛あり" in prompt_gemini # 患者情報
    assert "特記なし" in prompt_gemini # デフォルト指示

    # Ollama向けプロンプト (サフィックスが付くか)
    prompt_ollama = build_group_prompt(MockSchema, facts_str, {}, is_ollama=True)
    assert "生成するJSON" in prompt_ollama # Ollama用の誘導

# --- 4. 環境変数と設定のテスト ---

def test_gemini_client_initialization_config():
    """
    [Gemini] 環境変数が無い場合の挙動などを検証
    """
    # モジュールレベルのclient変数をモックしてNoneにする
    with patch("app.services.llm.gemini.client", None):
        client = GeminiClient()
        # クライアントがNoneの状態でメソッドを呼ぶとエラーになるか
        with pytest.raises(RuntimeError) as excinfo:
            client.generate_json("test", MockSchema)
        assert "not initialized" in str(excinfo.value)
