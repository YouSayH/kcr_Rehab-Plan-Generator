import pytest
from app.services.extraction.fast_extractor import FastExtractor

@pytest.fixture(scope="module")
def extractor():
    # モデルロードに時間がかかるためmoduleスコープ推奨
    return FastExtractor(use_gpu=False)

class TestFastExtractor:

    def test_extract_basic_facts(self, extractor):
        """基本的な肯定文からの抽出テスト"""
        text = """
        患者プロフィール: テスト 太郎 (80歳・男性)
        診断名: 脳梗塞による右片麻痺
        既往歴: 高血圧症、糖尿病あり。
        """
        result = extractor.extract_facts(text)
        
        assert result['name'] == 'テスト 太郎'
        assert result['age'] == 80
        assert result['gender'] == '男'
        assert result.get('func_motor_paralysis_chk') is True  # 麻痺
        assert result.get('func_risk_hypertension_chk') is True  # 高血圧
        assert result.get('func_risk_diabetes_chk') is True      # 糖尿病

    def test_extract_with_negation(self, extractor):
        """否定文が含まれる場合の抽出テスト"""
        text = """
        麻痺なし。
        疼痛は認めない。
        高血圧の既往はない。
        """
        result = extractor.extract_facts(text)
        
        # これらは否定されているため、結果に含まれない（FalseまたはNone）はず
        assert not result.get('func_motor_paralysis_chk')
        assert not result.get('func_pain_chk')
        assert not result.get('func_risk_hypertension_chk')

    def test_extract_complex_adl(self, extractor):
        """ADLや目標に関する抽出テスト"""
        text = """
        食事は自立。
        排泄は手すりを使用して自立。
        入浴は見守りが必要（介助）。
        目標：復職を目指す。
        """
        result = extractor.extract_facts(text)
        
        # 食事に関するキーワードヒット（自立・介助の区別まではRegexでしない設計の場合、有無だけ確認）
        # ※ label_mappingの実装に依存しますが、"食事"などでヒットするか確認
        assert result.get('nutrition_method_oral_chk') or result.get('nutrition_method_oral_meal_chk')
        
        # 目標
        assert result.get('goal_p_return_to_work_chk') is True # 復職

    def test_comorbidities_generation(self, extractor):
        """併存疾患テキストの自動生成テスト"""
        text = "高血圧、糖尿病、脂質異常症あり"
        result = extractor.extract_facts(text)
        
        comorbidities = result.get('main_comorbidities_txt', "")
        assert "高血圧症" in comorbidities
        assert "糖尿病" in comorbidities
        assert "脂質異常症" in comorbidities