"""担当外の患者データへアクセスできないこと（IDOR対策）の検証。

背景: 監査所見 be-04。edit_patient_info / save_patient_info / like_suggestion /
download の4ルートで担当患者チェックが抜けており、担当が0人の職員でも
患者IDを変えるだけで氏名・生年月日・傷病名・FIM を閲覧でき、
POST すれば医療記録を改ざんできる状態だった。

ここでは「担当外なら拒否される」ことをルートごとに固定する。
正常系（担当患者なら通る）は各ルートの既存テストで担保している。
"""

import pytest
from flask import url_for

from app.models import Patient


@pytest.fixture
def other_patient(db_session):
    """ログイン中の職員(test_user)には割り当てられていない患者。"""
    patient = Patient(name="担当外 患者", gender="男")
    db_session.add(patient)
    db_session.commit()
    return patient


def test_edit_page_denies_unassigned_patient(login_staff, app, other_patient):
    """担当外の患者の編集ページを開けないこと。"""
    with app.test_request_context():
        url = url_for("patient.edit_patient_info", patient_id=other_patient.patient_id)

    response = login_staff.get(url, follow_redirects=False)

    assert response.status_code == 302, "担当外の患者ページが表示されてしまっている"


def test_edit_page_does_not_leak_patient_name(login_staff, app, other_patient):
    """拒否時に患者の氏名が漏れないこと。"""
    with app.test_request_context():
        url = url_for("patient.edit_patient_info", patient_id=other_patient.patient_id)

    response = login_staff.get(url, follow_redirects=True)

    assert "担当外 患者" not in response.data.decode("utf-8")


def test_save_denies_unassigned_patient(login_staff, app, db_session, other_patient):
    """担当外の患者情報を書き換えられないこと。"""
    with app.test_request_context():
        url = url_for("patient.save_patient_info")

    login_staff.post(url, data={
        "patient_id": str(other_patient.patient_id),
        "name": "改ざんされた名前",
        "gender": "女",
        "age": "70",
    }, follow_redirects=True)

    db_session.expire_all()
    reloaded = db_session.query(Patient).filter_by(patient_id=other_patient.patient_id).first()
    assert reloaded.name == "担当外 患者", "担当外の患者の医療記録が改ざんされた"


def test_like_suggestion_denies_unassigned_patient(login_staff, app, other_patient, mocker):
    """担当外の患者に対していいねを保存できないこと。"""
    mock_save = mocker.patch("app.crud.plan.save_suggestion_like")

    with app.test_request_context():
        url = url_for("plan.like_suggestion")

    response = login_staff.post(url, json={
        "patient_id": other_patient.patient_id,
        "item_key": "main_risks_txt",
        "liked_model": "general",
    })

    assert response.status_code == 403
    mock_save.assert_not_called()


def test_patient_list_excludes_unassigned_patients(login_staff, app, db_session, other_patient, assign_patient):
    """編集ページの患者プルダウンに担当外の患者が出ないこと。

    担当外の患者IDが分かると、それを手掛かりに他ルートへアクセスされる。
    """
    mine = Patient(name="担当 患者", gender="女")
    db_session.add(mine)
    db_session.commit()
    assign_patient(mine)

    with app.test_request_context():
        url = url_for("patient.edit_patient_info")

    body = login_staff.get(url).data.decode("utf-8")

    assert "担当 患者" in body, "自分の担当患者が一覧に出ていない"
    assert "担当外 患者" not in body, "担当外の患者が一覧に漏れている"


def test_save_rejects_mismatched_patient_id_sources(
    login_staff, app, db_session, other_patient, assign_patient
):
    """クエリ文字列とフォーム本文で patient_id を食い違わせても迂回できないこと。

    ガードが「最初に見つけた1件」で判定を打ち切ると、クエリに自分の担当患者ID、
    フォーム本文に担当外の患者IDを入れるだけで認可を通過できてしまう。
    save_patient_info が実際に読むのは request.form の方である。
    """
    mine = Patient(name="担当 患者", gender="女")
    db_session.add(mine)
    db_session.commit()
    assign_patient(mine)

    with app.test_request_context():
        url = url_for("patient.save_patient_info", patient_id=mine.patient_id)

    login_staff.post(url, data={
        "patient_id": str(other_patient.patient_id),  # 本文には担当外のID
        "name": "改ざんされた名前",
        "gender": "女",
        "age": "70",
    }, follow_redirects=True)

    db_session.expire_all()
    reloaded = db_session.query(Patient).filter_by(patient_id=other_patient.patient_id).first()
    assert reloaded.name == "担当外 患者", "クエリ文字列で認可を迂回され、担当外の記録が改ざんされた"


def test_like_rejects_mismatched_patient_id_sources(
    login_staff, app, db_session, other_patient, assign_patient, mocker
):
    """クエリ文字列とJSONボディで patient_id を食い違わせても迂回できないこと。"""
    mine = Patient(name="担当 患者", gender="女")
    db_session.add(mine)
    db_session.commit()
    assign_patient(mine)

    mock_save = mocker.patch("app.crud.plan.save_suggestion_like")

    with app.test_request_context():
        url = url_for("plan.like_suggestion", patient_id=mine.patient_id)

    response = login_staff.post(url, json={
        "patient_id": other_patient.patient_id,  # 本文には担当外のID
        "item_key": "main_risks_txt",
        "liked_model": "general",
    })

    assert response.status_code == 403
    mock_save.assert_not_called()


def test_newly_created_patient_is_reachable_by_creator(login_staff, app):
    """新規登録した患者を、登録した本人が開けること。

    新規患者は誰の担当にもならないため、登録直後のリダイレクト先で
    作成者自身がアクセス権限チェックに弾かれ、患者一覧にも出ないので
    二度と辿り着けなくなる、という事故が起きやすい箇所。
    """
    with app.test_request_context():
        save_url = url_for("patient.save_patient_info")

    response = login_staff.post(save_url, data={
        "name": "新規登録 太郎",
        "gender": "男",
        "age": "72",
    }, follow_redirects=True)

    assert response.status_code == 200
    body = response.data.decode("utf-8")
    assert "新規登録 太郎" in body, "登録した患者を作成者自身が開けない"


def test_non_numeric_patient_id_is_rejected(login_staff, app):
    """patient_id に数値以外を渡しても素通りしないこと。"""
    with app.test_request_context():
        url = url_for("plan.like_suggestion")

    response = login_staff.post(url, json={
        "patient_id": "1 OR 1=1",
        "item_key": "main_risks_txt",
        "liked_model": "general",
    })

    assert response.status_code == 403
