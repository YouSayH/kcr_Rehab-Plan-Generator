import json
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel, Field

# アプリケーションのモジュールをインポート
from app.services.llm.context_builder import prepare_patient_facts
from app.services.llm.gemini import GeminiClient
from app.services.llm.ollama import OllamaClient
from app.services.llm.base import LLMClient
from app.services.llm.prompts import build_group_prompt
from app.services.llm.rag_executor import RAGExecutor

# --- ダミーデータとスキーマの定義 ---

# Pytestにテストクラスとして収集されないよう名前を変更 (Test... -> SchemaForTest)
class SchemaForTest(BaseModel):
    """テスト用のシンプルなPydanticスキーマ"""
    summary: str = Field(..., description="患者の概要")
    risk_level: int = Field(..., description="リスクレベル(1-5)")

@pytest.fixture
def sample_patient_data():
    """DBから取得したと仮定する患者データのダミー"""
    return {
        "name": "テスト 太郎",
        "age": 75,
        "gender": "男性",
        "header_disease_name_txt": "脳梗塞",
        "therapist_notes": "意欲的だが転倒リスクあり。",
        # チェックボックスとテキストのペア (ロジック確認用)
        "func_pain_chk": True,
        "func_pain_txt": "右肩に軽度の疼痛あり",
        "func_swallowing_disorder_chk": False, # チェックなし
        "func_swallowing_disorder_txt": "特記なし",
        # チェックありだがテキストなし (推論ロジック確認用)
        "func_rom_limitation_chk": True,
        "func_rom_limitation_txt": "特記なし",
    }

@pytest.fixture
def mock_rag_executor():
    """RAGExecutorのモック"""
    executor = MagicMock(spec=RAGExecutor)
    # RAGが返すダミー結果
    executor.execute.return_value = {
        "answer": {"main_risks_txt": "転倒リスクが高いです。"},
        "contexts": [
            {"content": "転倒予防ガイドライン...", "metadata": {"source": "ガイドライン2024"}},
            {"content": "脳梗塞のリハビリ...", "metadata": {"source": "文献A"}}
        ]
    }
    return executor

# --- 1. データ整形・情報共有のテスト (Context Builder) ---

def test_context_builder_formatting(sample_patient_data):
    """
    [判定項目]:
    - DBの内容(sample_patient_data)を持ってこれているか
    - ユーザーの入力(therapist_notes)を持ってこれているか
    - チェックボックスのロジック(ON/OFF)が正しく反映されているか
    """
    facts = prepare_patient_facts(sample_patient_data)

    # 基本情報の確認
    assert facts["基本情報"]["性別"] == "男性"
    assert facts["基本情報"]["算定病名"] == "脳梗塞"

    # ユーザー入力(所見)が含まれているか
    assert facts["担当者からの所見"] == "意欲的だが転倒リスクあり。"

    # チェックボックスロジックの確認
    # 1. チェックON + テキストあり -> テキストが採用される
    assert facts["心身機能・構造"]["疼痛"] == "右肩に軽度の疼痛あり"

    # 2. チェックOFF -> 項目自体が含まれない (過不足ない情報共有)
    assert "摂食嚥下障害" not in facts["心身機能・構造"]

    # 3. チェックON + テキストなし -> AIへの推論指示が入る
    assert "推測して記述してください" in facts["心身機能・構造"]["関節可動域制限"]

# --- 2. プロンプト構築のテスト ---

def test_prompt_construction(sample_patient_data):
    """
    [判定項目]:
    - LLMに共有する情報に過不足ないか
    - 指定したスキーマ(JSON構造)をLLMに指示できているか
    """
    facts = prepare_patient_facts(sample_patient_data)
    facts_str = json.dumps(facts, indent=2, ensure_ascii=False)

    prompt = build_group_prompt(SchemaForTest, facts_str, {}, is_ollama=False)

    # 必須要素が含まれているか確認
    assert "脳梗塞" in prompt # 患者情報
    assert "意欲的だが転倒リスクあり" in prompt # 所見
    assert "properties" in prompt # JSONスキーマ定義
    assert "risk_level" in prompt # スキーマのフィールド

# --- 3. LLMクライアント(Gemini)の動作テスト ---

