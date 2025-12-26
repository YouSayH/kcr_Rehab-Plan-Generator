import pytest

from app.utils.helpers import has_permission_for_patient


# 権限チェック用のダミーユーザークラス
class MockUser:
    def __init__(self, id, role="staff", is_authenticated=True):
        self.id = id
        self.role = role
        self.is_authenticated = is_authenticated

@pytest.fixture
def mock_helpers_crud(mocker):
    # 【変更】database ではなく staff_crud をモックする
    # app/utils/helpers.py で "from app.crud import staff as staff_crud" しているため
    return mocker.patch("app.utils.helpers.staff_crud")

def test_has_permission_admin(mock_helpers_crud):
    """管理者は常にアクセス許可"""
    admin_user = MockUser(id=1, role="admin")

    # モックの設定は不要（adminチェックで即returnするため）
    assert has_permission_for_patient(admin_user, patient_id=123) is True

def test_has_permission_assigned_staff(mock_helpers_crud):
    """担当スタッフの場合アクセス許可"""
    staff_user = MockUser(id=2, role="staff")

    # 【変更】staff_crud.get_assigned_patients の戻り値を設定
    mock_helpers_crud.get_assigned_patients.return_value = [
        {"patient_id": 100, "name": "Patient A"},
        {"patient_id": 101, "name": "Patient B"}
    ]

    # ID=100 は担当リストにあるので True
    assert has_permission_for_patient(staff_user, patient_id=100) is True

def test_has_permission_unassigned_staff(mock_helpers_crud):
    """担当外スタッフの場合アクセス拒否"""
    staff_user = MockUser(id=3, role="staff")

    # 【変更】担当患者リスト
    mock_helpers_crud.get_assigned_patients.return_value = [
        {"patient_id": 200, "name": "Patient C"}
    ]

    # ID=999 は担当リストにないので False
    assert has_permission_for_patient(staff_user, patient_id=999) is False

def test_has_permission_not_authenticated():
    """未認証ユーザーはFalse"""
    anon_user = MockUser(id=None, is_authenticated=False)
    assert has_permission_for_patient(anon_user, patient_id=1) is False
