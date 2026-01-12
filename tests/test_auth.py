import os

from flask import session, url_for
from werkzeug.security import generate_password_hash

# Flask-Login用モデル (型チェック用)
from app.auth_models import Staff as AuthStaff

# DBモデル (SQLAlchemy)
from app.models import Staff


def test_login_page_loads(client, app):
    """ログインページが正常に開くか"""
    with app.test_request_context():
        login_url = url_for('auth.login')

    response = client.get(login_url)
    assert response.status_code == 200
    assert "ログイン" in response.data.decode("utf-8")


def test_login_success(client, app, db_session):
    """正しい認証情報でログインし、セッションが維持されるか"""
    # 1. ユーザー準備
    password = "password"
    hashed_pw = generate_password_hash(password)
    staff = Staff(username="test_login_user", password=hashed_pw, occupation="PT", role="staff")
    db_session.add(staff)
    db_session.commit()

    with app.test_request_context():
        login_url = url_for('auth.login')
        # indexはplanブループリント配下
        # テンプレート側がまだ修正されていない場合でも、URL生成自体は成功するはず
        # もしテンプレートエラーが出るなら、まずはログイン成功後のリダイレクト(302)を確認するだけでも良い

    # 2. ログイン試行
    response = client.post(login_url, data={
        "username": "test_login_user",
        "password": password
    }, follow_redirects=True)

    # 3. 画面遷移の確認
    assert response.status_code == 200
    # ログイン成功後はログイン画面の要素が消えているはず
    assert "ログイン" not in response.data.decode("utf-8")

    # セッションにユーザーIDが保存されているか確認 (Flask-Loginの仕様)
    with client.session_transaction() as sess:
        assert sess['_user_id'] == str(staff.id)


def test_login_failure(client, app, db_session):
    """誤ったパスワードでログイン失敗するか"""
    password = "password"
    hashed_pw = generate_password_hash(password)
    staff = Staff(username="test_fail_user", password=hashed_pw, occupation="PT", role="staff")
    db_session.add(staff)
    db_session.commit()

    with app.test_request_context():
        login_url = url_for('auth.login')

    response = client.post(login_url, data={
        "username": "test_fail_user",
        "password": "wrong_password"
    }, follow_redirects=True)

    html = response.data.decode("utf-8")
    assert "ユーザー名またはパスワードが正しくありません" in html


def test_logout(client, app, login_staff):
    """ログアウト処理のテスト"""
    # login_staff フィクスチャですでにログイン済み

    with app.test_request_context():
        logout_url = url_for('auth.logout')

    response = client.get(logout_url, follow_redirects=True)

    assert response.status_code == 200
    assert "ログイン" in response.data.decode("utf-8")

    # セッションからユーザーIDが消えているか確認
    with client.session_transaction() as sess:
        assert '_user_id' not in sess


def test_user_loader(app, db_session):
    """
    Flask-Loginのuser_loader (load_user関数) を直接テストする。
    """
    # 1. テストデータ準備
    token = os.urandom(24).hex()
    staff = Staff(
        username="loader_test",
        password="pw",
        occupation="OT",
        role="staff",
        session_token=token  # トークンを予め設定しておく
    )
    db_session.add(staff)
    db_session.commit()

    # 2. テストリクエストコンテキスト内で load_user を実行
    with app.test_request_context():
        # セッションにトークンがある状態をシミュレート
        session["session_token"] = token

        # アプリに登録されている user_loader コールバック関数を取得
        # (app/__init__.py で @login_manager.user_loader デコレータをつけた関数)
        loader = app.login_manager._user_callback

        # 実行 (ここで app/__init__.py の load_user が走る)
        loaded_user = loader(str(staff.id))

        # 検証
        assert loaded_user is not None
        # 正しいクラス(AuthStaff)のインスタンスかチェック
        assert isinstance(loaded_user, AuthStaff)
        # 型の違い(int vs str)を吸収して比較、またはint同士で比較
        assert int(loaded_user.id) == staff.id
        assert loaded_user.username == "loader_test"

        # セッショントークンが一致しない場合は None が返るべき（セキュリティチェック）
        session["session_token"] = "invalid_token"
        assert loader(str(staff.id)) is None
