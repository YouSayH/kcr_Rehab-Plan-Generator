"""管理画面の破壊的操作がCSRF保護されていることの検証。

背景: 監査所見 be-06。職員削除と担当解除が GET で実装されており、
Flask-WTF の CSRF 検証は既定で GET を対象外にするため保護が全く効いていなかった。
管理者がログイン中に攻撃ページのリンクや、HTMLメール内の画像を読み込むだけで
発火し、staff_patients の ON DELETE CASCADE で担当割当が連鎖削除され、
計画書の作成者(fk_plan_staff_id)も ON DELETE SET NULL で失われる。
"""

import pytest
from flask import url_for
from werkzeug.security import generate_password_hash

from app.models import Patient, Staff


@pytest.fixture
def admin_client(client, db_session):
    """管理者としてログイン済みのクライアント。"""
    admin = Staff(
        username="csrf_admin",
        password=generate_password_hash("password"),
        role="admin",
        occupation="Dr",
        must_change_password=False,
    )
    db_session.add(admin)
    db_session.commit()
    client.post("/login", data={"username": "csrf_admin", "password": "password"},
                follow_redirects=True)
    return client


@pytest.fixture
def victim_staff(db_session):
    """削除対象になる職員。"""
    staff = Staff(
        username="victim",
        password=generate_password_hash("password"),
        role="general",
        occupation="PT",
        must_change_password=False,
    )
    db_session.add(staff)
    db_session.commit()
    return staff


def test_delete_staff_rejects_get(admin_client, app, db_session, victim_staff):
    """職員削除がGETでは実行されないこと。"""
    with app.test_request_context():
        url = url_for("admin.delete_staff", staff_id=victim_staff.id)

    response = admin_client.get(url)

    assert response.status_code == 405, "GETで職員削除が実行できてしまう"
    db_session.expire_all()
    assert db_session.query(Staff).filter_by(username="victim").first() is not None


def test_unassign_rejects_get(admin_client, app, db_session, victim_staff):
    """担当解除がGETでは実行されないこと。"""
    patient = Patient(name="担当解除 対象", gender="男")
    db_session.add(patient)
    db_session.commit()
    victim_staff.assigned_patients.append(patient)
    db_session.commit()

    with app.test_request_context():
        url = url_for("admin.unassign", staff_id=victim_staff.id,
                      patient_id=patient.patient_id)

    response = admin_client.get(url)

    assert response.status_code == 405, "GETで担当解除が実行できてしまう"
    db_session.expire_all()
    reloaded = db_session.query(Staff).filter_by(id=victim_staff.id).first()
    assert len(reloaded.assigned_patients) == 1, "担当割当が解除されてしまった"


def test_delete_staff_works_with_post(admin_client, app, db_session, victim_staff):
    """POSTなら従来どおり削除できること。"""
    with app.test_request_context():
        url = url_for("admin.delete_staff", staff_id=victim_staff.id)

    admin_client.post(url, follow_redirects=True)

    db_session.expire_all()
    assert db_session.query(Staff).filter_by(username="victim").first() is None


def test_csrf_lifetime_matches_session_lifetime(app):
    """CSRFトークンの有効期限がセッションより短くないこと。

    短いと、長時間の編集の末に保存ボタンを押した瞬間に400になり、
    入力内容が失われる。
    """
    csrf_limit = app.config.get("WTF_CSRF_TIME_LIMIT")
    session_lifetime = app.config["PERMANENT_SESSION_LIFETIME"].total_seconds()

    assert csrf_limit is None or csrf_limit >= session_lifetime, (
        f"CSRFの有効期限({csrf_limit}秒)がセッション({session_lifetime}秒)より短い"
    )


def test_session_cookie_hardening(app):
    """セッションCookieに保護属性が設定されていること。"""
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
