import logging
import os

from flask import Blueprint

# Blueprint作成
plan_bp = Blueprint('plan', __name__)

# ロガーの設定
# app/routers/plan パッケージ全体で共通のロガー設定を行う
log_directory = "logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)
log_file_path = os.path.join(log_directory, "gemini_prompts.log")

logger = logging.getLogger("app.routers.plan")
if not logger.hasHandlers():
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

# 循環インポートを防ぐため、Blueprint定義後にViewとAPIをインポートする
# E402: インポートが先頭にない (Blueprint登録のため意図的)
# F401: インポートしたモジュールを使っていない (副作用でルート登録するため意図的)
# I001: インポートの並び順（ソート）が正しくない。(場所的にしょうがない)
from . import api, views  # noqa: E402, F401, I001
