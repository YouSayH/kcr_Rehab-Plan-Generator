from flask import url_for


# 引数に 'app' を追加 (conftest.pyのappフィクスチャを受け取るため)
def test_edit_patient_info_route(login_staff, app):
    """患者情報編集ページへのアクセス"""

    # リクエストコンテキストを作成して url_for を有効化
    with app.test_request_context():
        target_url = url_for('patient.edit_patient_info')

    # クエリパラメータなしでアクセス
    response = login_staff.get(target_url)
    assert response.status_code == 200
    # テンプレート内の特徴的な文字列が含まれているか確認
    assert "患者" in response.data.decode("utf-8")

def test_save_patient_info_route(login_staff, app):
    """患者情報の保存処理（POST）"""

    with app.test_request_context():
        target_url = url_for('patient.save_patient_info')

    # データベースの定義に基づき、保存に必要なデータを揃える
    data = {
        # 新規登録時は patient_id を空にするか含めない
        "patient_id": "",
        "name": "テスト患者",      # 【必須】
        "name_kana": "テストカンジャ",
        "age": "80",              # 年齢 (内部計算で使用)
        "gender": "Male",         # 性別
        # チェックボックスの動作確認用
        "func_basic_rolling_level": "independent"
    }

    # follow_redirects=True で保存後のリダイレクト先まで追跡
    response = login_staff.post(target_url, data=data, follow_redirects=True)

    # エラーにならず完了するか
    assert response.status_code == 200

    # 保存成功のメッセージが表示されているか確認
    # (flashメッセージの内容や、遷移先画面のタイトルなどで判定)
    html = response.data.decode("utf-8")
    assert "成功" in html or "保存" in html
