from datetime import date

from flask import url_for

# 操作関数(assign_patient_to_staff)を app.crud.staff からインポート
from app.crud.staff import assign_patient_to_staff

# モデル定義を app.models からインポート
from app.models import Patient, RehabilitationPlan, Staff


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

# --- 【追加】 Phase 1: save_plan のテスト ---

def test_save_plan_success(login_staff, app, db_session):
    """
    正常系: 計画書の保存フローが正しく完了するか検証
    (DB保存 -> Excel生成 -> ダウンロードページへの遷移)
    """
    # 1. テスト用データの準備
    patient = Patient(name="Save Test Patient", date_of_birth=date(1990, 5, 5), gender="Female")
    db_session.add(patient)
    db_session.commit()

    staff = db_session.query(Staff).filter_by(username="test_user").first()
    assign_patient_to_staff(staff.id, patient.patient_id)

    # 保存するフォームデータ (必須項目+α)
    form_data = {
        "patient_id": patient.patient_id,
        "therapist_notes": "保存テスト用の所見",
        "suggestion_main_risks": "転倒リスクあり", # AI提案項目のシミュレーション
        # ... 他の項目は省略してもDB定義上Nullableなら通るはずですが、必要に応じて追加
        "regeneration_history": "[]"
    }

    with app.test_request_context():
        target_url = url_for('plan.save_plan')

    # 2. POST実行
    # Excel生成処理が含まれるため、モックを使わずに実行すると実際にファイル生成を試みますが、
    # テスト環境(in-memory DB)での整合性を確認するため、ここでは結合テストとして実行します。
    # ※ 本来は excel_writer をモック化するのがUnit Testとしては望ましいですが、
    #    Phase 1の目的は「現状の挙動の担保」なので、エラーが出ないことを確認します。
    try:
        response = login_staff.post(target_url, data=form_data, follow_redirects=True)
    except FileNotFoundError:
        # Excelテンプレートファイルがテスト環境で見つからない場合のエラーハンドリング
        # CI/CD環境などではテンプレートの配置に注意が必要です
        import pytest
        pytest.skip("Excel template not found, skipping save_plan integration test")

    # 3. 検証
    assert response.status_code == 200

    # ダウンロード準備完了ページが表示されているか
    response_text = response.data.decode('utf-8')
    assert "download_and_redirect.html" in response_text or "ダウンロード" in response_text

    # 4. DBに保存されたか確認
    saved_plan = db_session.query(RehabilitationPlan).filter_by(patient_id=patient.patient_id).first()
    assert saved_plan is not None
    assert saved_plan.created_by_staff_id == staff.id
