import logging

from flask import Blueprint

# Blueprint作成
plan_bp = Blueprint('plan', __name__)

# ロガーはハンドラを持たせず、app.core.logging_config が "app" ロガーに
# 設定したローテーション付きハンドラへ伝播させる。
# ここで個別に FileHandler を足すと、同じファイルを複数のハンドラが開き
# ローテーションが壊れる。
logger = logging.getLogger("app.routers.plan")

# 循環インポートを防ぐため、Blueprint定義後にViewとAPIをインポートする
# E402: インポートが先頭にない (Blueprint登録のため意図的)
# F401: インポートしたモジュールを使っていない (副作用でルート登録するため意図的)
# I001: インポートの並び順（ソート）が正しくない。(場所的にしょうがない)
from . import api, views  # noqa: E402, F401, I001
