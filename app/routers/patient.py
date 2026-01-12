import logging

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

# 自作のPythonファイルをインポート
from app.crud import patient as patient_crud
from app.services import patient_service  # 新規サービスのインポート
from app.services.rag_manager import patient_info_parser

# Blueprint作成
patient_bp = Blueprint('patient', __name__)
logger = logging.getLogger(__name__)

@patient_bp.route("/edit_patient_info", methods=["GET"])
@login_required
def edit_patient_info():
    """患者の事実情報（マスターデータ）を追加・編集するページを表示"""
    current_patient_id = request.args.get("patient_id", type=int)

    # サービス層へ処理を委譲
    data = patient_service.prepare_edit_page_data(current_patient_id)

    if data.get("error_message"):
        flash(data["error_message"], "danger")

    return render_template(
        "edit_patient_info.html",
        all_patients=data.get("all_patients", []),
        patient_data=data.get("patient_data", {}),
        plan_history=data.get("plan_history", []),
        current_patient_id=current_patient_id,
        fim_history_json=data.get("fim_history_json"),
    )


@patient_bp.route("/save_patient_info", methods=["POST"])
@login_required
def save_patient_info():
    """患者の事実情報をデータベースに保存（新規作成または更新）"""
    try:
        form_data = request.form.to_dict()

        # サービス層でフォームデータの正規化を実行
        form_data = patient_service.normalize_form_data(form_data)

        # データベースに保存処理を実行
        saved_patient_id = patient_crud.save_patient_master_data(form_data)

        flash("患者情報を正常に保存しました。", "success")
        # 保存後、今編集していた患者が選択された状態で同ページにリダイレクト
        return redirect(url_for("patient.edit_patient_info", patient_id=saved_patient_id))

    except Exception as e:
        logger.error(f"save_patient_info でエラー: {e}")
        flash(
            "情報の保存中にエラーが発生しました。システム管理者にご確認ください。", "danger"
        )
        return redirect(url_for("patient.edit_patient_info"))


@patient_bp.route("/api/parse-patient-info", methods=["POST"])
@login_required
def api_parse_patient_info():
    """カルテテキストを解析して構造化された患者情報を返すAPI"""
    if not patient_info_parser:
        return jsonify({"error": "サーバー側でパーサーが初期化されていません。"}), 500

    data = request.get_json()
    if not data or "text" not in data or not data["text"].strip():
        return jsonify({"error": "解析対象のテキストがありません。"}), 400

    try:
        text_to_parse = data["text"]
        parsed_data = patient_info_parser.parse_text(text_to_parse)
        return jsonify(parsed_data)
    except Exception as e:
        logger.error(f"Error during parsing patient info: {e}")
        return jsonify({"error": "解析中にサーバーでエラーが発生しました。", "details": str(e)}), 500
