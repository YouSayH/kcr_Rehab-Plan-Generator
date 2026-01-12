import base64

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


def test_save_and_download_flow(login_staff, monkeypatch, tmp_path, app): # 【修正】appフィクスチャを追加
    """
    【遷移】保存処理 -> ダウンロード画面 -> 実際のファイルダウンロード の流れ
    """
    client = login_staff

    # --- モックの準備 ---

    # 1. 権限チェックパス
    monkeypatch.setattr("app.routers.plan.views.has_permission_for_patient", lambda user, pid: True)

    # 2. 保存ワークフローのモック (ファイル名だけ返す)
    expected_filename = "RehabPlan_Test_2025.xlsx"
    monkeypatch.setattr("app.services.plan_service.execute_save_workflow", lambda *args, **kwargs: expected_filename)

    # --- 保存処理のテスト ---

    # 【修正】リクエストコンテキスト内で url_for を実行
    with app.test_request_context():
        save_url = url_for('plan.save_plan')

    response_save = client.post(save_url, data={
        "patient_id": 1,
        "name": "Save Test"
    })

    assert response_save.status_code == 200
    assert expected_filename in response_save.data.decode('utf-8')

    # --- ダウンロード処理のテスト ---

    # 一時ファイル作成
    mock_output_dir = tmp_path / "output"
    mock_output_dir.mkdir()
    (mock_output_dir / expected_filename).write_text("fake excel content")

    monkeypatch.setattr(writer, "OUTPUT_DIR", str(mock_output_dir))

    # 【修正】リクエストコンテキスト内で url_for を実行
    with app.test_request_context():
        download_url = url_for('plan.download_file', filename=expected_filename)

    response_download = client.get(download_url)

    assert response_download.status_code == 200
    assert "attachment" in response_download.headers.get("Content-Disposition", "")
    assert expected_filename in response_download.headers.get("Content-Disposition", "")
