from flask import url_for
from werkzeug.security import generate_password_hash

# conftest.py で定義された app, client, mock_db を使用

def test_login_page_loads(client, app):
    """ログインページが正常に開くか"""
    with app.test_request_context():
        login_url = url_for('auth.login')

    response = client.get(login_url)
    assert response.status_code == 200
    assert "ログイン" in response.data.decode("utf-8")

def test_login_success(client, app, mock_db, mocker):
    """正しい認証情報でログインできるか"""
    # 1. ログイン用のモック (get_staff_by_username)
    valid_password = "password"
    hashed_pw = generate_password_hash(valid_password)

    mock_staff_data_login = {
        "id": 1,
        "username": "test_user",
        "password": hashed_pw,
        "role": "staff",
        "occupation": "PT",
        "session_token": "old_token" # ログイン前は古いトークン
    }
    mock_db.get_staff_by_username.return_value = mock_staff_data_login

    # 2. ログイン試行 (リダイレクトを追跡しない！)
    with app.test_request_context():
        login_url = url_for('auth.login')
        index_url = url_for('index')

    # follow_redirects=False にして、セッション更新後に一旦止める
    response = client.post(login_url, data={
        "username": "test_user",
        "password": valid_password
    }, follow_redirects=False)

    # まずはログイン処理自体が成功して、リダイレクト(302)しようとしているか確認
    assert response.status_code == 302
    assert response.location == index_url or index_url in response.location

    # 3. 生成された新しいセッショントークンを取得
    with client.session_transaction() as sess:
        new_token = sess.get("session_token")
        assert new_token is not None # トークンが生成されていること

    # 4. user_loader用のモック (get_staff_by_id)
    # ここで、セッション内のトークンと一致するトークンを持ったユーザーデータを返す
    mock_staff_data_load = mock_staff_data_login.copy()
    mock_staff_data_load["session_token"] = new_token

    mock_db.get_staff_by_id.return_value = mock_staff_data_load

    # 5. リダイレクト先（トップページ）へ手動でアクセス
    response_redirect = client.get(index_url)

    # 6. 検証: 今度は弾かれずに200 OKになるはず
    assert response_redirect.status_code == 200
    # ログイン後の画面にいるはず（ログイン画面の要素がないか、ログアウトボタンがあるか等）
    assert "ログイン" not in response_redirect.data.decode("utf-8") # タイトルの"ログイン"を含まない

def test_login_failure(client, app, mock_db, mocker):
    """誤ったパスワードでログイン失敗するか"""
    hashed_pw = generate_password_hash("correct_password")

    mock_staff_data = {
        "id": 1,
        "username": "test_user",
        "password": hashed_pw,
    }
    mock_db.get_staff_by_username.return_value = mock_staff_data

    with app.test_request_context():
        login_url = url_for('auth.login')

    response = client.post(login_url, data={
        "username": "test_user",
        "password": "wrong_password"
    }, follow_redirects=True)

    html = response.data.decode("utf-8")
    assert "ユーザー名またはパスワードが正しくありません" in html

def test_logout(client, app, mock_db, mocker):
    """ログアウト処理のテスト"""
    # ログイン用のデータ
    hashed_pw = generate_password_hash("p")
    user_data = {
        "id": 1, "username": "u", "password": hashed_pw,
        "role": "staff", "occupation": "OT", "session_token": "token"
    }

    mock_db.get_staff_by_username.return_value = user_data
    mock_db.get_staff_by_id.return_value = user_data # logout時のload_user用

    with app.test_request_context():
        login_url = url_for('auth.login')
        logout_url = url_for('auth.logout')

    # ログイン
    client.post(login_url, data={"username": "u", "password": "p"})

    # user_loader対策: ログインでトークンが変わっているため、login_success同様に対応が必要だが、
    # ログアウト処理自体はcurrent_userを使わない場合もある。
    # Flask-Loginのlogout_userはcurrent_userを要求するため、ここも厳密にはトークン合わせが必要。
    # 簡易的に、sessionを上書きしてモックと合わせる手法をとる。
    with client.session_transaction() as sess:
        sess["session_token"] = "fixed_token"
    user_data["session_token"] = "fixed_token"

    # ログアウト実行
    response = client.get(logout_url, follow_redirects=True)

    # 検証
    assert response.status_code == 200
    assert "ログイン" in response.data.decode("utf-8")
