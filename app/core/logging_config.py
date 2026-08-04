"""アプリケーション共通のロギング設定。

以前は app/__init__.py・app/routers/plan/__init__.py・
app/services/llm/rag_executor.py の3箇所が、それぞれ独立に
ローテーションなしの FileHandler で同じファイルを開いていた。
容量の上限が無いため、患者情報を含むログが単調増加してディスクを
埋め、同じホスト上の MySQL の書き込みも巻き添えで失敗しうる状態だった。

ここに集約し、サイズ上限つきのローテーションを行う。
"""

import logging
import logging.handlers
import os
import sys

LOG_DIRECTORY = "logs"
LOG_FILENAME = "app.log"

#: 1ファイルあたりの上限。超えると app.log.1 ... app.log.5 へ退避される
MAX_BYTES = 10 * 1024 * 1024
BACKUP_COUNT = 5

_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 同じプロセス内で複数回呼ばれてもハンドラを重複させないための記録
_configured = False


def _build_file_handler():
    """ローテーション付きのファイルハンドラを返す。作れない場合は None。

    ログディレクトリに書けないことは、アプリを止める理由にはなりません。
    特にコンテナを非rootで動かす構成では、Linuxホスト上のバインドマウントが
    root所有で作られて書き込めないことがあります。ここで例外を送出すると
    create_app が失敗し、gunicorn の --preload と restart: always が合わさって
    無限再起動になり、ログが書けないという些細な理由でサービスが停止します。
    """
    try:
        os.makedirs(LOG_DIRECTORY, exist_ok=True)
        handler = logging.handlers.RotatingFileHandler(
            os.path.join(LOG_DIRECTORY, LOG_FILENAME),
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
    except OSError as e:
        # ここではまだロガーを設定できていないので標準エラーへ直接出す
        print(
            f"[警告] ログファイル {LOG_DIRECTORY}/{LOG_FILENAME} を開けません ({e})。"
            "標準出力へのログ出力のみで続行します。"
            "コンテナ実行時は、マウント元ディレクトリの所有者を"
            "実行ユーザー(uid 1000)に合わせてください。",
            file=sys.stderr,
        )
        return None

    handler.setFormatter(logging.Formatter(_FORMAT))
    return handler


def configure_logging(level=logging.INFO):
    """アプリ全体のロギングを設定する。

    個々のモジュールは logging.getLogger(__name__) を呼ぶだけでよく、
    ハンドラを自分で追加する必要はありません（追加すると同じファイルを
    複数のハンドラが開き、ローテーションが壊れます）。
    """
    global _configured
    if _configured:
        return

    root = logging.getLogger("app")
    root.setLevel(level)

    # 既存のハンドラを一掃してから付け直す（リロード時の重複防止）
    for existing in list(root.handlers):
        root.removeHandler(existing)

    file_handler = _build_file_handler()
    if file_handler is not None:
        root.addHandler(file_handler)

    # 標準出力にも出す。propagate=False にすると gunicorn がルートロガーへ
    # 張っている console ハンドラへ届かなくなり、`docker compose logs` に
    # アプリのエラー（Flask が出す500のトレースバックを含む）が
    # 一切出なくなるため、ここで明示的に付け直す。
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter(_FORMAT))
    root.addHandler(stream_handler)

    # 親(ルートロガー)へ伝播させない。伝播させると gunicorn 側のハンドラと
    # 上の StreamHandler で二重出力になる。
    root.propagate = False

    _configured = True
    return root