@patch("app.services.llm.gemini.client") # google.genai.Clientをモック
def test_gemini_generate_json(mock_genai_client):
    """
    [判定項目]:
    - Geminiが正しく呼び出されているか
    - 制限付きデコーディング(schema)に対応できているか
    - 生成結果を指定したスキーマでパースできているか
    """
    client = GeminiClient()

    # LLMからの応答をモック
    mock_response = MagicMock()
    # model_dump(mode="json") が呼ばれる想定
    mock_response.parsed.model_dump.return_value = {"summary": "テスト結果", "risk_level": 3}
    mock_genai_client.models.generate_content.return_value = mock_response

    # 実行
    result = client.generate_json("prompt", SchemaForTest)

    # 検証
    assert result["summary"] == "テスト結果"
    assert result["risk_level"] == 3

    # スキーマが渡されているか確認 (制限付きデコーディング)
    args, kwargs = mock_genai_client.models.generate_content.call_args
    assert kwargs["config"].response_schema == SchemaForTest

@patch("app.services.llm.gemini.client")
def test_gemini_streaming_flow(mock_genai_client, sample_patient_data):
    """
    [判定項目]:
    - 生成結果をアプリに返せるか(ストリーミング形式)
    - 変えられた情報(DBの値 vs 生成値)を表示できているか
    """
    client = GeminiClient()

    # ストリーミング生成のモック (GENERATION_GROUPSのループ内で呼ばれる)
    mock_response = MagicMock()
    # ダミーの生成結果 (Pydanticモデルのダンプを想定)
    mock_response.parsed.model_dump.return_value = {
        "header_disease_name_txt": "生成された病名"
    }
    mock_genai_client.models.generate_content.return_value = mock_response

    # ジェネレータを実行
    stream = client.generate_plan_stream(sample_patient_data)
    events = list(stream)

    # SSE形式 ("event: update\ndata: ...") になっているか確認
    assert len(events) > 0
    first_event = events[0]
    assert "event: update" in first_event

    # データの中身を確認
    data_line = first_event.split("\n")[1]
    json_data = json.loads(data_line.replace("data: ", ""))

    # キーと値が含まれているか
    assert "key" in json_data
    assert "value" in json_data

# --- 4. RAG連携のテスト ---

def test_rag_integration_flow(mock_rag_executor):
    """
    [判定項目]:
    - RAGは動いているか (Executorが呼ばれるか)
    - RAGの参照情報をアプリに返せているか (context_updateイベント)
    - 生成結果をアプリに返せるか
    """
    # GeminiClientを使ってテスト (ロジックは共通部分が多い)
    client = GeminiClient()

    # 実行
    stream = client.generate_rag_plan_stream({"name": "test"}, mock_rag_executor)
    events = list(stream)

    # RAG Executorが呼ばれたか
    mock_rag_executor.execute.assert_called_once()

    # イベントの検証
    has_update = False
    has_context = False

    for event in events:
        if "event: update" in event:
            has_update = True
            # JSONをパースして中身を確認
            data_line = event.split("\n")[1].replace("data: ", "")
            data = json.loads(data_line)
            # 生成テキストが含まれているか
            assert "転倒リスクが高いです" in data["value"]

        if "event: context_update" in event:
            has_context = True
            # JSONをパースして中身を確認 (これでエスケープ文字の問題を回避)
            data_line = event.split("\n")[1].replace("data: ", "")
            context_list = json.loads(data_line)

            # リスト内の辞書からsourceを抽出
            sources = [ctx["source"] for ctx in context_list]
            assert "ガイドライン2024" in sources

    assert has_update, "LLMの生成結果がストリームされていません"
    assert has_context, "RAGの参照情報がストリームされていません"

# --- 5. Ollamaクライアントのテスト (JSONモード) ---

@patch("app.services.llm.ollama.ollama.chat")
def test_ollama_json_mode(mock_ollama_chat):
    """
    [判定項目]:
    - Ollama呼び出し時に 'format="json"' (制限付きデコーディング相当) が指定されているか
    """
    client = OllamaClient()

    # モック設定
    mock_ollama_chat.return_value = {
        "message": {"content": json.dumps({"summary": "Ollama結果", "risk_level": 1})}
    }

    # 環境変数を一時的にセットしてJSONモード有効化をシミュレート
    with patch("app.services.llm.ollama.OLLAMA_USE_STRUCTURED_OUTPUT", True):
        client.generate_json("prompt", SchemaForTest)

        # 呼び出し引数の確認
        args, kwargs = mock_ollama_chat.call_args
        assert kwargs["format"] == "json"  # JSONモードが有効になっているか

# --- 全体のまとめテスト ---

def test_full_component_integration():
    """
    [判定項目]:
    - ファクトリからクライアントを取得し、メソッドを呼び出せるか
    """
    from app.services.llm import get_llm_client

    # デフォルト(Gemini)が返るか
    client = get_llm_client()
    assert isinstance(client, (GeminiClient, OllamaClient))

    # メソッドが存在するか
    assert hasattr(client, "generate_plan_stream")
    assert hasattr(client, "generate_json")
    assert hasattr(client, "generate_rag_plan_stream")
