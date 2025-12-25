import base64
import json
import logging
import os

from flask import (
    Blueprint,
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import (
    current_user,
    login_required,
)

# 自作のPythonファイルをインポート
import app.core.database as database
import app.services.excel_writer as excel_writer
import app.services.llm.gemini_client as gemini_client
import app.services.llm.ollama_client as ollama_client
from app.constants import ITEM_KEY_TO_JAPANESE
from app.services.rag_manager import (
    DEFAULT_RAG_PIPELINE,
    LLM_CLIENT_TYPE,
    get_rag_executor,
)
from app.utils.helpers import get_plan_checked, has_permission_for_patient

# Blueprint作成
plan_bp = Blueprint('plan', __name__)

log_directory = "logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)
log_file_path = os.path.join(log_directory, "gemini_prompts.log")

# ロガーの設定 (app.py専用のロガーインスタンスを取得)
logger = logging.getLogger(__name__)
if not logger.hasHandlers():  # ハンドラが未設定の場合のみ設定
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

@plan_bp.route("/")
@login_required
def index():
    """トップページ。担当患者のみ表示"""
    try:
        assigned_patients = database.get_assigned_patients(current_user.id)
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
        print(f"こっちはジェネレートプラン無印　DEBUG [app.py]: therapist_notes from URL = '{therapist_notes[:100]}...'")

        # 権限チェック
        if not has_permission_for_patient(current_user, patient_id):
            flash("権限がありません。", "danger")
            return redirect(url_for("plan.index"))

        # 患者の基本情報と「最新の」計画書データを取得
        patient_data = database.get_patient_data_for_plan(patient_id)
        if not patient_data:
            flash(f"ID:{patient_id}の患者データが見つかりません。", "warning")
            return redirect(url_for("plan.index"))

        # AI生成前のplanオブジェクトを作成 (AI生成項目は空にしておく)
        general_plan = patient_data.copy()
        specialized_plan = {}

        editable_keys = [
            "main_risks_txt",
            "main_contraindications_txt",
            "func_pain_txt",
            "func_rom_limitation_txt",
            "func_muscle_weakness_txt",
            "func_swallowing_disorder_txt",
            "func_behavioral_psychiatric_disorder_txt",
            "cs_motor_details",
            "func_nutritional_disorder_txt",
            "func_excretory_disorder_txt",
            "func_pressure_ulcer_txt",
            "func_contracture_deformity_txt",
            "func_motor_muscle_tone_abnormality_txt",
            "func_disorientation_txt",
            "func_memory_disorder_txt",
            "adl_equipment_and_assistance_details_txt",
            "goals_1_month_txt",
            "goals_at_discharge_txt",
            "policy_treatment_txt",
            "policy_content_txt",
            "goal_p_action_plan_txt",
            "goal_a_action_plan_txt",
            "goal_s_psychological_action_plan_txt",
            "goal_s_env_action_plan_txt",
            "goal_s_3rd_party_action_plan_txt",
        ]
        for key in editable_keys:
            # general_plan と specialized_plan の両方に空文字を設定
            general_plan[key] = ""
            specialized_plan[key] = ""  # 仮テキストを削除

        # 履歴ドロップダウン用に、全計画書のIDと作成日時を準備
        session = database.SessionLocal()
        try:
            all_plans_query = (
                session.query(database.RehabilitationPlan.plan_id, database.RehabilitationPlan.created_at)
                .filter(database.RehabilitationPlan.patient_id == patient_id)
                .order_by(database.RehabilitationPlan.created_at.desc())
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
            therapist_notes=therapist_notes,  # 独立して渡す
            is_generating=True,  # JavaScriptで生成処理をキックするためのフラグ
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


@plan_bp.route("/api/render_plan_history/<int:plan_id>")
@login_required
def render_plan_history(plan_id):
    """計画書の履歴表示用HTMLを返すAPI (サーバーサイドレンダリング)"""
    try:
        try:
            plan_data = get_plan_checked(plan_id, current_user)
        except ValueError:
             return jsonify({"error": "Plan not found"}), 404
        except PermissionError:
             return jsonify({"error": "Permission denied"}), 403

        # フォーマット指定を確認 (?format=json)
        response_format = request.args.get('format', 'html')

        if response_format == 'json':
            # JSON形式で返却する場合（特定の項目だけ使いたい、グラフを作りたい等）
            # datetimeオブジェクトを文字列に変換
            for key, value in plan_data.items():
                if hasattr(value, 'isoformat'):
                    plan_data[key] = value.isoformat()
            return jsonify(plan_data)
        else:
            # デフォルト: 既存のテンプレートを再利用してHTMLを生成
            return render_template('components/patient_info_ref.html', patient_data=plan_data)
    except Exception as e:
        logger.error(f"Error rendering plan history: {e}")
        return jsonify({"error": str(e)}), 500


@plan_bp.route("/api/generate/general")
@login_required
def generate_general_stream():
    """Gemini単体モデルによる計画案をストリーミングで生成するAPI"""
    try:
        # URLのクエリパラメータから患者IDと所見を取得
        patient_id = int(request.args.get("patient_id"))
        therapist_notes = request.args.get("therapist_notes", "")

        # 権限チェック：ログイン中のユーザーが担当する患者か確認
        if not has_permission_for_patient(current_user, patient_id):
            return Response("権限がありません。", status=403)

        # データベースから患者データを取得
        patient_data = database.get_patient_data_for_plan(patient_id)
        if not patient_data:
            return Response("患者データが見つかりません。", status=404)

        # 担当者の所見を患者データに含める
        patient_data["therapist_notes"] = therapist_notes

        stream_generator = None

        if LLM_CLIENT_TYPE == "ollama":
            print("--- Ollama (local) クライアントで汎用モデルを実行します ---")
            logger.info(f"Calling Ollama general stream for patient_id: {patient_id}")
            stream_generator = ollama_client.generate_ollama_plan_stream(patient_data)
        else:  # デフォルトは 'gemini'
            print("--- Gemini (cloud) クライアントで汎用モデルを実行します ---")
            logger.info(f"Calling Gemini general stream for patient_id: {patient_id}")
            stream_generator = gemini_client.generate_general_plan_stream(patient_data)

        # 結果をストリーミングでフロントエンドに返す
        return Response(stream_generator, mimetype="text/event-stream")

    except ValueError:
        error_message = "無効な患者IDが指定されました。"
        error_event = f"event: error\ndata: {json.dumps({'error': error_message})}\n\n"
        return Response(error_event, mimetype="text/event-stream")
    except Exception as e:
        logger.error(f"汎用モデルのストリーム処理中にエラーが発生しました: {e}")
        error_message = "サーバーエラーが発生しました。詳細は管理者にお問い合わせください。"
        error_event = f"event: error\ndata: {json.dumps({'error': error_message})}\n\n"
        return Response(error_event, mimetype="text/event-stream")


@plan_bp.route("/api/generate/rag/<pipeline_name>")
@login_required
def generate_rag_stream(pipeline_name):
    """指定されたRAGパイプラインによる計画案をストリーミングで生成するAPI"""
    try:
        # URLのクエリパラメータから患者IDと所見を取得
        patient_id = int(request.args.get("patient_id"))
        therapist_notes = request.args.get("therapist_notes", "")

        # 権限チェック
        if not has_permission_for_patient(current_user, patient_id):
            return Response("権限がありません。", status=403)

        # データベースから患者データを取得
        patient_data = database.get_patient_data_for_plan(patient_id)
        if not patient_data:
            return Response("患者データが見つかりません。", status=404)

        # 担当者の所見を患者データに含める
        patient_data["therapist_notes"] = therapist_notes

        # キャッシュ管理関数を使って、指定されたパイプラインのExecutorを取得
        rag_executor = get_rag_executor(pipeline_name)
        if not rag_executor:
            raise Exception(f"パイプライン '{pipeline_name}' の Executorを取得できませんでした。")

        stream_generator = None
        if LLM_CLIENT_TYPE == "ollama" and hasattr(ollama_client, "generate_rag_plan_stream"):
            print("--- Ollama (local) クライアントでRAGモデルを実行します ---")
            logger.info(f"Calling Ollama RAG stream for patient_id: {patient_id}")
            stream_generator = ollama_client.generate_rag_plan_stream(patient_data, rag_executor)
        else:
            if LLM_CLIENT_TYPE == "ollama":
                print(
                    "--- [警告] OllamaクライアントにRAG初期生成(generate_rag_plan_stream)が実装されていません。Geminiクライアントでフォールバックします。---"
                )
                logger.warning("Ollama client missing 'generate_rag_plan_stream'. Falling back to Gemini.")

            print("--- Gemini (cloud) クライアントでRAGモデルを実行します ---")
            logger.info(f"Calling Gemini RAG stream for patient_id: {patient_id}")
            stream_generator = gemini_client.generate_rag_plan_stream(patient_data, rag_executor)

        return Response(stream_generator, mimetype="text/event-stream")

    except ValueError:
        error_message = "無効な患者IDが指定されました。"
        error_event = f"event: error\ndata: {json.dumps({'error': error_message})}\n\n"
        return Response(error_event, mimetype="text/event-stream")
    except Exception as e:
        logger.error(f"RAGモデル({pipeline_name})のストリーム処理中にエラーが発生しました: {e}")
        error_message = "サーバーエラーが発生しました。詳細は管理者にお問い合わせください。"
        error_event = f"event: error\ndata: {json.dumps({'error': error_message})}\n\n"
        return Response(error_event, mimetype="text/event-stream")


@plan_bp.route("/save_plan", methods=["POST"])
@login_required
def save_plan():
    """計画の保存とダウンロードページへのリダイレクト"""
    patient_id = int(request.form.get("patient_id"))

    # こちらでも、保存直前に再度権限チェックを行うことで、より安全性を高める。
    if not has_permission_for_patient(current_user, patient_id):
        flash("権限がありません。", "danger")
        return redirect(url_for("plan.index"))

    try:
        # フォームから送信された全データを辞書として取得
        form_data = request.form.to_dict()

        # 所感、AI提案テキスト、再生成履歴をフォームデータから分離
        therapist_notes = form_data.get("therapist_notes", "")
        suggestions = {k.replace("suggestion_", ""): v for k, v in form_data.items() if k.startswith("suggestion_")}
        regeneration_history_json = form_data.get("regeneration_history", "[]")

        # この患者の現在の「いいね」情報を取得（計画書のスナップショット用）
        liked_items = database.get_likes_by_patient_id(patient_id)

        # データベースに新しい計画として保存し、そのIDを取得
        new_plan_id = database.save_new_plan(patient_id, current_user.id, form_data, liked_items)

        # 全てのAI提案詳細情報を保存
        # 患者情報スナップショット用に、再度患者データを取得
        patient_info_snapshot = database.get_patient_data_for_plan(patient_id)
        editable_keys = [
            "main_risks_txt",
            "main_contraindications_txt",
            "func_pain_txt",
            "func_rom_limitation_txt",
            "func_muscle_weakness_txt",
            "func_swallowing_disorder_txt",
            "func_behavioral_psychiatric_disorder_txt",
            "cs_motor_details",
            "func_nutritional_disorder_txt",
            "func_excretory_disorder_txt",
            "func_pressure_ulcer_txt",
            "func_contracture_deformity_txt",
            "func_motor_muscle_tone_abnormality_txt",
            "func_disorientation_txt",
            "func_memory_disorder_txt",
            "adl_equipment_and_assistance_details_txt",
            "goals_1_month_txt",
            "goals_at_discharge_txt",
            "policy_treatment_txt",
            "policy_content_txt",
            "goal_p_action_plan_txt",
            "goal_a_action_plan_txt",
            "goal_s_psychological_action_plan_txt",
            "goal_s_env_action_plan_txt",
            "goal_s_3rd_party_action_plan_txt",
        ]
        database.save_all_suggestion_details(
            rehabilitation_plan_id=new_plan_id,
            staff_id=current_user.id,
            suggestions=suggestions,
            therapist_notes=therapist_notes,
            patient_info=patient_info_snapshot,
            liked_items=liked_items,
            editable_keys=editable_keys,
        )

        # 再生成履歴を保存
        try:
            regeneration_history = json.loads(regeneration_history_json)
            database.save_regeneration_history(new_plan_id, regeneration_history)
        except (json.JSONDecodeError, TypeError) as e:
            logger.warning(f"再生成履歴の処理中にエラーが発生しました: {e}")

        # Excel出力用に、DBに保存されたばかりの計画データをIDで再取得
        plan_data_for_excel = database.get_plan_by_id(new_plan_id)
        if not plan_data_for_excel:
            # このエラーは通常発生しないはず
            flash("保存した計画データの再取得に失敗しました。", "danger")
            return redirect(url_for("plan.index"))

        # Excelファイルを作成
        # Excel出力関数にもいいね情報を渡す（前回の改修を活かす）
        output_filepath = excel_writer.create_plan_sheet(plan_data_for_excel)
        output_filename = os.path.basename(output_filepath)

        # 一時的ないいね情報を削除
        database.delete_all_likes_for_patient(patient_id)

        # ファイルダウンロードとページ移動を同時に行うための中間ページを表示
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
    try:
        patient_id = int(request.form.get("patient_id"))

        # 権限チェック
        if not has_permission_for_patient(current_user, patient_id):
            return Response("権限がありません。", status=403)

        # フォームデータを取得
        form_data = request.form.to_dict()

        # 患者基本情報を取得
        patient_data = database.get_patient_data_for_plan(patient_id)
        if not patient_data:
            return Response("患者データが見つかりません。", status=404)

        # フォームデータと患者データを結合
        plan_data = patient_data.copy()
        plan_data.update(form_data)

        # Excelファイルのバイナリデータを生成
        excel_bytes = excel_writer.create_plan_sheet(plan_data, return_bytes=True)

        # Base64エンコード
        b64_data = base64.b64encode(excel_bytes.read()).decode("utf-8")

        return render_template("preview_viewer.html", excel_base64=b64_data)

    except Exception as e:
        logger.error(f"Error generating preview: {e}")
        return Response(f"プレビュー生成エラー: {e}", status=500)


@plan_bp.route("/like_suggestion", methods=["POST"])
@login_required
def like_suggestion():
    """AI提案の「いいね」評価を保存するAPIエンドポイント"""
    data = request.get_json()
    patient_id = data.get("patient_id")
    item_key = data.get("item_key")
    liked_model = data.get("liked_model")  # 'general', 'specialized', または null

    if not all([patient_id, item_key]):
        return jsonify({"status": "error", "message": "必須フィールドが不足しています。"}), 400

    try:
        # この関数を database.py に作成する必要があります
        # どのユーザーが評価したかを記録するために current_user.id も渡します
        if liked_model:
            database.save_suggestion_like(
                patient_id=patient_id, item_key=item_key, liked_model=liked_model, staff_id=current_user.id
            )
        else:
            # いいね削除
            model_to_delete = data.get("model_to_delete")
            if model_to_delete:
                database.delete_suggestion_like(patient_id=patient_id, item_key=item_key, liked_model=model_to_delete)
        return jsonify({"status": "success", "message": f"項目「{item_key}」の評価を保存しました。"})
    except Exception as e:
        logger.error(f"Error saving suggestion like: {e}")
        return jsonify({"status": "error", "message": "データベース処理中にエラーが発生しました。"}), 500


@plan_bp.route("/api/regenerate", methods=["POST"])
@login_required
def regenerate_item():
    """指定された項目をストリーミングで再生成するAPI"""
    try:
        data = request.get_json()
        patient_id = int(data.get("patient_id")) if data.get("patient_id") else None
        item_key = data.get("item_key")
        current_text = data.get("current_text", "")
        instruction = data.get("instruction", "")
        therapist_notes = data.get("therapist_notes", "")
        model_type = data.get("model_type")  # 'general' or 'specialized'
        pipeline_name = data.get("pipeline_name", DEFAULT_RAG_PIPELINE)

        if not all([patient_id, item_key, instruction]):
            return Response("必須パラメータが不足しています。", status=400)

        # 権限チェック
        if not has_permission_for_patient(current_user, patient_id):
            return Response("権限がありません。", status=403)

        # 患者データを取得
        patient_data = database.get_patient_data_for_plan(patient_id)
        if not patient_data:
            return Response("患者データが見つかりません。", status=404)

        patient_data["therapist_notes"] = therapist_notes

        # モデルタイプに応じてRAG Executorを準備
        rag_executor = None
        if model_type == "specialized":
            rag_executor = get_rag_executor(pipeline_name)
            if not rag_executor:
                raise Exception(f"パイプライン '{pipeline_name}' の Executorを取得できませんでした。")

        stream_generator = None
        if LLM_CLIENT_TYPE == "ollama":
            print(f"--- Ollama (local) クライアントで再生成を実行します (RAG: {'あり' if rag_executor else 'なし'}) ---")
            logger.info(f"Calling Ollama regeneration stream for item: {item_key} (RAG: {bool(rag_executor)})")
            stream_generator = ollama_client.regenerate_ollama_plan_item_stream(
                patient_data=patient_data,
                item_key=item_key,
                current_text=current_text,
                instruction=instruction,
                rag_executor=rag_executor,
            )
        else:  # デフォルトは 'gemini'
            print(f"--- Gemini (cloud) クライアントで再生成を実行します (RAG: {'あり' if rag_executor else 'なし'}) ---")
            logger.info(f"Calling Gemini regeneration stream for item: {item_key} (RAG: {bool(rag_executor)})")
            stream_generator = gemini_client.regenerate_plan_item_stream(
                patient_data=patient_data,
                item_key=item_key,
                current_text=current_text,
                instruction=instruction,
                rag_executor=rag_executor,
            )

        return Response(stream_generator, mimetype="text/event-stream")

    except Exception as e:
        logger.error(f"項目の再生成中にエラーが発生しました: {e}")
        error_message = "サーバーエラーが発生しました。"
        error_event = f"event: error\ndata: {json.dumps({'error': error_message})}\n\n"
        return Response(error_event, mimetype="text/event-stream")


@plan_bp.route("/api/plan_history/<int:patient_id>")
@login_required
def get_plan_history(patient_id):
    """指定された患者の計画書履歴をJSONで返すAPI"""
    # 権限チェック: ログイン中のユーザーがその患者の担当か、あるいは管理者か
    if not has_permission_for_patient(current_user, patient_id):
        return jsonify({"error": "権限がありません。"}), 403

    try:
        history = database.get_plan_history_for_patient(patient_id)
        # 日付を読みやすいフォーマットに変換
        for item in history:
            item["created_at"] = item["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        return jsonify(history)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@plan_bp.route("/view_plan/<int:plan_id>")
@login_required
def view_plan(plan_id):
    """特定の計画書を閲覧するページ"""
    try:
        plan_data = database.get_plan_by_id(plan_id)
        if not plan_data:
            flash("指定された計画書が見つかりません。", "danger")
            return redirect(url_for("plan.index"))

        # 権限チェック
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
        # send_from_directoryは、指定されたディレクトリの外にあるファイルへの
        # アクセスを防いでくれるため、安全なファイル送信に使われます。
        return send_from_directory(directory, filename, as_attachment=True)
    except FileNotFoundError:
        flash("ダウンロード対象のファイルが見つかりません。", "danger")
        return redirect(url_for("plan.index"))
