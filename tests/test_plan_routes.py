from datetime import date

from flask import url_for

from app.core.database import Patient


def test_index_requires_login(client, app):
    """未ログイン状態でトップページにアクセスするとログインページにリダイレクトされるか"""
    with app.test_request_context():
        target_url = url_for('plan.index')

    response = client.get(target_url)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

def test_index_access(login_staff, app):
    """ログイン状態でトップページにアクセスできるか"""
    with app.test_request_context():
        target_url = url_for('plan.index')

    response = login_staff.get(target_url)
    assert response.status_code == 200
    # レンダリング結果に含まれるはずの文字列
    assert b"Rehab Plan Generator" in response.data or b"patients" in response.data

def test_generate_plan_route(login_staff, app, db_session):
    """計画書生成の確認ページへの遷移テスト"""
    # テスト用患者データを作成
    patient = Patient(name="Test Patient", date_of_birth=date(1980, 1, 1), gender="Male")
    db_session.add(patient)
    db_session.commit()

    with app.test_request_context():
        target_url = url_for('plan.generate_plan')

    response = login_staff.post(target_url, data={
        "patient_id": patient.patient_id,
        "therapist_notes": "テスト所見",
        "model_choice": "gemini"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert "confirm.html" in response.data.decode("utf-8") or "計画書作成" in response.data.decode("utf-8")

def test_view_plan_permission(client, app):
    """権限のない計画書へのアクセス制御（ログインなし）"""
    with app.test_request_context():
        target_url = url_for('plan.view_plan', plan_id=9999)

    response = client.get(target_url)
    assert response.status_code == 302 # ログインへ
