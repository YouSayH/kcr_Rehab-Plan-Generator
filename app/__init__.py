import logging
import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, session
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# 自作モジュールのインポート
from app.auth_models import Staff
from app.crud import staff as staff_crud

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
    session_lifetime = timedelta(minutes=540)
    app.config["PERMANENT_SESSION_LIFETIME"] = session_lifetime

    # CSRFトークンの有効期限をセッションと揃える。
    # Flask-WTF の既定は1時間で、セッションより先にトークンだけが切れる。
    # 計画書の編集は所見の記入やAI生成の確認で1時間を超えることがあり、
    # 保存ボタンを押した瞬間に400になって入力内容が全て失われる。
    app.config["WTF_CSRF_TIME_LIMIT"] = int(session_lifetime.total_seconds())

    # セッションCookieの保護。HTTPONLY は既定でTrueだが、意図を明示しておく。
    # SECURE は HTTPS 化(add-03)の際に True にする。HTTP運用のまま True にすると
    # Cookieが送信されずログインできなくなるため、環境変数で切り替える。
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "").lower() in (
        "1", "true", "yes"
    )

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

    # パスワード変更が必要な職員を、変更画面以外へ進ませないためのガード
    register_password_change_guard(app)

    # セキュリティレスポンスヘッダ
    register_security_headers(app)

    # 初期管理者の作成 (職員が0件のときのみ)。テスト時は実行しません。
    if not app.config.get("TESTING"):
        bootstrap_initial_admin(app)

    # 起動時の情報をログ出力
    llm_client_type = os.getenv("LLM_CLIENT_TYPE", "gemini")
    app.logger.info(f"App initialized with LLM Client: {llm_client_type}")

    return app


def bootstrap_initial_admin(app):
    """職員が0件のとき、環境変数から初期管理者を作成する。"""
    # 遅延インポート: DB接続を伴うため、テスト用の設定適用より後に読み込む
    import app.core.database as database
    from app.core.bootstrap import ensure_initial_admin

    try:
        ensure_initial_admin()
    except Exception:
        # DB未起動などで失敗してもアプリ自体は起動させる
        app.logger.exception("初期管理者の作成処理でエラーが発生しました。")
    finally:
        # gunicorn は --preload で起動するため、ここで張った接続が fork 後の
        # 全ワーカーに共有されてしまう。プールを破棄して各ワーカーに張り直させる。
        database.engine.dispose()


#: 現在使用している唯一の外部CDN
_CDN = "https://cdn.jsdelivr.net"

#: Content-Security-Policy の各ディレクティブ
#:
#: 【制限事項】テンプレートにインラインの <script> が多数あるため、
#: script-src に 'unsafe-inline' が必要で、XSS対策としてのCSPの効果は限定的です。
#: それでも connect-src / form-action / frame-ancestors を絞ることで、
#: 万一スクリプトが実行された場合に患者情報を外部へ送信する経路と、
#: クリックジャッキングは塞げます。
#: インラインスクリプトを外部ファイルへ追い出せば 'unsafe-inline' を外せます。
_CSP_DIRECTIVES = [
    "default-src 'self'",
    f"script-src 'self' 'unsafe-inline' {_CDN}",
    f"style-src 'self' 'unsafe-inline' {_CDN}",
    f"font-src 'self' data: {_CDN}",
    "img-src 'self' data:",
    # 患者情報の外部送信(fetch/XHR/WebSocket)を自オリジンに限定する
    "connect-src 'self'",
    # フォームの送信先を自オリジンに限定する
    "form-action 'self'",
    # クリックジャッキング対策
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "object-src 'none'",
]


def register_security_headers(app):
    """全レスポンスにセキュリティヘッダを付与する。

    CSP は CSP_REPORT_ONLY=1 で Report-Only に切り替えられます。
    本番へ適用する前に、開発環境で違反が出ないか確認する用途です。
    """
    csp = "; ".join(_CSP_DIRECTIVES)
    report_only = os.getenv("CSP_REPORT_ONLY", "").lower() in ("1", "true", "yes")
    csp_header = "Content-Security-Policy-Report-Only" if report_only else "Content-Security-Policy"

    @app.after_request
    def set_security_headers(response):
        response.headers.setdefault(csp_header, csp)
        # MIMEスニッフィングによるスクリプト実行を防ぐ
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        # frame-ancestors 非対応ブラウザ向けの保険
        response.headers.setdefault("X-Frame-Options", "DENY")
        # 患者IDを含むURLを外部サイトへ渡さない
        response.headers.setdefault("Referrer-Policy", "same-origin")
        return response


def register_password_change_guard(app):
    """must_change_password が立っている間、パスワード変更画面以外を遮断する。"""
    from flask import redirect, request, url_for
    from flask_login import current_user

    # 変更前でもアクセスを許可するエンドポイント
    allowed_endpoints = {"auth.change_password", "auth.logout", "auth.login", "static"}

    @app.before_request
    def require_password_change():
        if not current_user.is_authenticated:
            return None
        if not getattr(current_user, "must_change_password", False):
            return None
        if request.endpoint in allowed_endpoints:
            return None
        return redirect(url_for("auth.change_password"))


def configure_logging(app):
    """ロギングの設定を行うヘルパー関数

    実体は app/core/logging_config.py に集約している。
    ローテーションを効かせるため、個々のモジュールでハンドラを追加しないこと。
    """
    from app.core.logging_config import configure_logging as setup

    # このパッケージ名が "app" のため、Flask の app.logger は
    # logging.getLogger("app") と同一オブジェクトになる。
    # つまり setup() の設定がそのまま app.logger にも効く（未捕捉例外の
    # トレースバックもローテーション先と標準出力の両方に出る）。
    setup()


# ユーザーローダーの定義
@login_manager.user_loader
def load_user(staff_id):
    """
    Flask-Login用ユーザーローダー
    セッション内のIDからユーザーオブジェクトを復元します。
    """
    staff_info = staff_crud.get_staff_by_id(int(staff_id))
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
        must_change_password=bool(staff_info.get("must_change_password")),
    )
