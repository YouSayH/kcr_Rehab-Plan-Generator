import json
import logging

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import text

# 自作のPythonファイルをインポート
import app.core.database as database
from app.services.rag_manager import patient_info_parser

# Blueprint作成
patient_bp = Blueprint('patient', __name__)
logger = logging.getLogger(__name__)

@patient_bp.route("/edit_patient_info", methods=["GET"])
@login_required
def edit_patient_info():
    """患者の事実情報（マスターデータ）を追加・編集するページを表示"""
    patient_data = {}
    plan_history = []
    fim_history_json = None
    all_patients = []
    current_patient_id = request.args.get("patient_id", type=int)

    session = database.SessionLocal()

    try:
        # プルダウン用に全患者のリストを取得
        all_patients_result = session.execute(text("SELECT patient_id, name FROM patients ORDER BY name"))
        all_patients = all_patients_result.mappings().all()

        if current_patient_id:
            # --- データ取得ロジックをORMに統一 ---
            # 1. 最新7件の計画書データをORMオブジェクトとして取得
            latest_plans = (
                session.query(database.RehabilitationPlan)
                .filter(database.RehabilitationPlan.patient_id == current_patient_id)
                .order_by(database.RehabilitationPlan.created_at.desc())
                .limit(7)
                .all()
            )

            # 2. 取得したデータを使ってフォーム表示とグラフ表示のデータを準備
            if latest_plans:
                # フォーム表示用に、最新の1件の計画書から患者データを構築
                latest_plan_obj = latest_plans[0]
                patient_obj = latest_plan_obj.patient

                # PatientオブジェクトとRehabilitationPlanオブジェクトから辞書を作成して結合
                patient_dict = {c.name: getattr(patient_obj, c.name) for c in patient_obj.__table__.columns}
                patient_dict["age"] = patient_obj.age  # ageプロパティを追加
                plan_dict = {c.name: getattr(latest_plan_obj, c.name) for c in latest_plan_obj.__table__.columns}
                patient_data = {**patient_dict, **plan_dict}

                # グラフ用に、古い→新しい順に並べ替えてJSON化
                fim_history_for_chart = [
                    {c.name: getattr(p, c.name) for c in p.__table__.columns}
                    for p in reversed(latest_plans)  # 古い順に並べ替え
                ]
                fim_history_json = json.dumps(fim_history_for_chart, default=str)

                # 履歴ドロップダウン用に、全計画書のIDと作成日時を準備
                all_plans_query = (
                    session.query(database.RehabilitationPlan.plan_id, database.RehabilitationPlan.created_at)
                    .filter(database.RehabilitationPlan.patient_id == current_patient_id)
                    .order_by(database.RehabilitationPlan.created_at.desc())
                    .all()
                )
                plan_history = [{"plan_id": p.plan_id, "created_at": p.created_at} for p in all_plans_query if p.created_at]

            else:
                # 計画書が1件もない場合 (新規患者など)
                patient_obj = session.query(database.Patient).filter(database.Patient.patient_id == current_patient_id).first()
                if patient_obj:
                    patient_data = {c.name: getattr(patient_obj, c.name) for c in patient_obj.__table__.columns}
                    patient_data["age"] = patient_obj.age
                else:
                    flash(f"ID:{current_patient_id}の患者データが見つかりません。", "warning")

    except Exception:
        flash("無効な患者IDです。", "danger")
    finally:
        session.close()

    return render_template(
        "edit_patient_info.html",
        all_patients=all_patients,
        patient_data=patient_data,
        plan_history=plan_history,
        current_patient_id=current_patient_id,
        fim_history_json=fim_history_json,  # グラフ用データをテンプレートに渡す
    )


@patient_bp.route("/save_patient_info", methods=["POST"])
@login_required
def save_patient_info():
    """患者の事実情報をデータベースに保存（新規作成または更新）"""
    try:
        form_data = request.form.to_dict()

        # nameとvalueのプレフィックスから、対応するチェックボックス名を生成する辞書
        RADIO_GROUP_MAP = {
            "func_basic_rolling_level": "func_basic_rolling_",
            "func_basic_sitting_balance_level": "func_basic_sitting_balance_",
            "func_basic_getting_up_level": "func_basic_getting_up_",
            "func_basic_standing_balance_level": "func_basic_standing_balance_",
            "func_basic_standing_up_level": "func_basic_standing_up_",
            "social_care_level_support_num_slct": "social_care_level_support_num",
            "social_care_level_care_num_slct": "social_care_level_care_num",
            "goal_p_schooling_status_slct": "goal_p_schooling_status_",
            "goal_a_bed_mobility_level": "goal_a_bed_mobility_",
            "goal_a_indoor_mobility_level": "goal_a_indoor_mobility_",
            "goal_a_outdoor_mobility_level": "goal_a_outdoor_mobility_",
            "goal_a_driving_level": "goal_a_driving_",
            "goal_a_transport_level": "goal_a_public_transport_",
            "goal_a_toileting_level": "goal_a_toileting_",
            "goal_a_eating_level": "goal_a_eating_",
            "goal_a_grooming_level": "goal_a_grooming_",
            "goal_a_dressing_level": "goal_a_dressing_",
            "goal_a_bathing_level": "goal_a_bathing_",
            "goal_a_housework_level": "goal_a_housework_meal_",
            "goal_a_writing_level": "goal_a_writing_",
            "goal_a_ict_level": "goal_a_ict_",
            "goal_a_communication_level": "goal_a_communication_",
            "goal_p_return_to_work_status_slct": "goal_p_return_to_work_status_",
            "func_circulatory_arrhythmia_status_slct": "func_circulatory_arrhythmia_status_",
        }
        # フォームデータを直接変更するのではなく、追加のデータを保持する辞書を作成
        additional_data = {}

        for group_name, prefix in RADIO_GROUP_MAP.items():
            if group_name in form_data and form_data[group_name]:
                value = form_data[group_name]

                # 例: social_care_level_support_num_slct の値が '1' の場合
                if group_name in ["social_care_level_support_num_slct", "social_care_level_care_num_slct"]:
                    # social_care_level_support_num1_slct = 'on' を生成
                    target_key = f"{prefix}{value}_slct"
                # 例: goal_a_writing_level の値が 'independent_after_hand_change' の場合
                elif value == "independent_after_hand_change":
                    # goal_a_writing_independent_after_hand_change_chk = 'on' を生成
                    target_key = f"{prefix}independent_after_hand_change_chk"
                # 例: func_basic_rolling_level の値が 'partial_assist' の場合
                elif value == "partial_assist":
                    # func_basic_rolling_partial_assistance_chk = 'on' を生成
                    target_key = f"{prefix}partial_assistance_chk"
                # 例: goal_a_toileting_level の値が 'assist' の場合
                elif value == "assist":
                    # goal_a_toileting_assistance_chk = 'on' を生成
                    target_key = f"{prefix}assistance_chk"
                # 'yes'/'no' のような新しい形式に対応
                elif value in ["yes", "no"]:
                    # func_circulatory_arrhythmia_status_yes_chk のようなキーは存在しないため、この場合は何もしない
                    continue
                # その他の一般的な値 (independent, not_performed など)
                else:
                    # func_basic_rolling_independent_chk = 'on' などを生成
                    target_key = f"{prefix}{value}_chk"

                additional_data[target_key] = "on"

        # 元のフォームデータに、変換して生成したデータを追加
        form_data.update(additional_data)

        # データベースに保存処理を実行
        saved_patient_id = database.save_patient_master_data(form_data)

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
