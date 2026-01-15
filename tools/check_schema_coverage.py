import sys
import os

# プロジェクトルートパスを通す
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.schemas.schemas import PatientMasterSchema
from app.services.extraction.fast_extractor import FastExtractor

def check_coverage():
    print("=== Schema Coverage Check ===")
    
    # 1. Schemaからターゲットとなる _chk フィールドを全取得
    schema_fields = PatientMasterSchema.model_fields.keys()
    target_chk_fields = {f for f in schema_fields if f.endswith('_chk')}
    
    print(f"Total '_chk' fields in Schema: {len(target_chk_fields)}")

    # 2. FastExtractor の label_mapping キーを取得
    extractor = FastExtractor(use_gpu=False)
    implemented_keys = set(extractor.label_mapping.keys())
    
    # 3. 差分検出 (Schemaにあるが、Extractorにないもの)
    missing_fields = target_chk_fields - implemented_keys
    
    # 除外リスト (意図的に実装しない、または親項目でカバーするものなど)
    # 例: 親項目がTrueなら自動でTrueになるものや、数値項目に関連するもの
    ignore_list = {
        "func_risk_factors_chk", # 子項目(高血圧等)から判定可能
        "func_motor_dysfunction_chk", 
        "func_sensory_dysfunction_chk",
        "func_speech_disorder_chk",
        "func_speech_other_chk",
        "nutrition_height_chk", "nutrition_weight_chk", "nutrition_bmi_chk", # 数値があればTrue
        "social_care_level_applying_chk", # "申請中" は social_care_level_status_chk で拾う？
        "goal_p_residence_chk", # 選択肢(slct)で拾うかも
        # 詳細な介助レベルのchkは、Glinerで拾うよりLLMで判定する方が無難な場合も
        "func_basic_rolling_independent_chk", "func_basic_rolling_partial_assistance_chk", 
        "func_basic_rolling_assistance_chk", "func_basic_rolling_not_performed_chk",
        "func_basic_getting_up_independent_chk", "func_basic_getting_up_partial_assistance_chk",
        "func_basic_getting_up_assistance_chk", "func_basic_getting_up_not_performed_chk",
        "func_basic_standing_up_independent_chk", "func_basic_standing_up_partial_assistance_chk",
        "func_basic_standing_up_assistance_chk", "func_basic_standing_up_not_performed_chk",
        "func_basic_sitting_balance_independent_chk", "func_basic_sitting_balance_partial_assistance_chk",
        "func_basic_sitting_balance_assistance_chk", "func_basic_sitting_balance_not_performed_chk",
        "func_basic_standing_balance_independent_chk", "func_basic_standing_balance_partial_assistance_chk",
        "func_basic_standing_balance_assistance_chk", "func_basic_standing_balance_not_performed_chk",
        # ... 他のGoal詳細など
    }

    # 本当に実装すべき不足項目
    real_missing = sorted(list(missing_fields - ignore_list))

    if real_missing:
        print(f"\n--- Missing Fields ({len(real_missing)}) ---")
        print("(これらはSchemaに存在するが、FastExtractorでキーワード定義されていません)")
        for field in real_missing:
            description = PatientMasterSchema.model_fields[field].description
            print(f"- {field}: {description}")
    else:
        print("\n--- Missing Fields (0) ---")
        print("(これらはSchemaに存在するが、FastExtractorでキーワード定義されていません)")

    # 4. 実装済みだが、Schemaにないもの (スペルミス確認)
    unknown_fields = implemented_keys - target_chk_fields
    if unknown_fields:
        print(f"\n--- Unknown Fields in Extractor ({len(unknown_fields)}) ---")
        print("(これらはExtractorに定義されていますが、Schemaに存在しません。スペルミスかも？)")
        for field in unknown_fields:
            print(f"- {field}")
    else:
        print("\n--- Unknown Fields in Extractor (0) ---")
        print("(これらはExtractorに定義されていますが、Schemaに存在しません)")

if __name__ == "__main__":
    check_coverage()