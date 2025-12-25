from unittest.mock import MagicMock

import pytest

# app.main をインポートする前に、必要なモジュール構造をモック化することも検討できますが、
# ここでは明示的なパッチ適用で対応します。
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
    # redirectを追跡する場合でもcookieを保持するように設定
    return app.test_client()

@pytest.fixture
def mock_db(mocker):
    """データベースアクセスのモック (全モジュール共通)"""
    # 共通のモックオブジェクトを作成
    mock_module = MagicMock()

    # 【重要】アプリケーション内の各ファイルが参照している 'database' をすべて書き換える
    # どこか一つでも漏れると、そこだけ本物が動いてバグになります
    mocker.patch("app.core.database", mock_module)         # 基本
    mocker.patch("app.main.database", mock_module)         # main.py
    mocker.patch("app.routers.auth.database", mock_module) # auth.py
    mocker.patch("app.routers.admin.database", mock_module)# admin.py
    mocker.patch("app.utils.helpers.database", mock_module)# helpers.py (権限チェック等で使用)

    return mock_module
