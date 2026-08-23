# ステージ1: ビルドステージ
# 安定版のDebian (Bookworm) をベースにした軽量Pythonイメージを使用
FROM python:3.11-slim-bookworm as builder

# タイムゾーンをJSTに設定
ENV TZ=Asia/Tokyo
RUN apt-get update && apt-get install -y tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# MeCab (Hybrid Search用) と関連ツールをインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    mecab \
    libmecab-dev \
    mecab-ipadic-utf8 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
# MeCabが辞書を見つけられるように環境変数を設定
ENV MECABRC=/etc/mecabrc

WORKDIR /app

# 依存関係をインストール (ビルドキャッシュ活用のため先に実行)
# requirements.txt ではなく requirements.lock を使う。前者はバージョンを固定して
# いても推移的依存が固定されないため、ビルドした日によってイメージの中身が変わる。
COPY requirements.lock .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.lock

# ステージ2: ランタイムステージ
FROM python:3.11-slim-bookworm

# タイムゾーン設定をコピー
ENV TZ=Asia/Tokyo
COPY --from=builder /etc/localtime /etc/localtime
COPY --from=builder /etc/timezone /etc/timezone

# MeCabの実行ファイルと辞書をコピー
COPY --from=builder /usr/lib/x86_64-linux-gnu /usr/lib/x86_64-linux-gnu
COPY --from=builder /usr/bin/mecab /usr/bin/mecab
COPY --from=builder /usr/lib/mecab /usr/lib/mecab
COPY --from=builder /etc/mecabrc /etc/mecabrc
ENV MECABRC=/etc/mecabrc

COPY --from=builder /var/lib/mecab /var/lib/mecab

WORKDIR /app

# 依存関係ライブラリをビルドステージからコピー
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# アプリケーションコードをコピー (.dockerignoreで不要ファイルは除外)
COPY . .

RUN chmod -R a+r /var/lib/mecab

# 非rootユーザーで実行する。
# web は nginx 経由で外部からのHTTPを受ける唯一のアプリプロセスであり、
# Flask/Jinja2/openpyxl/ChromaDB のいずれかに深刻な脆弱性が出た場合、
# root のままだとバインドマウントされたホスト側のディレクトリ
# (output・logs・rag_db_data) を自由に読み書きされる。
# アプリが書き込むディレクトリは事前に作って所有者を合わせておく
# (マウントされない場合でも起動できるようにするため)。
RUN useradd --system --uid 1000 --create-home appuser \
    && mkdir -p /app/logs /app/output \
    && chown -R appuser:appuser /app

USER appuser

# Cloud Runのデフォルトポート8080を公開
EXPOSE 8080

# Gunicornでアプリケーションを起動
# 1. timeoutを300秒(5分)に設定 (AWS側もこれに合わせます)
# 2. WSGIエントリポイントは run.py の app (app/main.py は存在しない)
# 起動コマンドの定義はこの1箇所に集約する。docker-compose 側で command を上書きすると、
# compose では動くが docker run / Cloud Run では動かないという乖離が生まれるため。
CMD ["gunicorn", "--bind", ":8080", "--workers", "1", "--threads", "8", "--timeout", "300", "--preload", "run:app"]