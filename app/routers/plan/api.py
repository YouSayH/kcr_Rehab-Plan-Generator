import json
import logging

from flask import Response, jsonify, request
from flask_login import current_user, login_required

from app.core.database import SessionLocal
from app.crud import patient as patient_crud
from app.crud import plan as plan_crud

# 履歴取得用にモデルとセッションをインポート
from app.models import RehabilitationPlan

# 【修正】個別クライアントのインポートを廃止し、ファクトリ関数を使用
from app.services.llm import get_llm_client
from app.services.rag_manager import (
    DEFAULT_RAG_PIPELINE,
    get_rag_executor,
)
from app.utils.helpers import has_permission_for_patient

# Blueprintのインポート
from . import plan_bp

logger = logging.getLogger(__name__)

@plan_bp.route("/api/generate/general")
@login_required
def generate_general_stream():
    """汎用モデル（Gemini/Ollama）による計画案をストリーミングで生成するAPI"""
    try:
        # URLのクエリパラメータから患者IDと所見を取得
        patient_id = int(request.args.get("patient_id"))
        therapist_notes = request.args.get("therapist_notes", "")

        # 権限チェック：ログイン中のユーザーが担当する患者か確認
        if not has_permission_for_patient(current_user, patient_id):
            return Response("権限がありません。", status=403)

        # データベースから患者データを取得
        patient_data = patient_crud.get_patient_data_for_plan(patient_id)
        if not patient_data:
            return Response("患者データが見つかりません。", status=404)

        # 担当者の所見を患者データに含める
        patient_data["therapist_notes"] = therapist_notes

        # 【修正】ファクトリからクライアントを取得して実行
        llm_client = get_llm_client()
        client_name = llm_client.__class__.__name__

        print(f"--- {client_name} で汎用モデルを実行します ---")
        logger.info(f"Calling General Stream using {client_name} for patient_id: {patient_id}")

        # 統一されたインターフェースでメソッド呼び出し
        stream_generator = llm_client.generate_plan_stream(patient_data)

        return Response(stream_generator, mimetype="text/event-stream")

    except ValueError:
        error_message = "無効な患者IDが指定されました。"
        error_event = f"event: error\ndata: {json.dumps({'error': error_message}, ensure_ascii=False)}\n\n"
        return Response(error_event, mimetype="text/event-stream")
    except Exception as e:
        logger.error(f"汎用モデルのストリーム処理中にエラーが発生しました: {e}", exc_info=True)
        error_message = "サーバーエラーが発生しました。詳細は管理者にお問い合わせください。"
        error_event = f"event: error\ndata: {json.dumps({'error': error_message}, ensure_ascii=False)}\n\n"
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
        patient_data = patient_crud.get_patient_data_for_plan(patient_id)
        if not patient_data:
            return Response("患者データが見つかりません。", status=404)

        # 担当者の所見を患者データに含める
        patient_data["therapist_notes"] = therapist_notes

        # キャッシュ管理関数を使って、指定されたパイプラインのExecutorを取得
        rag_executor = get_rag_executor(pipeline_name)
        if not rag_executor:
            raise Exception(f"パイプライン '{pipeline_name}' の Executorを取得できませんでした。")

        # 【修正】ファクトリからクライアントを取得して実行
        llm_client = get_llm_client()
        client_name = llm_client.__class__.__name__

        print(f"--- {client_name} でRAGモデルを実行します ---")
        logger.info(f"Calling RAG Stream using {client_name} for patient_id: {patient_id}")

        # 統一されたインターフェースでメソッド呼び出し
        stream_generator = llm_client.generate_rag_plan_stream(
            patient_data=patient_data,
            rag_executor=rag_executor
        )

        return Response(stream_generator, mimetype="text/event-stream")

    except ValueError:
        error_message = "無効な患者IDが指定されました。"
        error_event = f"event: error\ndata: {json.dumps({'error': error_message}, ensure_ascii=False)}\n\n"
        return Response(error_event, mimetype="text/event-stream")
    except Exception as e:
        logger.error(f"RAGモデル({pipeline_name})のストリーム処理中にエラーが発生しました: {e}", exc_info=True)
        error_message = "サーバーエラーが発生しました。詳細は管理者にお問い合わせください。"
        error_event = f"event: error\ndata: {json.dumps({'error': error_message}, ensure_ascii=False)}\n\n"
        return Response(error_event, mimetype="text/event-stream")


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
        # どのユーザーが評価したかを記録するために current_user.id も渡します
        if liked_model:
            plan_crud.save_suggestion_like(
                patient_id=patient_id, item_key=item_key, liked_model=liked_model, staff_id=current_user.id
            )
        else:
            # いいね削除
            model_to_delete = data.get("model_to_delete")
            if model_to_delete:
                plan_crud.delete_suggestion_like(patient_id=patient_id, item_key=item_key, liked_model=model_to_delete)

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
        # therapist_notes = data.get("therapist_notes", "") # 必要であれば取得
        model_type = data.get("model_type")  # 'general' or 'specialized'
        pipeline_name = data.get("pipeline_name", DEFAULT_RAG_PIPELINE)

        if not all([patient_id, item_key, instruction]):
            return Response("必須パラメータが不足しています。", status=400)

        # 権限チェック
        if not has_permission_for_patient(current_user, patient_id):
            return Response("権限がありません。", status=403)

        # 患者データを取得
        patient_data = patient_crud.get_patient_data_for_plan(patient_id)
        if not patient_data:
            return Response("患者データが見つかりません。", status=404)

        # モデルタイプに応じてRAG Executorを準備
        rag_executor = None
        if model_type == "specialized":
            rag_executor = get_rag_executor(pipeline_name)
            if not rag_executor:
                raise Exception(f"パイプライン '{pipeline_name}' の Executorを取得できませんでした。")

        # 【修正】ファクトリからクライアントを取得して実行
        llm_client = get_llm_client()
        client_name = llm_client.__class__.__name__

        print(f"--- {client_name} で再生成を実行します (RAG: {'あり' if rag_executor else 'なし'}) ---")
        logger.info(f"Calling Regeneration Stream using {client_name} for item: {item_key}")

        # 統一されたインターフェースでメソッド呼び出し
        stream_generator = llm_client.regenerate_plan_item_stream(
            patient_data=patient_data,
            item_key=item_key,
            current_text=current_text,
            instruction=instruction,
            rag_executor=rag_executor,
        )

        return Response(stream_generator, mimetype="text/event-stream")

    except Exception as e:
        logger.error(f"項目の再生成中にエラーが発生しました: {e}", exc_info=True)
        error_message = "サーバーエラーが発生しました。"
        error_event = f"event: error\ndata: {json.dumps({'error': error_message}, ensure_ascii=False)}\n\n"
        return Response(error_event, mimetype="text/event-stream")


@plan_bp.route("/api/plan_history/<int:patient_id>")
@login_required
def get_plan_history(patient_id):
    """指定された患者の計画書履歴をJSONで返すAPI"""
    # 権限チェック: ログイン中のユーザーがその患者の担当か、あるいは管理者か
    if not has_permission_for_patient(current_user, patient_id):
        return jsonify({"error": "権限がありません。"}), 403

    # 【修正】履歴リストの取得 (CRUDにはないためSessionLocalを使用)
    session = SessionLocal()
    try:
        plans = (
            session.query(RehabilitationPlan.plan_id, RehabilitationPlan.created_at)
            .filter(RehabilitationPlan.patient_id == patient_id)
            .order_by(RehabilitationPlan.created_at.desc())
            .all()
        )
        history = [
            {
                "plan_id": p.plan_id,
                "created_at": p.created_at.strftime("%Y-%m-%d %H:%M:%S") if p.created_at else "不明"
            }
            for p in plans
        ]
        return jsonify(history)
    except Exception as e:
        logger.error(f"Error fetching plan history: {e}")
        return jsonify({"error": "履歴の取得中にエラーが発生しました。"}), 500
    finally:
        session.close()
