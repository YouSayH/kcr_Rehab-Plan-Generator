import logging
import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, session
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# 自作モジュールのインポート
import app.core.database as database
from app.auth_models import Staff

# ブループリントのインポート
from app.routers.admin import admin_bp
from app.routers.auth import auth_bp
from app.routers.patient import patient_bp
from app.routers.plan import plan_bp

# .env ファイルの読み込み
load_dotenv()

# 拡張機能のグローバルインスタンス作成
# (初期化は create_app 内で行いますが、他モジュールからインポートできるようにここでインスタンス化します)
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(test_config=None):
    """
    アプリケーションファクトリ関数
    Flaskアプリのインスタンスを作成・設定して返します。
    """
    # template_folder, static_folder は app パッケージからの相対パスで指定
    app = Flask(__name__, template_folder="web/templates", static_folder="web/static")

    # 基本設定
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    # 9時間後(労働時間8時間+1時間)にタイムアウトする設定
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=540)

    # テスト設定の適用 (テスト時はこれで上書きされます)
    if test_config:
        app.config.update(test_config)

    # SECRET_KEYの検証 (テスト時以外)
    if not app.config.get("SECRET_KEY") and not (test_config and test_config.get("TESTING")):
        raise ValueError("環境変数 'SECRET_KEY' が .env ファイルに設定されていません。")

    # 拡張機能の初期化
    csrf.init_app(app)
    login_manager.init_app(app)
    # 未ログインユーザーのリダイレクト先
    login_manager.login_view = "auth.login"

    # ロギング設定
    configure_logging(app)

    # ブループリントの登録
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(plan_bp)
    app.register_blueprint(patient_bp)

    # 起動時の情報をログ出力
    llm_client_type = os.getenv("LLM_CLIENT_TYPE", "gemini")
    app.logger.info(f"App initialized with LLM Client: {llm_client_type}")

    return app


def configure_logging(app):
    """ロギングの設定を行うヘルパー関数"""
    log_directory = "logs"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    log_file_path = os.path.join(log_directory, "gemini_prompts.log")

    # ハンドラが未設定の場合のみ設定 (リロード時の重複防止)
    if not app.logger.hasHandlers():
        app.logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
        file_handler.setFormatter(formatter)

        app.logger.addHandler(file_handler)


# ユーザーローダーの定義
@login_manager.user_loader
def load_user(staff_id):
    """
    Flask-Login用ユーザーローダー
    セッション内のIDからユーザーオブジェクトを復元します。
    """
    staff_info = database.get_staff_by_id(int(staff_id))
    if not staff_info:
        return None

    # セッション固定攻撃対策: DB上のトークンとセッション内のトークンを比較
    # (他の端末でログインされた場合などに無効化するため)
    if session.get("session_token") != staff_info.get("session_token"):
        return None

    # Staffモデルのインスタンスを返却
    return Staff(
        staff_id=staff_info["id"],
        username=staff_info["username"],
        role=staff_info["role"],
        occupation=staff_info["occupation"],
    )
