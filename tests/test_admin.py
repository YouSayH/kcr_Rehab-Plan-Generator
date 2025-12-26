from flask import url_for
from werkzeug.security import generate_password_hash

from app.models import Staff


def test_admin_signup_access_denied_for_staff(client, app, db_session):
    """一般スタッフが管理者ページ(signup)にアクセスしようとすると拒否されるか"""
    # 一般スタッフを作成してログイン
    staff = Staff(username="staff", password=generate_password_hash("pw"), role="staff", occupation="PT")
    db_session.add(staff)
    db_session.commit()

    client.post("/login", data={"username": "staff", "password": "pw"}, follow_redirects=True)

    with app.test_request_context():
        signup_url = url_for('admin.signup')

    # アクセス試行 -> 権限エラーまたはトップへリダイレクトされるはず
    # admin_requiredデコレータの実装によりますが、通常は403かフラッシュメッセージ付きリダイレクト
    response = client.get(signup_url, follow_redirects=True)

    # ページ内に「新規職員登録」が表示されていないことを確認
    assert "新規職員登録" not in response.data.decode("utf-8")

def test_admin_signup_access_allowed_for_admin(client, app, db_session):
    """管理者が管理者ページにアクセスできるか"""
    # 管理者を作成してログイン
    admin = Staff(username="admin", password=generate_password_hash("pw"), role="admin", occupation="Dr")
    db_session.add(admin)
    db_session.commit()

    client.post("/login", data={"username": "admin", "password": "pw"}, follow_redirects=True)

    with app.test_request_context():
        signup_url = url_for('admin.signup')

    response = client.get(signup_url, follow_redirects=True)

    assert response.status_code == 200
    assert "新規職員登録" in response.data.decode("utf-8")

def test_create_staff(client, app, db_session):
    """管理者が新規ユーザーを作成できるか"""
    # 管理者でログイン
    admin = Staff(username="admin", password=generate_password_hash("pw"), role="admin", occupation="Dr")
    db_session.add(admin)
    db_session.commit()
    client.post("/login", data={"username": "admin", "password": "pw"}, follow_redirects=True)

    with app.test_request_context():
        signup_url = url_for('admin.signup')

    # 新規スタッフ作成POST
    client.post(signup_url, data={
        "username": "new_staff",
        "password": "new_password",
        "occupation": "PT"
    }, follow_redirects=True)

    # DBに保存されたか確認
    created_staff = db_session.query(Staff).filter_by(username="new_staff").first()
    assert created_staff is not None
    assert created_staff.occupation == "PT"
