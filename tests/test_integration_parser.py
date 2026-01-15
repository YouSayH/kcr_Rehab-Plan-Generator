import pytest
from unittest.mock import MagicMock, patch
import json
from app.services.llm.patient_info_parser import PatientInfoParser

# テスト用のダミー入力テキスト
SAMPLE_TEXT = """
右片麻痺あり。食事は自立。
"""

@pytest.fixture
def mock_llm_client():
    """LLMクライアントのモックを作成"""
    mock = MagicMock()
    
    # 1. 標準化(generate_text)のモック
    mock.generate_text.return_value = "- 右片麻痺あり\n- 食事は自立"
    
    # 2. 詳細抽出(generate_json)のモック
    # ExtractionフェーズとPlanフェーズで異なる辞書を返すように設定
    def side_effect(prompt, schema):
        schema_str = str(schema)
        if "HybridCombined_Extraction" in schema_str:
            return {
                "func_basic_rolling_level": "independent",
                "adl_eating_fim_current_val": 7,
                "main_comorbidities_txt": "特になし"
            }
        elif "HybridCombined_Plan" in schema_str:
            return {
                "goals_at_discharge_txt": "自宅退院",
                "policy_treatment_txt": "ADL訓練"
            }
        return {}
    
    mock.generate_json.side_effect = side_effect
    return mock

@patch('app.services.llm.patient_info_parser.get_llm_client')
@patch('app.services.llm.patient_info_parser.FastExtractor')
def test_parser_hybrid_integration(MockFastExtractor, mock_get_llm, mock_llm_client):
    """
    PatientInfoParserのハイブリッドモード統合テスト
    (LLMはモック、ロジックの連携を確認)
    """
    # モックの注入
    mock_get_llm.return_value = mock_llm_client
    
    # FastExtractorのモック (extract_factsが呼ばれたら特定の辞書を返す)
    mock_extractor_instance = MockFastExtractor.return_value
    mock_extractor_instance.extract_facts.return_value = {
        "func_motor_paralysis_chk": True
    }

    # パーサー初期化
    parser = PatientInfoParser(use_hybrid_mode=True)
    
    # 実行
    result = parser.parse_text(SAMPLE_TEXT)

    # --- 検証 ---
    
    # 1. 標準化が呼ばれたか
    mock_llm_client.generate_text.assert_called_once()
    
    # 2. 正規表現抽出が「標準化されたテキスト込み」で呼ばれたか
    args, _ = mock_extractor_instance.extract_facts.call_args
    assert "[AI補完情報]" in args[0]
    
    # 3. LLM抽出が2回（Extraction, Plan）呼ばれたか
    assert mock_llm_client.generate_json.call_count == 2
    
    # 4. 結果の結合確認
    # Regexの結果
    assert result['func_motor_paralysis_chk'] is True
    # LLM(Extraction)の結果
    assert result['adl_eating_fim_current_val'] == 7
    # LLM(Plan)の結果
    assert result['goals_at_discharge_txt'] == "自宅退院"
    
    # 5. チェックボックス復元ロジックの確認 (rolling_level='independent' -> rolling_chk=True)
    assert result.get('func_basic_rolling_chk') is True