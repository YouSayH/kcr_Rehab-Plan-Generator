from flask import url_for

from app.crud.staff import assign_patient_to_staff
from app.models import Patient, Staff


def test_generate_general_stream_api(login_staff, app, db_session, mocker):
    """
    汎用モデル生成API (/api/generate/general) のテスト
    正しい関数名 (generate_general_plan_stream) を呼んでいるか検証する
    """
    # 1. データ準備
    patient = Patient(name="API Test Patient", gender="男性")
    db_session.add(patient)
    db_session.commit()

    staff = db_session.query(Staff).filter_by(username="test_user").first()
    assign_patient_to_staff(staff.id, patient.patient_id)

    # 2. モックの設定
    # autospec=True にすることで、実在しない関数を呼ぼうとすると AttributeError になる
    mock_gemini = mocker.patch("app.routers.plan.api.gemini_client", autospec=True)

    # ストリーミングレスポンス用のイテレータを返すように設定
    def mock_stream_generator(*args, **kwargs):
        yield "event: update\ndata: {}\n\n"
        yield "event: general_finished\ndata: {}\n\n"

    # 正しい関数名に対して戻り値を設定
    mock_gemini.generate_general_plan_stream.return_value = mock_stream_generator()

    # 3. リクエスト実行
    with app.test_request_context():
        target_url = url_for('plan.generate_general_stream', patient_id=patient.patient_id)

    response = login_staff.get(target_url)

    # 4. 検証
    # もし api.py が間違った関数名 (generate_plan_streamなど) を呼んでいたら、
    # ここで 500 エラー (AttributeError) になっているはず
    assert response.status_code == 200
    assert response.mimetype == "text/event-stream"

    # 正しい関数が、意図した引数で呼ばれたか確認
    mock_gemini.generate_general_plan_stream.assert_called_once()

    # 誤って旧関数などを呼んでいないか確認（autospec=Trueなら呼んだ時点で落ちるが念のため）
    # assert not mock_gemini.generate_plan_stream.called  # 存在しない属性なのでアクセスするだけでエラーになる


def test_generate_rag_stream_api(login_staff, app, db_session, mocker):
    """
    RAG生成API (/api/generate/rag/...) のテスト
    """
    # 1. データ準備
    patient = Patient(name="RAG Test Patient", gender="女性")
    db_session.add(patient)
    db_session.commit()

    staff = db_session.query(Staff).filter_by(username="test_user").first()
    assign_patient_to_staff(staff.id, patient.patient_id)

    # 2. モックの設定
    mock_gemini = mocker.patch("app.routers.plan.api.gemini_client", autospec=True)

    # RAG Executorの取得部分もモックする（重い処理を避けるため）
    mock_get_executor = mocker.patch("app.routers.plan.api.get_rag_executor")
    mock_executor_instance = mocker.Mock() # ダミーのExecutor
    mock_get_executor.return_value = mock_executor_instance

    # ストリーミングのモック
    def mock_rag_stream(*args, **kwargs):
        yield "event: update\ndata: {}\n\n"
        yield "event: finished\ndata: {}\n\n"

    mock_gemini.generate_rag_plan_stream.return_value = mock_rag_stream()

    # 3. リクエスト実行
    pipeline_name = "default_pipeline"
    with app.test_request_context():
        target_url = url_for('plan.generate_rag_stream', pipeline_name=pipeline_name, patient_id=patient.patient_id)

    response = login_staff.get(target_url)

    # 4. 検証
    assert response.status_code == 200
    assert response.mimetype == "text/event-stream"

    # 正しい関数が呼ばれたか
    mock_gemini.generate_rag_plan_stream.assert_called_once()

    # 引数に RAG executor が渡されているか確認
    call_args = mock_gemini.generate_rag_plan_stream.call_args
    assert call_args.kwargs['rag_executor'] == mock_executor_instance


def test_like_suggestion_api(login_staff, app, db_session, mocker):
    """いいねAPI (/like_suggestion) のテスト"""
    # 1. データ準備
    patient = Patient(name="Like Test Patient", gender="女性")
    db_session.add(patient)
    db_session.commit()
    staff = db_session.query(Staff).filter_by(username="test_user").first()

    # モック: plan_crud.save_suggestion_like をモックしてDB書き込みを確認
    mock_save_like = mocker.patch("app.crud.plan.save_suggestion_like")

    with app.test_request_context():
        target_url = url_for('plan.like_suggestion')

    # 2. POST実行 (いいね保存)
    data = {
        "patient_id": patient.patient_id,
        "item_key": "goal_test",
        "liked_model": "gemini"
    }
    response = login_staff.post(target_url, json=data)

    assert response.status_code == 200
    assert response.json["status"] == "success"

    # モックが正しい引数で呼ばれたか
    mock_save_like.assert_called_once_with(
        patient_id=patient.patient_id,
        item_key="goal_test",
        liked_model="gemini",
        staff_id=staff.id
    )
