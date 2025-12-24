import pytest

from app.utils.helpers import has_permission_for_patient


# このファイル専用のモックフィクスチャを定義
@pytest.fixture
def mock_helpers_db(mocker):
    # app.utils.helpers モジュールの中にある 'database' 変数をモックに置き換える
    return mocker.patch("app.utils.helpers.database")

def test_has_permission_admin(mock_helpers_db):
    """管理者は常にTrueを返すか"""
    admin_user = type('User', (object,), {'is_authenticated': True, 'role': 'admin', 'id': 1})
    assert has_permission_for_patient(admin_user, 999) is True

def test_has_permission_assigned_staff(mock_helpers_db):
    """担当患者の場合はTrueを返すか"""
    staff_user = type('User', (object,), {'is_authenticated': True, 'role': 'staff', 'id': 10})

    # モックの挙動を設定
    mock_helpers_db.get_assigned_patients.return_value = [
        {"patient_id": 100, "name": "Patient A"},
        {"patient_id": 101, "name": "Patient B"}
    ]

    assert has_permission_for_patient(staff_user, 100) is True

def test_has_permission_unassigned_staff(mock_helpers_db):
    """担当外の患者の場合はFalseを返すか"""
    staff_user = type('User', (object,), {'is_authenticated': True, 'role': 'staff', 'id': 10})

    mock_helpers_db.get_assigned_patients.return_value = [
        {"patient_id": 100, "name": "Patient A"}
    ]

    assert has_permission_for_patient(staff_user, 999) is False

def test_has_permission_anonymous():
    """未ログインユーザーはFalseを返すか"""
    anon_user = type('User', (object,), {'is_authenticated': False})
    assert has_permission_for_patient(anon_user, 100) is False
