import pytest
from app.services.extraction.nlp_loader import load_ginza
from app.services.extraction.negation import NegationDetector

@pytest.fixture(scope="module")
def negation_detector():
    """テスト用にNegationDetectorを初期化（モジュール単位で1回だけロード）"""
    nlp = load_ginza()
    return NegationDetector(nlp)

class TestNegationDetector:
    
    @pytest.mark.parametrize("text, keyword, expected", [
        # --- 肯定（否定されていない）ケース ---
        ("右片麻痺を認める。", "麻痺", False),
        ("疼痛あり。", "疼痛", False),
        ("高血圧の既往がある。", "高血圧", False),
        ("食事は自立している。", "自立", False),
        
        # --- 否定ケース (単純な否定) ---
        ("麻痺なし。", "麻痺", True),
        ("麻痺はない。", "麻痺", True),
        ("疼痛は認めない。", "疼痛", True),
        ("発熱は見られない。", "発熱", True),
        ("高血圧の既往なし。", "高血圧", True),
        
        # --- 否定ケース (文脈・記号) ---
        ("浮腫(-)", "浮腫", True),
        ("浮腫（-）", "浮腫", True),
        ("浮腫：なし", "浮腫", True),
        
        # --- 少し難しいケース (係り受けが必要なもの) ---
        ("明らかな運動麻痺は認めず、感覚障害のみ。", "運動麻痺", True),
        ("麻痺は消失した。", "麻痺", True),
    ])
    def test_is_negated(self, negation_detector, text, keyword, expected):
        """様々なパターンの否定判定をテスト"""
        # 擬似的にエンティティ情報を構築
        start = text.find(keyword)
        assert start != -1, f"Test data error: keyword '{keyword}' not found in '{text}'"
        end = start + len(keyword)
        
        entity_info = {'start': start, 'end': end, 'text': keyword}
        
        # GiNZA解析
        doc = negation_detector.nlp(text)
        
        # 判定実行
        result = negation_detector.is_negated(text, entity_info, doc)
        assert result == expected, f"Failed for text: '{text}' keyword: '{keyword}'"

    def test_check_snippet_negation_fallback(self, negation_detector):
        """ルールベース（スニペットチェック）のフォールバックテスト"""
        text = "麻痺なし"
        keyword = "麻痺"
        # nlpを使わずに簡易メソッドを呼ぶ
        assert negation_detector.check_snippet_negation(text, keyword) is True