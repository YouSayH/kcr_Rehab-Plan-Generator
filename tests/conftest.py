import pytest

from app.main import app as flask_app


# ログインユーザーのモック用クラス
class MockUser:
    def __init__(self, id, role="staff", username="test_user", is_authenticated=True):
        self.id = id
        self.role = role
        self.username = username
        self.is_authenticated = is_authenticated # プロパティではなく値として持つ簡易実装

@pytest.fixture
def app():
    """テスト用のFlaskアプリインスタンスを作成"""
    # 【変更】既存のappインスタンスをテスト設定で上書き
    flask_app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test_secret_key"
    })
    return flask_app

@pytest.fixture
def client(app):
    """テスト用クライアント"""
    return app.test_client()

@pytest.fixture
def mock_db(mocker):
    """データベースアクセスのモック"""
    return mocker.patch("app.core.database")
