import base64
from datetime import datetime
from io import BytesIO

from flask import url_for

from app.services.excel import writer

# conftest.py の login_staff fixture を利用する
# login_staff はログイン済みの client を返します

def test_preview_plan_api(login_staff, monkeypatch, app): # 【修正】appフィクスチャを追加
    """
    【API】/api/preview_plan が Luckysheet 用の Base64 文字列を含んだHTMLを返すか
    """
    client = login_staff

    # --- モックの準備 ---

    # 1. 権限チェックをパスさせる
    monkeypatch.setattr("app.routers.plan.views.has_permission_for_patient", lambda user, pid: True)

    # 2. 患者データ取得をモック化 (DBにデータがなくても辞書を返す)
    dummy_patient_data = {"name": "Preview Taro", "gender": "男"}
    monkeypatch.setattr("app.crud.patient.get_patient_data_for_plan", lambda pid: dummy_patient_data)

    # 3. Excel生成をモック化 (テンプレート依存を避けるため、適当なバイト列を返す)
    from io import BytesIO
    mock_output = BytesIO(b"fake_excel_binary_data")
    monkeypatch.setattr("app.services.excel.writer.create_plan_sheet", lambda *args, **kwargs: mock_output)

    # --- テスト実行 ---

    # フォームデータ送信
    form_data = {
        "patient_id": 1,
        "name": "Updated Name",
    }

    # 【修正】リクエストコンテキスト内で url_for を実行
    with app.test_request_context():
        target_url = url_for('plan.preview_plan')

    response = client.post(target_url, data=form_data)

    assert response.status_code == 200
    html_content = response.data.decode('utf-8')

    # --- 検証 ---

    assert "transform" in html_content or "luckyexcel" in html_content

    expected_b64 = base64.b64encode(b"fake_excel_binary_data").decode("utf-8")
    assert expected_b64 in html_content


def test_save_and_download_flow(login_staff, monkeypatch, app):
    """
    【遷移】保存処理 -> ダウンロード画面 -> 実際のファイルダウンロード の流れ

    ダウンロードはファイル名ではなく plan_id で受け取り、その場でExcelを
    生成して返す（ディスクに患者情報のExcelを残さないため）。
    """
    client = login_staff
    plan_id = 42

    # --- モックの準備 ---

    # 1. 権限チェックパス
    monkeypatch.setattr("app.routers.plan.views.has_permission_for_patient", lambda user, pid: True)

    # 2. 保存ワークフローのモック (plan_id を返す)
    monkeypatch.setattr("app.services.plan_service.execute_save_workflow", lambda *args, **kwargs: plan_id)

    # --- 保存処理のテスト ---

    with app.test_request_context():
        save_url = url_for('plan.save_plan')
        expected_download_url = url_for('plan.download_file', plan_id=plan_id)

    response_save = client.post(save_url, data={
        "patient_id": 1,
        "name": "Save Test"
    })

    assert response_save.status_code == 200
    # ダウンロード画面が plan_id 経由のURLを案内していること
    assert expected_download_url in response_save.data.decode('utf-8')

    # --- ダウンロード処理のテスト ---

    monkeypatch.setattr(
        "app.crud.plan.get_plan_by_id",
        lambda pid: {"plan_id": pid, "patient_id": 1, "created_at": datetime(2026, 7, 23, 10, 30, 0)},
    )
    monkeypatch.setattr(
        writer, "create_plan_sheet", lambda plan_data, return_bytes=False: BytesIO(b"fake excel content")
    )

    response_download = client.get(expected_download_url)

    assert response_download.status_code == 200
    disposition = response_download.headers.get("Content-Disposition", "")
    assert "attachment" in disposition
    # ファイル名に患者名を含めない（推測でのアクセスを避けるため）
    assert f"RehabPlan_{plan_id}_20260723_103000.xlsx" in disposition
    assert response_download.data == b"fake excel content"


def test_download_denied_for_unassigned_patient(login_staff, monkeypatch, app):
    """担当外の患者の計画書はダウンロードできないこと。"""
    client = login_staff

    monkeypatch.setattr(
        "app.crud.plan.get_plan_by_id",
        lambda pid: {"plan_id": pid, "patient_id": 999, "created_at": datetime(2026, 7, 23)},
    )
    # 例外を投げて検知するのは不可。download_file の Excel 生成は
    # `except Exception` で囲まれており、AssertionError も握り潰されて
    # 「リダイレクトされた」ように見えてしまう。呼び出しの記録で判定する。
    called = []
    monkeypatch.setattr(
        writer, "create_plan_sheet",
        lambda *a, **kw: called.append(True) or BytesIO(b"leaked"),
    )

    with app.test_request_context():
        download_url = url_for('plan.download_file', plan_id=1)

    response = client.get(download_url, follow_redirects=False)

    assert not called, "権限が無いのにExcelが生成された"
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    assert "attachment" not in response.headers.get("Content-Disposition", "")
    assert b"leaked" not in response.data
