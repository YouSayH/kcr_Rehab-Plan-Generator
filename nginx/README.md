# Web Server Configuration (`nginx/`)

このディレクトリは、Docker Compose環境で動作する **Nginx** の設定ファイルを管理しています。

Nginxは **リバースプロキシ** として機能し、Webブラウザからのリクエストを最初に受け取ります。その後、リクエストの種類に応じて、静的ファイルを直接返却するか、バックエンドのFlaskアプリケーションに転送するかを振り分けます。

---

## 📁 1. 現在の設定と役割 (Current Configuration)

### `default.conf` (メイン設定)

`docker-compose.yml` によってコンテナ内の `/etc/nginx/conf.d/default.conf` にマウントされ、適用される主要な設定ファイルです。

* **主な設定内容**:
* **ポート80での待機**: HTTPリクエストを受け付けます。
* **静的ファイルの配信 (`/static/`)**:
* CSS、JavaScript、画像などのリクエスト（URLが `/static/` で始まるもの）に対しては、Flaskを経由せず、Nginxが直接ディスクからファイルを読み込んで返却します。
* これにより、アプリケーションサーバーの負荷を大幅に軽減し、レスポンスを高速化しています。


* **リバースプロキシ (`/`)**:
* その他の全てのリクエストは、Flaskアプリケーションコンテナ（ホスト名: `web`、ポート: `8080`）に転送します。


* **タイムアウト設定**:
* AIによる文章生成は時間がかかる場合があるため、`proxy_read_timeout` などを長めに設定し、生成途中で接続が切断されるのを防いでいます。


* **ストリーミング対応**:
* AIの回答をリアルタイムに表示（Server-Sent Events）するため、バッファリング設定 (`proxy_buffering`) を調整し、データが溜まるのを待たずに即座にクライアントへ送信するように構成しています。


### `host_proxy.conf` (開発用・ホスト連携設定)

このファイルは、**Dockerコンテナ内のNginxから、ホストマシン（あなたのPC自体）で動作しているWebサーバーにリクエストを転送するため** の設定例です。

通常、`default.conf` は同じDockerネットワーク内の `web` コンテナ（Flask）に転送しますが、`host_proxy.conf` は `host.docker.internal` などを介して、Dockerの外側へリクエストを投げます。

* **主な用途**:
* **ローカル開発中のデバッグ**: FlaskアプリをDockerではなく、VS Codeのデバッガなどでローカル起動 (`python app.py`) している状態で、Nginxコンテナだけを使いたい場合。
* **既存システムとの併用**: ホストマシン上で動いている別のWebサーバーやAPIと連携させたい場合。


* **設定のポイント**:
* **`proxy_pass http://host.docker.internal:5000;`**:
* 転送先が `web` (コンテナ名) ではなく、`host.docker.internal` (ホストマシンを表すDockerの特殊DNS名) になっています。
* これにより、あなたのPCで `localhost:5000` で起動しているアプリに、コンテナ内のNginxからアクセスできるようになります。





#### 使い方 (How to use)

この設定を使用するには、`docker-compose.yml` の `volumes` 設定を書き換える必要があります。

```yaml
# docker-compose.yml の修正例
services:
  nginx:
    volumes:
      # default.conf の代わりに host_proxy.conf をマウントする
      - ./nginx/host_proxy.conf:/etc/nginx/conf.d/default.conf:ro

```


### 🏗 アーキテクチャと設計思想

* **責務の分離**: Nginxは「静的配信・通信制御」、Flaskは「動的処理・DB操作」に集中させます。
* **セキュリティ**: 外部（ブラウザ）からはNginxしか見えず、Flaskアプリケーションが直接インターネットにさらされることはありません。

---

## 📚 2. Nginx 学習ガイド (Learning Guide)

Nginxの設定は、**Context (コンテキスト)** と **Directive (ディレクティブ)** の組み合わせで記述します。

### 🔹 基本構造 (Structure)

