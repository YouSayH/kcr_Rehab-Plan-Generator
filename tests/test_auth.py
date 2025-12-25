from flask import url_for
from werkzeug.security import generate_password_hash

from app.core.database import Staff


def test_login_page_loads(client, app):
    """ログインページが正常に開くか"""
    with app.test_request_context():
        login_url = url_for('auth.login')

    response = client.get(login_url)
    assert response.status_code == 200
    assert "ログイン" in response.data.decode("utf-8")

def test_login_success(client, app, db_session):
    """正しい認証情報でログインできるか"""
    # ユーザー準備
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

    # ログイン試行
    response = client.post(login_url, data={
        "username": "test_login_user",
        "password": password
    }, follow_redirects=True)

    # リダイレクトされてトップページ(index)が表示されているか
    assert response.status_code == 200
    # ログイン後の画面チェック (タイトルからログインが消えている、またはRehab Plan Generatorがある等)
    assert "ログイン" not in response.data.decode("utf-8")

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
