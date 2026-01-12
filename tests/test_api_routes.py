from unittest.mock import MagicMock

from flask import url_for

from app.crud.staff import assign_patient_to_staff
from app.models import Patient, Staff


def test_generate_general_stream_api(login_staff, app, db_session, mocker):
    """
    汎用モデル生成API (/api/generate/general) のテスト
    get_llm_client が返すクライアントの generate_plan_stream が呼ばれるかを検証
    """
    # 1. データ準備
    patient = Patient(name="API Test Patient", gender="男性")
    db_session.add(patient)
    db_session.commit()

    staff = db_session.query(Staff).filter_by(username="test_user").first()
    assign_patient_to_staff(staff.id, patient.patient_id)

    # 2. モックの設定
    # get_llm_client をモックし、それが返すクライアントインスタンスもモックする
    mock_get_client = mocker.patch("app.routers.plan.api.get_llm_client")
    mock_client_instance = MagicMock()
    mock_get_client.return_value = mock_client_instance

    # ストリーミングレスポンス用のイテレータを返すように設定
    def mock_stream_generator(*args, **kwargs):
        yield "event: update\ndata: {}\n\n"
        yield "event: general_finished\ndata: {}\n\n"

    mock_client_instance.generate_plan_stream.return_value = mock_stream_generator()

    # 3. GET実行
    with app.test_request_context():
        target_url = url_for('plan.generate_general_stream', patient_id=patient.patient_id)

    response = login_staff.get(target_url)

    # 4. 検証
    # もし api.py が間違った関数名 (generate_plan_streamなど) を呼んでいたら、
    # ここで 500 エラー (AttributeError) になっているはず
    assert response.status_code == 200
    assert response.mimetype == "text/event-stream"

    # 正しいメソッドが呼ばれたか
    mock_client_instance.generate_plan_stream.assert_called_once()


def test_generate_rag_stream_api(login_staff, app, db_session, mocker):
    """
    RAG生成API (/api/generate/rag/...) のテスト
    get_llm_client が返すクライアントの generate_rag_plan_stream が呼ばれるかを検証
    """
    # 1. データ準備
    patient = Patient(name="RAG Test Patient", gender="女性")
    db_session.add(patient)
    db_session.commit()

    staff = db_session.query(Staff).filter_by(username="test_user").first()
    assign_patient_to_staff(staff.id, patient.patient_id)

    # 2. モックの設定
    # get_rag_executor のモック
    mock_get_executor = mocker.patch("app.routers.plan.api.get_rag_executor")
    mock_executor_instance = MagicMock()
    mock_get_executor.return_value = mock_executor_instance

    # get_llm_client のモック
    mock_get_client = mocker.patch("app.routers.plan.api.get_llm_client")
    mock_client_instance = MagicMock()
    mock_get_client.return_value = mock_client_instance

    def mock_stream_generator(*args, **kwargs):
        yield "event: update\ndata: {}\n\n"
        yield "event: finished\ndata: {}\n\n"

    mock_client_instance.generate_rag_plan_stream.return_value = mock_stream_generator()

    # 3. GET実行
    with app.test_request_context():
        target_url = url_for('plan.generate_rag_stream', pipeline_name="test_pipeline", patient_id=patient.patient_id)

    response = login_staff.get(target_url)

    # 4. 検証
    assert response.status_code == 200
    assert response.mimetype == "text/event-stream"

    # 正しいメソッドが呼ばれたか
    mock_client_instance.generate_rag_plan_stream.assert_called_once()

    # 引数に RAG executor が渡されているか確認
    call_args = mock_client_instance.generate_rag_plan_stream.call_args
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
        "item_key": "main_risks_txt",
        "liked_model": "general"
    }
    response = login_staff.post(target_url, json=data)

    # 3. 検証
    assert response.status_code == 200
    assert response.json["status"] == "success"

    # モックが正しい引数で呼ばれたか
    mock_save_like.assert_called_once_with(
        patient_id=patient.patient_id,
        item_key="main_risks_txt",
        liked_model="general",
        staff_id=staff.id
    )

    # 4. POST実行 (いいね削除)
    mock_delete_like = mocker.patch("app.crud.plan.delete_suggestion_like")
    data_delete = {
        "patient_id": patient.patient_id,
        "item_key": "main_risks_txt",
        "model_to_delete": "general"
    }
    response_del = login_staff.post(target_url, json=data_delete)

    assert response_del.status_code == 200
    mock_delete_like.assert_called_once()
