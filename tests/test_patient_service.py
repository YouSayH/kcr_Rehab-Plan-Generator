import json
from unittest.mock import MagicMock, patch

from app.services import patient_service


# --- 1. データ変換ロジックのテスト ---
def test_normalize_patient_form_data():
    """
    フォームからの入力（ラジオボタンの値）が、
    DB保存用のチェックボックス形式（key=on）に正しく変換されるか検証
    """
    input_data = {
        "name": "Test Patient",
        # ケースA: 通常のラジオボタン
        "func_basic_rolling_level": "independent",
        # ケースB: 特殊な値の変換
        "func_basic_sitting_balance_level": "partial_assist",
        # ケースC: 除外すべき値 (yes/no)
        "func_circulatory_arrhythmia_status_slct": "yes",
        # ケースD: 介護度
        "social_care_level_support_num_slct": "1"
    }

    result = patient_service.normalize_form_data(input_data)

    assert result["name"] == "Test Patient"
    assert result.get("func_basic_rolling_independent_chk") == "on"
    assert result.get("func_basic_sitting_balance_partial_assistance_chk") == "on"
    assert "func_circulatory_arrhythmia_status_yes_chk" not in result
    assert result.get("social_care_level_support_num1_slct") == "on"

# --- 2. 編集ページ用データ準備ロジックのテスト ---
@patch("app.services.patient_service.patient_crud")
@patch("app.services.patient_service.SessionLocal")
def test_prepare_edit_page_data(mock_session_cls, mock_patient_crud):
    """
    編集ページ表示に必要なデータセットが正しく構築されるか検証
    """
    patient_id = 123

    # --- モックの設定: 患者データ ---
    mock_patient = MagicMock()
    mock_patient.name = "Test Taro"
    mock_patient.age = 80

    # FIX: カラムのモック作成（.name属性が文字列を返すように明示的に設定）
    col_name = MagicMock()
    col_name.name = "name"
    col_pid = MagicMock()
    col_pid.name = "patient_id"

    mock_patient_table = MagicMock()
    mock_patient_table.columns = [col_name, col_pid]
    mock_patient.__table__ = mock_patient_table

    # --- モックの設定: 計画書履歴 ---
    mock_plan = MagicMock()
    mock_plan.plan_id = 1
    mock_plan.created_at = "2025-01-01"
    mock_plan.patient = mock_patient

    # FIX: 計画書カラムのモックも同様に設定
    col_plan_id = MagicMock()
    col_plan_id.name = "plan_id"
    col_created_at = MagicMock()
    col_created_at.name = "created_at"

    mock_plan_table = MagicMock()
    mock_plan_table.columns = [col_plan_id, col_created_at]
    mock_plan.__table__ = mock_plan_table

    # --- Sessionの挙動設定 ---
    mock_session = mock_session_cls.return_value
    # query().filter()...all() のチェーンをモックし、リストを返す
    mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_plan]
    # plan_history用のクエリ (limitなしのall) にも対応
    # ※厳密に分ける場合はside_effectを使うが、ここでは簡略化のため同じ戻り値でテスト可能

    # 実行
    result = patient_service.prepare_edit_page_data(patient_id)

    # 検証
    assert result["patient_data"]["name"] == "Test Taro"
    assert "fim_history_json" in result
    json_data = json.loads(result["fim_history_json"])
    assert isinstance(json_data, list)
    # グラフ用データにもカラム値が含まれているか確認
    assert json_data[0]["plan_id"] == 1
