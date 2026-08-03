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


def _build_handler():
    os.makedirs(LOG_DIRECTORY, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        os.path.join(LOG_DIRECTORY, LOG_FILENAME),
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
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

    root.addHandler(_build_handler())

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
