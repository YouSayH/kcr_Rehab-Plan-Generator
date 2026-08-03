"""セキュリティヘッダとXSS対策の検証。

背景: 監査所見 add-09（セキュリティヘッダが1つも無い）、
fe-01（fim_history_json を | safe で <script> 内に生出力）。
"""

import json

import pytest
from flask import url_for

from app.models import Patient

# </script> で脱出してスクリプトを注入するペイロード
XSS_PAYLOAD = "</script><script>window.__pwned=1;</script>"


def test_security_headers_present(client):
    """主要なセキュリティヘッダが付与されていること。"""
    response = client.get("/login")

    assert "Content-Security-Policy" in response.headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "same-origin"


def test_csp_restricts_exfiltration_and_framing(client):
    """CSPが外部送信とクリックジャッキングを塞いでいること。

    インラインスクリプトが多いため 'unsafe-inline' は外せないが、
    connect-src と form-action を自オリジンに限定しておけば、
    スクリプトが実行されても患者情報の外部送信は防げる。
    """
    csp = client.get("/login").headers["Content-Security-Policy"]

    assert "connect-src 'self'" in csp
    assert "form-action 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "object-src 'none'" in csp


def test_fim_history_escapes_script_tag(login_staff, app, db_session, assign_patient):
    """計画書の自由記述に含まれる </script> がそのまま出力されないこと。

    fim_history は計画書の全カラムを含み、<script> 内に描画される。
    json.dumps は </script> をエスケープしないため、| safe で出力すると
    併存疾患欄などから任意のスクリプトを注入できる。
    """
    from app.crud import plan as plan_crud

    patient = Patient(name="XSS 検証", gender="女")
    db_session.add(patient)
    db_session.commit()
    assign_patient(patient)

    # FIMチャートは2件以上の履歴で描画されるため2件保存する
    for _ in range(2):
        plan_crud.save_new_plan(
            patient_id=patient.patient_id,
            staff_id=None,
            form_data={
                "main_comorbidities_txt": XSS_PAYLOAD,
                "adl_eating_fim_current_val": "6",
            },
        )

    with app.test_request_context():
        url = url_for("patient.edit_patient_info", patient_id=patient.patient_id)

    body = login_staff.get(url).data.decode("utf-8")

    assert "</script><script>window.__pwned=1;" not in body, (
        "スクリプト終了タグが生で出力されており、XSSが成立する"
    )
    # エスケープされた形では含まれていてよい（データとして保持されている）
    assert "window.__pwned" in body or "u003c" in body


def test_fim_chart_is_rendered_for_multiple_plans(login_staff, app, db_session, assign_patient):
    """計画書が2件以上ある患者でFIM推移グラフの描画先が出力されること。

    テンプレート側の出し分け条件とスクリプト側のデータが別々の変数を見ていると、
    canvas が出力されないままスクリプトだけが走り、
    getElementById('fimChart').getContext() が null 参照で落ちる。
    計画書1件の患者ではこの分岐に入らないため、必ず2件で確認する。
    """
    from app.crud import plan as plan_crud

    patient = Patient(name="FIMグラフ 検証", gender="男")
    db_session.add(patient)
    db_session.commit()
    assign_patient(patient)

    for value in ("4", "6"):
        plan_crud.save_new_plan(
            patient_id=patient.patient_id,
            staff_id=None,
            form_data={"adl_eating_fim_current_val": value},
        )

    with app.test_request_context():
        url = url_for("patient.edit_patient_info", patient_id=patient.patient_id)

    body = login_staff.get(url).data.decode("utf-8")

    assert 'id="fimChart"' in body, "FIM推移グラフのcanvasが出力されていない"
    assert 'id="fim-chart-select"' in body, "FIM項目の選択欄が出力されていない"


def test_app_logger_writes_to_stdout(app):
    """アプリのログが標準出力にも出ること。

    ファイルだけに出すと、docker compose logs にアプリのエラーが
    一切出なくなり、500の原因追跡ができなくなる。
    """
    import logging
    import sys

    handlers = logging.getLogger("app").handlers
    streams = [
        h for h in handlers
        if isinstance(h, logging.StreamHandler)
        and not isinstance(h, logging.FileHandler)
        and getattr(h, "stream", None) is sys.stdout
    ]

    assert streams, "標準出力へのハンドラが無い（docker logs にアプリログが出ない）"
    assert any(isinstance(h, logging.handlers.RotatingFileHandler) for h in handlers), (
        "ローテーション付きのファイルハンドラが無い"
    )


def test_model_choice_is_whitelisted(login_staff, app, db_session, assign_patient, mocker):
    """model_choice に想定外の値を渡しても、そのままJSに埋め込まれないこと。"""
    patient = Patient(name="モデル選択 検証", gender="男")
    db_session.add(patient)
    db_session.commit()
    assign_patient(patient)

    # AI生成は呼ばずにページだけ描画させる
    mocker.patch("app.crud.patient.get_patient_data_for_plan",
                 return_value={"patient_id": patient.patient_id, "name": "モデル選択 検証"})

    with app.test_request_context():
        url = url_for("plan.generate_plan")

    response = login_staff.post(url, data={
        "patient_id": str(patient.patient_id),
        "therapist_notes": "",
        "model_choice": '";window.__pwned=1;//',
    }, follow_redirects=True)

    body = response.data.decode("utf-8")
    assert '";window.__pwned=1;//' not in body, "不正な model_choice がJSへ生出力されている"
