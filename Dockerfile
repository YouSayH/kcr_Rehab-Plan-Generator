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
# 【重要】: requirements.txtに "gunicorn" と "mecab-python3" を追加してください
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

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

# 非rootユーザーの作成と切り替え (セキュリティ強化)
# RUN useradd --system --uid 1000 appuser
# USER appuser

# Cloud Runのデフォルトポート8080を公開
EXPOSE 8080

# Gunicornでアプリケーションを起動
# 1. timeoutを300秒(5分)に設定 (AWS側もこれに合わせます)
# 2. 起動パスを app.main:app に修正
CMD ["gunicorn", "--bind", ":8080", "--workers", "1", "--threads", "8", "--timeout", "300", "app.main:app"]