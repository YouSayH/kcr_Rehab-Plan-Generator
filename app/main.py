import logging
import os
from datetime import timedelta

import yaml
from dotenv import load_dotenv
from flask import (
    Flask,
    session,
)
from flask_login import (
    LoginManager,
)
from flask_wtf.csrf import CSRFProtect

# 自作のPythonファイルをインポート
import app.core.database as database
from app.models import Staff
from app.routers.admin import admin_bp
from app.routers.auth import auth_bp
from app.routers.patient import patient_bp
from app.routers.plan import plan_bp
from app.services.llm.patient_info_parser import PatientInfoParser

load_dotenv()

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

LLM_CLIENT_TYPE = os.getenv("LLM_CLIENT_TYPE", "gemini")
print(f"--- LLMクライアントとして '{LLM_CLIENT_TYPE}' を使用します ---")

def load_active_pipeline_from_config():
    # 設定ファイルのパス (app.pyと同じ階層にあると仮定)
    config_path = "rag_config.yaml"

    # デフォルトのフォールバック値（ファイルがない場合など）
    fallback_pipeline = "hybrid_search_experiment"

    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                pipeline = config.get("active_pipeline")
                if pipeline:
                    print(f"--- このRAGを使用します。: {pipeline} ---")
                    return pipeline
        except Exception as e:
            print(f"Warning: RAG選択ファイルが読み込めませんでした。 {config_path}: {e}")

    print(f"--- デフォルトのRAGを使用します。: {fallback_pipeline} ---")
    return fallback_pipeline


# アプリケーション起動時に一度だけ読み込んで定数にセット
DEFAULT_RAG_PIPELINE = load_active_pipeline_from_config()

app = Flask(__name__, template_folder="web/templates", static_folder="web/static")

# ユーザーのセッション情報（例: ログイン状態）を暗号化するため
# これがないとflashメッセージなどが使えない。
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
if not app.config["SECRET_KEY"]:
    raise ValueError("環境変数 'SECRET_KEY' が .env ファイルに設定されていません。")

csrf = CSRFProtect(app)

# 9時間後(労働時間8時間+1時間)にタイムアウトする。
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=540)


login_manager = LoginManager()
login_manager.init_app(app)
# 未ログインのユーザーがログイン必須ページにアクセスした際、
# どのページにリダイレクト（転送）するかを指定します。'login'は下の@app.route('/login')を持つ関数名を指します。
login_manager.login_view = "auth.login"



# 患者情報解析パーサーを初期化
USE_HYBRID_MODE = os.getenv("USE_HYBRID_MODE", "false").lower() == "true"

print("Initializing Patient Info Parser...")
try:
    # クライアントタイプ(gemini/ollama)と、ハイブリッドモード(True/False)を指定して初期化
    patient_info_parser = PatientInfoParser(
        client_type=LLM_CLIENT_TYPE,
        use_hybrid_mode=USE_HYBRID_MODE
    )

    mode_name = "Hybrid Mode (GLiNER2 + LLM)" if USE_HYBRID_MODE else "Standard Mode (Multi-step LLM)"
    print(f"Patient Info Parser initialized successfully. [{mode_name}]")

except Exception as e:
    print(f"FATAL: Failed to initialize Patient Info Parser: {e}")
    # 初期化に失敗した場合、アプリがクラッシュしないように None を設定
    patient_info_parser = None


# ・ユーザー情報をセッションから読み込むための関数
# Flask-Loginは、ページを移動するたびにこの関数を呼び出し、
# セッションに保存されたユーザーIDからユーザー情報を復元します。
@login_manager.user_loader
def load_user(staff_id):
    staff_info = database.get_staff_by_id(int(staff_id))
    if not staff_info:
        return None

    # ブラウザのCookie(session)内のトークンと、DBに保存されている最新のトークンを比較
    # staff_info は辞書なので .get() を使う
    if session.get("session_token") != staff_info.get("session_token"):
        # 一致しない場合 (他のPCが新しくログインしたため)
        return None  # ログインを無効化する

    # トークンが一致した場合のみ、ユーザー情報を復元
    return Staff(
        staff_id=staff_info["id"],
        username=staff_info["username"],
        role=staff_info["role"],
        occupation=staff_info["occupation"],
    )

# ブループリントでルーティング
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(plan_bp)
app.register_blueprint(patient_bp)


# 現在未使用
# @app.route("/api/get_plan/<int:plan_id>")
# @login_required
# def api_get_plan(plan_id):
#     """特定の計画書データをJSONで返すAPI"""
#     try:
#         try:
#             plan_data = get_plan_checked(plan_id, current_user)
#         except ValueError:
#             return jsonify({"error": "Plan not found"}), 404
#         except PermissionError:
#             return jsonify({"error": "Permission denied"}), 403

#         # datetimeオブジェクトを文字列に変換
#         for key, value in plan_data.items():
#             if hasattr(value, 'isoformat'):
#                 plan_data[key] = value.isoformat()

#         return jsonify(plan_data)
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=5000, debug=False) # 最初にRAGインスタンスを作る場合に邪魔

    # debug=True のままだとリローダーが有効になるため、use_reloader=False を明示的に指定します。
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
