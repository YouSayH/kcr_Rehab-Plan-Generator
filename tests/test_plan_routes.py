from datetime import date

from flask import url_for

from app.core.database import Patient, Staff, assign_patient_to_staff


def test_index_requires_login(client, app):
    """未ログイン状態でトップページにアクセスするとログインページにリダイレクトされるか"""
    with app.test_request_context():
        target_url = url_for('plan.index')

    response = client.get(target_url)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

def test_index_index(login_staff, app):
    """ログイン状態でトップページにアクセスできるか"""
    with app.test_request_context():
        target_url = url_for('plan.index')

    response = login_staff.get(target_url)
    assert response.status_code == 200
    # 日本語のタイトル、またはフォームのIDなどが含まれているか確認する
    # response.data はバイト列なので、decodeして文字列として比較するのがベターです
    response_text = response.data.decode('utf-8')
    assert "リハビリテーション総合実施計画書" in response_text or "patient-select" in response_text


def test_generate_plan_route(login_staff, app, db_session):
    """計画書生成の確認ページへの遷移テスト"""
    # 1. テスト用患者データを作成
    patient = Patient(name="Test Patient", date_of_birth=date(1980, 1, 1), gender="Male")
    db_session.add(patient)
    db_session.commit() # ID確定のために一度コミット

    # 2. 【追加】ログイン中のスタッフを取得し、患者を割り当てる
    # conftest.py の login_staff フィクスチャで作成されるユーザー名は "test_user"
    staff = db_session.query(Staff).filter_by(username="test_user").first()
    assign_patient_to_staff(staff.id, patient.patient_id)

    with app.test_request_context():
        target_url = url_for('plan.generate_plan')

    # 3. POSTリクエスト送信
    response = login_staff.post(target_url, data={
        "patient_id": patient.patient_id,
        "therapist_notes": "テスト所見",
        "model_choice": "gemini"
    }, follow_redirects=True)

    assert response.status_code == 200
    # 成功すれば confirm.html が返ってくるはず
    assert "confirm.html" in response.data.decode("utf-8") or "確認・修正" in response.data.decode("utf-8")

def test_view_plan_permission(client, app):
    """権限のない計画書へのアクセス制御（ログインなし）"""
    with app.test_request_context():
        target_url = url_for('plan.view_plan', plan_id=9999)

    response = client.get(target_url)
    assert response.status_code == 302 # ログインへ
