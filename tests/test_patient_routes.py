from datetime import date

from flask import url_for

from app.crud.staff import assign_patient_to_staff
from app.models import Patient, RehabilitationPlan, Staff


# 引数に 'app' を追加 (conftest.pyのappフィクスチャを受け取るため)
def test_edit_patient_info_route(login_staff, app):
    """患者情報編集ページへのアクセス"""

    # リクエストコンテキストを作成して url_for を有効化
    with app.test_request_context():
        # ルート名は 'patient.register_patient' (新規登録) または 'patient.edit_patient_info' (編集)
        # routers/patient.py の実装を確認すると、register_patient が GET/POST 両対応している場合が多いですが、
        # 今回のコードでは edit_patient_info が GET, save_patient_info が POST という構成に見えます。
        # ただし、新規登録画面への遷移が edit_patient_info (paramなし) なのかを確認。
        # 実装上、current_patient_id がなければ新規扱いになっているため、edit_patient_info を呼び出します。
        target_url = url_for('patient.edit_patient_info') # ルート名を確認(edit_patient_info or register_patient)

    # クエリパラメータなしでアクセス（＝新規登録画面）
    response = login_staff.get(target_url)
    assert response.status_code == 200
    # テンプレート内の特徴的な文字列が含まれているか確認（例: "基本情報" や "患者ID" など）
    # ※ 実際のテンプレートに合わせて調整してください
    assert "基本情報" in response.data.decode("utf-8") or "患者" in response.data.decode("utf-8")

# def test_save_patient_info_route(login_staff, app, db_session):
#     """患者情報の保存処理（POST）"""

def test_save_patient_info_create(login_staff, app, db_session):
    """患者情報の新規保存テスト"""
    with app.test_request_context():
        target_url = url_for('patient.save_patient_info')

    # データベースの定義に基づき、保存に必要なデータを揃える
    data = {
        # 新規登録時は patient_id を空にするか含めない
        "patient_id": "",
        "name": "テスト患者",      # 【必須】
        "name_kana": "テストカンジャ",
        "age": "80",              # 年齢 (内部計算で使用)
        "gender": "女性",         # 性別
        "bi_total": "100",
        "fim_total": "120",
        # チェックボックスの動作確認用
        "func_basic_rolling_level": "independent"
    }

    # follow_redirects=True で保存後のリダイレクト先まで追跡
    response = login_staff.post(target_url, data=data, follow_redirects=True)
    assert response.status_code == 200

    # DB確認: 患者が作成されているか
    saved_patient = db_session.query(Patient).filter_by(name="テスト患者").first()
    assert saved_patient is not None
    assert saved_patient.gender == "女性"

    # DB確認: 計画書(RehabilitationPlan)も自動作成されているか
    saved_plan = db_session.query(RehabilitationPlan).filter_by(patient_id=saved_patient.patient_id).first()
    assert saved_plan is not None


    # 保存成功のメッセージが表示されているか確認
    # (flashメッセージの内容や、遷移先画面のタイトルなどで判定)
    html = response.data.decode("utf-8")
    assert "成功" in html or "保存" in html

def test_edit_patient_info_existing(login_staff, app, db_session):
    """既存患者の編集ページ表示テスト"""
    # 1. データ準備
    patient = Patient(name="Existing Patient", gender="男性", date_of_birth=date(1950, 1, 1))
    db_session.add(patient)
    db_session.commit()

    # スタッフに割り当てないと見れない仕様の場合に備えて割り当て
    # (現在の実装では edit_patient_info 内で権限チェックがあるかによりますが、念のため)
    staff = db_session.query(Staff).filter_by(username="test_user").first()
    if staff:
        assign_patient_to_staff(staff.id, patient.patient_id)

    # 2. リクエスト
    with app.test_request_context():
        # クエリパラメータ patient_id を指定
        target_url = url_for('patient.edit_patient_info', patient_id=patient.patient_id)

    response = login_staff.get(target_url)
    assert response.status_code == 200

    # レスポンスに患者名が含まれているか確認
    assert "Existing Patient" in response.data.decode("utf-8")


def test_save_patient_info_update(login_staff, app, db_session):
    """既存患者情報の更新テスト"""
    # 1. データ準備
    patient = Patient(name="Update Target", gender="男性")
    db_session.add(patient)
    db_session.commit()

    with app.test_request_context():
        target_url = url_for('patient.save_patient_info')

    # 2. 更新データ (IDを指定)
    data = {
        "patient_id": str(patient.patient_id),
        "name": "Update Target", # 名前は変えずに
        "gender": "女性",       # 性別を変更してみる
        "age": "85",
    }

    response = login_staff.post(target_url, data=data, follow_redirects=True)
    assert response.status_code == 200

    # 3. DB確認
    # セッションをリフレッシュするか、再クエリして確認
    db_session.expire_all()
    updated_patient = db_session.query(Patient).filter_by(patient_id=patient.patient_id).first()
    assert updated_patient.gender == "女性"
