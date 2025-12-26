from sqlalchemy.orm import declarative_base

# 循環参照を防ぐため、Baseクラスのみを定義するファイルを作成
Base = declarative_base()
