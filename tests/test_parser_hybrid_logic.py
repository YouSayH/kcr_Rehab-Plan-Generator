import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import unittest
from unittest.mock import MagicMock, patch
import json
from app.services.llm.patient_info_parser import PatientInfoParser
from app.schemas.schemas import HybridCombined_Extraction, HybridCombined_Plan

class TestPatientInfoParserHybrid(unittest.TestCase):
    
    @patch('app.services.llm.patient_info_parser.get_llm_client')
    @patch('app.services.llm.patient_info_parser.FastExtractor')
    def test_parse_text_hybrid_flow(self, MockFastExtractor, mock_get_llm_client):
        """
        ハイブリッドモード(統合スキーマ使用)のフロー検証
        1. 標準化(generate_text)が呼ばれるか
        2. FastExtractorが呼ばれるか
        3. LLMが統合スキーマで2回(Extraction, Plan)呼ばれるか
        4. コンテキストが引き継がれているか
        """
        print("\n=== テスト開始: ハイブリッドモード抽出フロー ===")

        # --- 1. モックの設定 ---
        
        # LLMクライアントのモック
        mock_llm = MagicMock()
        mock_get_llm_client.return_value = mock_llm
        
        # generate_text (標準化) の戻り値設定
        mock_llm.generate_text.return_value = "- 標準化されたテキスト: 麻痺あり"
        
        # generate_json (抽出・計画) の戻り値設定
        # 1回目 (Extraction) と 2回目 (Plan) で異なる値を返すように設定
        extraction_result = {
            "func_basic_rolling_level": "independent",
            "adl_eating_fim_current_val": 7,
            "main_comorbidities_txt": "高血圧症"
        }
        plan_result = {
            "goals_at_discharge_txt": "自宅復帰",
            "policy_treatment_txt": "歩行訓練強化"
        }
        
        def generate_json_side_effect(prompt, schema):
            # スキーマに応じたレスポンスを返す
            if "HybridCombined_Extraction" in str(schema):
                print(f"  [Mock LLM] Extractionスキーマのリクエストを受信")
                return extraction_result
            elif "HybridCombined_Plan" in str(schema):
                print(f"  [Mock LLM] Planスキーマのリクエストを受信")
                return plan_result
            return {}
        
        mock_llm.generate_json.side_effect = generate_json_side_effect

        # FastExtractorのモック
        mock_extractor_instance = MockFastExtractor.return_value
        mock_extractor_instance.extract_facts.return_value = {
            "func_pain_chk": True,
            "func_motor_paralysis_chk": True
        }

        # --- 2. テスト実行 ---
        
        # パーサーの初期化 (ハイブリッドモード有効)
        parser = PatientInfoParser(use_hybrid_mode=True)
        # モックが注入されたか確認 (インスタンス変数を強制上書きも可能だが、今回はコンストラクタで呼ばれるget_llm_clientをパッチしている)
        
        input_text = "患者は右片麻痺あり。痛みあり。寝返りは自立。"
        result = parser.parse_text(input_text)

        # --- 3. 検証 (Assert) ---

        print("\n=== 検証結果 ===")

        # A. 標準化 (generate_text) が呼ばれたか
        mock_llm.generate_text.assert_called_once()
        print("✅ 標準化メソッド (generate_text) が呼び出されました。")

        # B. FastExtractor が呼ばれたか
        # 呼ばれた際の引数に「標準化テキスト」が含まれているか確認
        args, _ = mock_extractor_instance.extract_facts.call_args
        self.assertIn("[AI補完情報]", args[0])
        print("✅ FastExtractor が標準化テキスト込みで呼び出されました。")

        # C. generate_json が正しい回数（実質2回）呼ばれたか
        # 並列実行のため呼び出し順序は保証されないが、回数と引数を確認
        # Combined Extraction と Combined Plan の2回 + スキーマ定義数によっては変動するが、
        # 今回の実装では `HYBRID_COMBINED_GROUPS` の要素数分 (2回) バッチが回るはず。
        # ただし、Batch1完了後にBatch2が走るため、合計2回呼ばれるはず。
        self.assertEqual(mock_llm.generate_json.call_count, 2)
        print("✅ LLMの構造化抽出 (generate_json) が想定通り 2回 呼び出されました。")

        # D. 結果の結合確認
        # Regexの結果が含まれているか
        self.assertTrue(result.get("func_pain_chk"))
        # Extractionバッチの結果が含まれているか
        self.assertEqual(result.get("func_basic_rolling_level"), "independent")
        # Planバッチの結果が含まれているか
        self.assertEqual(result.get("goals_at_discharge_txt"), "自宅復帰")
        
        # E. チェックボックス復元ロジックの確認
        # rolling_level='independent' -> rolling_chk=True, rolling_independent_chk=True になっているか
        self.assertTrue(result.get("func_basic_rolling_chk"))
        self.assertTrue(result.get("func_basic_rolling_independent_chk"))
        print("✅ チェックボックスの自動復元 (restore_checkboxes) が機能しました。")

        print("\n=== 全テスト成功: ロジックは正しく実装されています ===")

if __name__ == '__main__':
    unittest.main()