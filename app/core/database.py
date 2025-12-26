import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

# データベース接続URLを作成
# "mysql+pymysql" の部分で、SQLAlchemyが内部的にPyMySQLを使うことを指定
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset=utf8mb4"

# SQLAlchemyのエンジンを作成
# engine = create_engine(DATABASE_URL, echo=False)
# pool_recycle=3600 を追加し、接続を1時間ごとにリサイクルする
# engine = create_engine(DATABASE_URL, echo=False, pool_recycle=3600)
# 接続が生きてるかを自動確認し、死んでいれば再接続
engine = create_engine(DATABASE_URL, echo=False, pool_recycle=3600, pool_pre_ping=True, pool_size=10, max_overflow=20)

# セッションを作成するためのクラス（ファクトリ）を定義
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    # モデルの定義をデータベースに反映（テーブル作成）
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    import sys

    # コマンドライン引数をチェック
    if len(sys.argv) > 1 and sys.argv[1] == "--init":
        print("データベースのテーブルを初期化（作成）します...")
        init_db()
        print("完了しました。")
    else:
        print("使い方:")
        print("  python database.py --init     # データベースを初期化します")
