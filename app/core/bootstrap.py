"""初期管理者アカウントのブートストラップ。

以前は schema.sql が固定のユーザー名とパスワードハッシュで管理者を投入しており、
平文パスワードがコメントに併記されていました。デプロイした全環境に既知の
管理者資格情報が存在することになるため、その方式を廃止しています。

代わりに、職員が1人も登録されていない場合にのみ、環境変数から管理者を作成します。
作成された管理者は must_change_password が立っており、パスワードを変更するまで
他の画面を使用できません (app/routers/auth.py の require_password_change を参照)。
"""

import logging
import os
import time

from sqlalchemy.exc import OperationalError
from werkzeug.security import generate_password_hash

import app.core.database as database
from app.models import Staff

logger = logging.getLogger(__name__)

MIN_PASSWORD_LENGTH = 12

# DBの起動待ちリトライ設定
_CONNECT_RETRIES = 10
_CONNECT_WAIT_SECONDS = 3


def _verify_staff_columns():
    """staff テーブルに必要なカラムが揃っているか確認する。

    モデルに追加したカラムが稼働中のDBに無いと、ログイン処理が
    ERROR 1054 (Unknown column) で失敗します。起動時は正常に見えるのに
    ログインだけが500になるため、ここで明示的に警告します。
    """
    from sqlalchemy import inspect

    try:
        actual = {c["name"] for c in inspect(database.engine).get_columns(Staff.__tablename__)}
    except Exception:
        logger.exception("staff テーブルのカラム情報を取得できませんでした。")
        return False

    expected = {c.name for c in Staff.__table__.columns}
    missing = expected - actual
    if missing:
        logger.error(
            "staff テーブルに必要なカラムがありません: %s。"
            "このままではログイン処理が Unknown column エラーで失敗します。"
            "migrations/001_add_password_change_columns.sql を適用してください。",
            ", ".join(sorted(missing)),
        )
        return False
    return True


def ensure_initial_admin():
    """職員が0件のとき、環境変数から初期管理者を作成する。

    既に職員が存在する場合は何もしません（毎回の起動で安全に呼べます）。
    作成した場合は True、しなかった場合は False を返します。

    DBがまだ接続を受け付けていない場合に備えて数回リトライします。
    compose の healthcheck があっても、初回起動時のタイミングは競合しやすいためです。
    """
    username = os.getenv("INITIAL_ADMIN_USER", "").strip()
    password = os.getenv("INITIAL_ADMIN_PASSWORD", "")

    for attempt in range(1, _CONNECT_RETRIES + 1):
        try:
            with database.engine.connect():
                break
        except OperationalError:
            if attempt == _CONNECT_RETRIES:
                logger.warning(
                    "DBに接続できないため初期管理者の作成をスキップします。"
                    "DB起動後にアプリを再起動してください。"
                )
                return False
            time.sleep(_CONNECT_WAIT_SECONDS)

    if not _verify_staff_columns():
        return False

    db = database.SessionLocal()
    try:
        if db.query(Staff.id).first() is not None:
            # 既に誰か登録済み。既存環境に勝手にアカウントを足さない。
            return False

        if not username or not password:
            logger.warning(
                "職員が1件も登録されていませんが、INITIAL_ADMIN_USER / INITIAL_ADMIN_PASSWORD が "
                "設定されていないため初期管理者を作成できません。"
                ".env に設定して再起動してください。"
            )
            return False

        if len(password) < MIN_PASSWORD_LENGTH:
            logger.warning(
                "INITIAL_ADMIN_PASSWORD が %d文字未満のため初期管理者を作成しません。"
                "より長いパスワードを設定して再起動してください。",
                MIN_PASSWORD_LENGTH,
            )
            return False

        admin = Staff(
            username=username,
            password=generate_password_hash(password),
            occupation=os.getenv("INITIAL_ADMIN_OCCUPATION", "管理者"),
            role="admin",
            must_change_password=True,
        )
        db.add(admin)
        db.commit()

        logger.info(
            "初期管理者 '%s' を作成しました。初回ログイン時にパスワード変更が必要です。", username
        )
        return True
    except Exception:
        db.rollback()
        # 初期化に失敗してもアプリ自体は起動させる（DB未起動時などに落とさないため）
        logger.exception("初期管理者の作成に失敗しました。")
        return False
    finally:
        db.close()
