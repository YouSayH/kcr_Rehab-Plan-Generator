import base64
import logging
import os

from flask import Response, flash, jsonify, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required

import app.services.excel.writer as excel_writer
import app.services.plan_service as plan_service

# アプリケーション内モジュール
from app.constants import ITEM_KEY_TO_JAPANESE
from app.core.database import SessionLocal  # 履歴取得クエリ用
from app.crud import patient as patient_crud
from app.crud import plan as plan_crud
from app.crud import staff as staff_crud
from app.models import RehabilitationPlan  # 履歴取得クエリ用
from app.services.rag_manager import DEFAULT_RAG_PIPELINE
from app.utils.helpers import has_permission_for_patient

# Blueprintのインポート
from . import plan_bp

logger = logging.getLogger(__name__)

@plan_bp.route("/")
@login_required
def index():
    """トップページ。担当患者のみ表示"""
    try:
        assigned_patients = staff_crud.get_assigned_patients(current_user.id)
        return render_template("index.html", patients=assigned_patients)
    except Exception as e:
        flash(f"データベース接続エラー: {e}", "danger")
        return render_template("index.html", patients=[])


@plan_bp.route("/generate_plan", methods=["POST"])
@login_required
def generate_plan():
    """AI生成の準備をし、確認・修正ページを直接表示する"""
    try:
        patient_id = int(request.form.get("patient_id"))
        therapist_notes = request.form.get("therapist_notes", "")
        model_choice = request.form.get("model_choice", "both")

        # 権限チェック
        if not has_permission_for_patient(current_user, patient_id):
            flash("権限がありません。", "danger")
            return redirect(url_for("plan.index"))

        # 患者の基本情報と「最新の」計画書データを取得
        patient_data = patient_crud.get_patient_data_for_plan(patient_id)
        if not patient_data:
            flash(f"ID:{patient_id}の患者データが見つかりません。", "warning")
            return redirect(url_for("plan.index"))

        # AI生成前のplanオブジェクトを作成
        general_plan = patient_data.copy()
        specialized_plan = {}

        # 編集可能なキーを取得 (Service層から定数を利用)
        editable_keys = plan_service.EDITABLE_KEYS

        for key in editable_keys:
            # general_plan と specialized_plan の両方に空文字を設定
            general_plan[key] = ""
            specialized_plan[key] = ""

        # 履歴ドロップダウン用に、全計画書のIDと作成日時を準備
        # ここはCRUD化せず、SessionLocalとモデルを使って直接クエリを実行
        session = SessionLocal()
        try:
            all_plans_query = (
                session.query(RehabilitationPlan.plan_id, RehabilitationPlan.created_at)
                .filter(RehabilitationPlan.patient_id == patient_id)
                .order_by(RehabilitationPlan.created_at.desc())
                .all()
            )
            plan_history = [{"plan_id": p.plan_id, "created_at": p.created_at} for p in all_plans_query if p.created_at]
        finally:
            session.close()

        return render_template(
            "confirm.html",
            patient_data=patient_data,
            general_plan=general_plan,
            specialized_plan=specialized_plan,
            therapist_notes=therapist_notes,
            is_generating=True,
            model_to_generate=model_choice,
            editable_keys=editable_keys,
            item_key_to_japanese=ITEM_KEY_TO_JAPANESE,
            default_rag_pipeline=DEFAULT_RAG_PIPELINE,
            plan_history=plan_history,
        )

    except (ValueError, TypeError):
        flash("有効な患者が選択されていません。", "warning")
        return redirect(url_for("plan.index"))
    except Exception as e:
        logger.error(f"Error during generate_plan: {e}")
        flash(f"ページの表示中にエラーが発生しました: {e}", "danger")
        return redirect(url_for("plan.index"))