```nginx
# Main Context (グローバル設定)
worker_processes auto;

events {
    # Events Context (接続処理の設定)
    worker_connections 1024;
}

http {
    # HTTP Context (Webサーバーとしての共通設定)
    include       mime.types;
    default_type  application/octet-stream;

    server {
        # Server Context (バーチャルホスト設定)
        listen 80;
        server_name localhost;

        location / {
            # Location Context (URLパスごとの振る舞い)
            # ...
        }
    }
}

```

### 🔹 主要なディレクティブ (Common Directives)

このプロジェクトや一般的なWebアプリでよく使われる設定項目（オプション）です。

| ディレクティブ | 説明 | 設定例 |
| --- | --- | --- |
| **`listen`** | 待ち受けポートを指定します。 | `listen 80;` / `listen 443 ssl;` |
| **`server_name`** | どのドメインへのアクセスを処理するか指定します。 | `server_name example.com;` |
| **`root`** | 静的ファイルのルートディレクトリを指定します。 | `root /usr/share/nginx/html;` |
| **`proxy_pass`** | リクエストを別のサーバー（Flaskなど）に転送します。 | `proxy_pass http://web:8080;` |
| **`client_max_body_size`** | アップロードファイルの最大サイズ制限。デフォルトは1MB。 | `client_max_body_size 10M;` |
| **`proxy_read_timeout`** | バックエンドからの応答を待つ最大時間。AI生成など時間がかかる処理に必須。 | `proxy_read_timeout 300s;` |
| **`try_files`** | ファイルの存在を確認し、なければ別の処理（index.htmlを返す等）を行います。SPAで必須。 | `try_files $uri $uri/ /index.html;` |

---

## 🚀 3. 実践的な設定パターン (Best Practices & Patterns)

本番運用や機能拡張の際に役立つ「書き方」の例です。

### A. HTTPS化 (SSL/TLS) [必須]

本番環境では通信の暗号化が必須です。Let's Encryptなどで証明書を取得し、以下のように記述します。

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    # 証明書ファイルのパス
    ssl_certificate /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;

    # 推奨されるセキュリティ設定 (Mozilla SSL Configuration Generator参照)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}

```

### B. セキュリティヘッダーの追加

ブラウザの保護機能を有効にします。

```nginx
# クリックジャッキング対策 (iframeでの埋め込み禁止)
add_header X-Frame-Options "SAMEORIGIN";
# XSSフィルタ有効化
add_header X-XSS-Protection "1; mode=block";
# MIMEタイプスニフィング防止
add_header X-Content-Type-Options "nosniff";

```

### C. パフォーマンスチューニング (Gzip圧縮)

テキストファイルを圧縮して送信し、表示速度を向上させます。

```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript;
gzip_min_length 1000; # 1KB以上なら圧縮

```

### D. 負荷分散 (Load Balancing)

将来的にFlaskコンテナを複数に増やした場合、`upstream` ブロックを使って負荷分散できます。

```nginx
http {
    upstream backend_servers {
        server web1:8080;
        server web2:8080;
    }

    server {
        location / {
            proxy_pass http://backend_servers; # 自動的に振り分けられる
        }
    }
}

```

---

## 🛠 4. トラブルシューティングとコマンド

コンテナ内でNginxを操作する際のコマンドです。

* **設定ファイルの構文チェック**:
```bash
docker-compose exec nginx nginx -t

```


* `syntax is ok` と表示されればOKです。エラーがある場合は行番号が表示されます。


* **設定の再読み込み (ダウンタイムなし)**:
```bash
docker-compose exec nginx nginx -s reload

```


* コンテナを再起動せずに設定変更を反映させたい場合に使用します。


* **ログの確認**:
```bash
docker-compose logs -f nginx

```


* アクセスログやエラーログをリアルタイムで確認できます。



### 📖 おすすめ学習リソース

* **[Nginx 公式ドキュメント (英語)](http://nginx.org/en/docs/)**: 最も確実な情報源です。
* **[Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)**: 安全なSSL設定を自動生成してくれるツールです。