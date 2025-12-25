from flask import url_for


def test_admin_signup_access_denied_for_staff(client, app, mock_db, mocker):
    """一般スタッフが管理者ページ(signup)にアクセスしようとすると拒否されるか"""
    mock_user = {"id": 2, "username": "staff", "password": "pw", "role": "staff", "occupation": "PT", "session_token": "token"}
    mock_db.get_staff_by_id.return_value = mock_user

    with client.session_transaction() as sess:
        sess["session_token"] = "token"
        sess["_user_id"] = "2"

    with app.test_request_context():
        signup_url = url_for('admin.signup')

    # 【重要】follow_redirects=True を指定
    response = client.get(signup_url, follow_redirects=True)

    assert response.status_code == 200

def test_admin_signup_access_allowed_for_admin(client, app, mock_db, mocker):
    """管理者が管理者ページにアクセスできるか"""
    mock_admin = {"id": 1, "username": "admin", "password": "pw", "role": "admin", "occupation": "Dr", "session_token": "token_admin"}
    mock_db.get_staff_by_id.return_value = mock_admin

    with client.session_transaction() as sess:
        sess["session_token"] = "token_admin"
        sess["_user_id"] = "1"

    with app.test_request_context():
        signup_url = url_for('admin.signup')

    response = client.get(signup_url)

    assert response.status_code == 200
    # 【重要】画面の実際のタイトル「新規職員登録」に合わせる
    assert "新規職員登録" in response.data.decode("utf-8")

def test_create_staff(client, app, mock_db, mocker):
    """管理者が新規ユーザーを作成できるか"""
    mock_admin = {"id": 1, "username": "admin", "password": "pw", "role": "admin", "occupation": "Dr", "session_token": "token_admin"}
    mock_db.get_staff_by_id.return_value = mock_admin
    with client.session_transaction() as sess:
        sess["session_token"] = "token_admin"
        sess["_user_id"] = "1"

    mock_db.get_staff_by_username.return_value = None
    mock_create = mock_db.create_staff

    with app.test_request_context():
        signup_url = url_for('admin.signup')

    client.post(signup_url, data={
        "username": "new_staff",
        "password": "new_password",
        "occupation": "PT"
    }, follow_redirects=True)

    args, _ = mock_create.call_args
    assert args[0] == "new_staff"
    assert args[2] == "PT"
    assert mock_create.called