@plan_bp.route("/save_plan", methods=["POST"])
@login_required
def save_plan():
    """計画の保存とダウンロードページへのリダイレクト"""
    try:
        patient_id = int(request.form.get("patient_id"))

        if not has_permission_for_patient(current_user, patient_id):
            flash("権限がありません。", "danger")
            return redirect(url_for("plan.index"))

        form_data = request.form.to_dict()

        # Service層へ委譲：保存ワークフローを実行し、生成されたファイル名を取得
        output_filename = plan_service.execute_save_workflow(
            staff_id=current_user.id,
            patient_id=patient_id,
            form_data=form_data
        )

        return render_template(
            "download_and_redirect.html",
            download_url=url_for("plan.download_file", filename=output_filename),
            redirect_url=url_for("plan.index"),
        )

    except Exception as e:
        logger.error(f"Error saving plan: {e}")
        flash(f"保存中にエラーが発生しました: {e}", "danger")
        return redirect(url_for("plan.index"))


@plan_bp.route("/api/preview_plan", methods=["POST"])
@login_required
def preview_plan():
    """計画書のプレビュー用HTMLを返すAPI (ExcelデータをBase64埋め込み)"""
    # テンプレートを返すため、APIという名前だがViewsに配置
    try:
        patient_id = int(request.form.get("patient_id"))

        if not has_permission_for_patient(current_user, patient_id):
            return Response("権限がありません。", status=403)

        form_data = request.form.to_dict()

        patient_data = patient_crud.get_patient_data_for_plan(patient_id)
        if not patient_data:
            return Response("患者データが見つかりません。", status=404)

        plan_data = patient_data.copy()
        plan_data.update(form_data)

        excel_bytes = excel_writer.create_plan_sheet(plan_data, return_bytes=True)
        b64_data = base64.b64encode(excel_bytes.read()).decode("utf-8")

        return render_template("preview_viewer.html", excel_base64=b64_data)

    except Exception as e:
        logger.error(f"Error generating preview: {e}")
        return Response(f"プレビュー生成エラー: {e}", status=500)


@plan_bp.route("/api/render_plan_history/<int:plan_id>")
@login_required
def render_plan_history(plan_id):
    """計画書の履歴表示用HTMLを返すAPI (サーバーサイドレンダリング)"""
    try:
        plan_data = plan_crud.get_plan_by_id(plan_id)
        if not plan_data:
             return jsonify({"error": "Plan not found"}), 404

        # 権限チェック
        if not has_permission_for_patient(current_user, plan_data["patient_id"]):
             return jsonify({"error": "Permission denied"}), 403

        response_format = request.args.get('format', 'html')

        if response_format == 'json':
            for key, value in plan_data.items():
                if hasattr(value, 'isoformat'):
                    plan_data[key] = value.isoformat()
            return jsonify(plan_data)
        else:
            return render_template('components/patient_info_ref.html', patient_data=plan_data)
    except Exception as e:
        logger.error(f"Error rendering plan history: {e}")
        return jsonify({"error": str(e)}), 500


@plan_bp.route("/view_plan/<int:plan_id>")
@login_required
def view_plan(plan_id):
    """特定の計画書を閲覧するページ"""
    try:
        plan_data = plan_crud.get_plan_by_id(plan_id)
        if not plan_data:
            flash("指定された計画書が見つかりません。", "danger")
            return redirect(url_for("plan.index"))

        patient_id = plan_data["patient_id"]
        if not has_permission_for_patient(current_user, patient_id):
            flash("この計画書を閲覧する権限がありません。", "danger")
            return redirect(url_for("plan.index"))

        return render_template("view_plan.html", plan=plan_data)
    except Exception as e:
        flash(f"計画書の読み込み中にエラーが発生しました: {e}", "danger")
        return redirect(url_for("plan.index"))


@plan_bp.route("/download/<path:filename>")
@login_required
def download_file(filename):
    """ファイルを安全にダウンロードさせる"""
    directory = os.path.abspath(excel_writer.OUTPUT_DIR)
    try:
        return send_from_directory(directory, filename, as_attachment=True)
    except FileNotFoundError:
        flash("ダウンロード対象のファイルが見つかりません。", "danger")
        return redirect(url_for("plan.index"))
