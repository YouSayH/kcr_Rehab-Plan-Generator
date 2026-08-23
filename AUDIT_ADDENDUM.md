# 監査レポート 追補（穴埋めパス・完走）

本追補では、過剰な重複統合によって潰されていた「unused」「architecture」領域と、個別検証を経ずに丸められていた medium/low 群を掘り起こし、あわせて元の監査で省略された完全性スイープ（エントリポイント・依存管理・Cookie/TLS 設定・CDN 供給網・RAG 知識ベースの更新経路）を実施しました。その結果、反証に耐えた新規指摘13件（critical 1件・high 4件・medium 4件・low 4件）を追加します。うち RAG 知識ベースの残留問題2件は根本原因が同一のため1件に統合しています。

本パスは、初回統合で過剰に圧縮された unused/architecture 領域の回収と、
打ち切りで未実行だった完全性クリティック＋二次探索を実施したものです。
新規候補 65件 → 反証パス通過 **13件**。

## 新規確定指摘 (13件)

### [CRITICAL] add-01 schema.sqlがinitdbで既知平文パスワードの管理者アカウントを必ず投入する（ハッシュと平文の一致を検証済み）

- area: infra / file: `schema.sql:160`

**問題**: docker-compose.yml:64 が schema.sql を /docker-entrypoint-initdb.d/1_schema.sql としてマウントしているため、DBコンテナの初回起動時にサンプルデータのINSERT群が必ず実行されます。この中に、平文パスワードをコメントに併記したまま管理者 yamada（adminpass）と一般職員 sato（password123）を投入する文が含まれています。ハッシュが実際にその平文と一致することを scrypt の再計算で確認済みで、総当たりもレインボーテーブルも不要です。アプリ側にはパスワード変更機能が一切存在せず（ルートを全列挙しても /change_password 相当は無く、パスワード入力欄は login.html と signup.html のみ）、初回変更の強制もありません。したがってデプロイした全環境に既知の管理者資格情報が恒久的に存在します。具体的な被害としては、病院ネットワークに docker-compose up -d した直後から yamada / adminpass で管理者ログインが成立し、@admin_required 配下の /manage_assignments で任意職員へ任意患者を割り当て（be-06 参照）、全患者の氏名・生年月日・算定病名・FIM 等の要配慮個人情報を閲覧して Excel としてダウンロードできます。be-m16 によりログイン試行のレート制限も無いため検知も遅れます。さらにアカウントを削除しても、README.md:371 のローカル手順や新環境構築のたびに元のハッシュごと再投入され、ON DUPLICATE KEY UPDATE 句が role を 'admin' に復元します。155-157行の「本番環境でのデータベース作成では使わないでください。」は単なるコメントで、本番用スキーマファイルへの分離は行われていません。README.md:303-305 の「変更することを推奨します」も任意手順にすぎず技術的統制ではないうえ、README.md:336 が「デフォルト: admin / adminpass」と資格情報自体を公開しています。

```
schema.sql:156-171（コメントに平文パスワードを併記したまま管理者を投入）
-- -- 7. サンプルデータの挿入 本番環境でのデータベース作成では使わないでください。
-- 職員1: yamada さん (管理者 / パスワード: adminpass)
INSERT INTO staff (`id`, `username`, `password`, `occupation`, `role`)
VALUES (1, 'yamada', 'scrypt:32768:8:1$JlKJ01aekkBsObaa$73e73e06...435131', '理学療法士', 'admin')
 ON DUPLICATE KEY UPDATE `username`=`username`, `occupation`='理学療法士', `role`='admin';

schema.sql:172-177
-- 職員2: sato さん (一般 / パスワード: password123)
INSERT INTO staff (...) VALUES (2, 'sato', 'scrypt:32768:8:1$rcfwDMziQwokAhOv$c34b18e7...67972', ...);

docker-compose.yml:63-64
      # 初期化用のSQLファイルをマウント (コンテナ初回起動時に自動実行されます)
      - ./schema.sql:/docker-entrypoint-initdb.d/1_schema.sql

検証（読み取り専用の s
```

**修正**: (1) サンプルデータのINSERT群を schema.sql から物理的に分離し（例: seed_dev.sql）、docker-entrypoint-initdb.d へは本番用スキーマのみをマウントしてください。開発用シードは docker-compose.dev.yml のオーバーライドでのみ読み込む構成にします。(2) 初期管理者はSQLに固定値で埋め込まず、初回起動時に環境変数（INITIAL_ADMIN_USER / INITIAL_ADMIN_PASSWORD）から生成するブートストラップ処理へ置き換え、生成後は必ずパスワード変更を強制してください。(3) staff テーブルに must_change_password BOOLEAN NOT NULL DEFAULT TRUE と password_updated_at を追加し、Flask 側の before_request で当該フラグが立っている間はパスワード変更画面以外へのアクセスを全て拒否してください。(4) 平文パスワードを記したコメント行（160行・172行）を削除し、既にコミット済みのハッシュは漏洩済み資格情報として扱って、稼働中の全環境で該当アカウントのパスワードを即時変更してください。

### [HIGH] add-02 エントリポイントが debug=True を無条件固定し、Werkzeugデバッガ付き開発サーバを 0.0.0.0 でLANに公開している

- area: backend / file: `run.py:12`

**問題**: run.py は12行しかなく、FLASK_DEBUG / FLASK_ENV / os.getenv による分岐が一切ないまま debug=True をハードコードし、さらに host="0.0.0.0" で全インタフェースにバインドしています。導入済み Flask 3.1.3 の app.run は options.setdefault("use_debugger", self.debug) を行うため、use_reloader=False を明示してもデバッガは無効化されません。werkzeug/serving.py:1080-1087 で DebuggedApplication(application, evalex=use_evalex)（use_evalex の既定は True）が全WSGIアプリを包むため、未処理例外はすべて Werkzeug のトレースバックHTML（例外メッセージ・全フレームのソース断片・絶対パス・デバッガsecret）として返り、対話コンソールも載ります。start_app.bat:21 が python run.py を実行して 127.0.0.1:5000 をポーリングしブラウザを自動起動する構成であり、これが想定運用です（README.md 5.4 のローカル起動手順は存在しない python app.py を指しているため、実際に動くローカル起動口はこの run.py 経路だけです）。具体的な被害としては、院内LANの別端末や同一Wi-Fiの見舞客端末から http://<スタッフPCのIP>:5000/ へ接続し、未認証で500を起こすだけで、認証なしにトレースバックページが返り、app/routers/auth.py などのソース断片と C:\Users\<ユーザー名>\OneDrive\Desktop\... という絶対パス、デバッガのsecretトークンが露出します。ホスト制限はクライアント制御の Host ヘッダで判定される（debug/__init__.py:465）ため Host: 127.0.0.1 を送るだけで回避でき、残る関門の9桁PINも uuid.getnode() とマシンIDから決定的に生成されて再起動しても変わらず、start_app.bat が開いたままにするコンソールに常時表示されます。画面共有や肩越しで一度漏れれば永続的に有効で、コンソールから os.environ を読めば DB_PASSWORD・GEMINI_API_KEY・SECRET_KEY を取得でき、患者DBへの直接接続とセッションクッキー偽造が可能になります。なお docker-compose.yml:29 の gunicorn 経由（run:app）は __main__ ガードにより影響を受けませんが、ローカル運用は常にデバッグモードになります。

```
run.py:12（全文12行、分岐なし）
app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)

venv/Lib/site-packages/flask/app.py:627-632（環境変数を足しても引数の True が勝つ）
    if "FLASK_DEBUG" in os.environ: self.debug = get_debug_flag()
    # debug passed to method overrides all other sources
    if debug is not None: self.debug = bool(debug)

venv/Lib/site-packages/flask/app.py:654
    options.setdefault("use_debugger", self.debug)

venv/Lib/site-packages/werkzeug/serving.py:1080-1087
    if use_debugger: application = DebuggedApplication(application, evalex=use_evalex)

werkzeug/debug/__init__.py:336-370 — トレースバックHTMLは check_host_trust と無関係に500で返る。host trust の判定(:465)は Host ヘッダ由来で、sansio/utils.py:53 がポー
```

**修正**: run.py の debug=True を環境変数分岐へ置き換え（例: debug = os.getenv("FLASK_DEBUG") == "1"、既定は False）、既定バインドを 127.0.0.1 にしてください。LAN公開が必要な場合のみ nginx + gunicorn/waitress 経由とします。開発時でも app.run(..., use_debugger=False, use_evalex=False) を明示してインタラクティブデバッガを無効化してください。start_app.bat も python run.py ではなく本番用WSGIサーバ（Windows なら waitress-serve --listen=127.0.0.1:5000 run:app）を起動するよう変更し、README.md の起動手順も併せて更新してください。

### [HIGH] add-03 セッションCookieのセキュリティ属性が皆無、かつnginxがTLS無しのHTTP専用（要配慮個人情報のCookieとパスワードが平文で流れる）

- area: backend / file: `app/__init__.py:40`

**問題**: app/__init__.py:37-40 の設定は SECRET_KEY と PERMANENT_SESSION_LIFETIME だけで、SESSION_COOKIE_SECURE / SESSION_COOKIE_SAMESITE はリポジトリ全体で0ヒットです。導入済み Flask 3.1.3 の既定値は SECURE=False / SAMESITE=None（HttpOnly のみ既定で有効）なので、セッションCookieには Secure も SameSite も付きません。さらに nginx/default.conf は listen 80; のみで TLS も HTTPS リダイレクトも HSTS も無く、docker-compose.yml も 80番だけを公開しています。nginx/README.md:130 は「### A. HTTPS化 (SSL/TLS) [必須]」と自ら必須と明記しており、未実装であることを認めています。具体的な被害としては、院内無線LANや共用セグメント上で ARP スプーフィング等により通信を傍受されると、(1) POST /login の本文から療法士の username / password が平文で取得され、(2) 応答の Set-Cookie: session=... に Secure も SameSite も付かないため以後の全リクエストで平文のセッションCookieが繰り返し流れ、そのままコピーできます。攻撃者は自分のブラウザにこのCookieを貼るだけで当該療法士として認証され、患者氏名・診断名・ADL・生成済みリハビリ計画書へ無制限にアクセスできます。既報 be-05 のとおりログアウトしてもDB側の session_token は消えないため、被害者がログアウトしても盗まれたCookieは当該職員が次にログインして新トークンを発行するまで有効なまま残ります。SameSite 属性が無いことで、既報 be-06 の GET ベースの破壊的管理操作（delete_staff / unassign）もクロスサイトのリンクや画像読み込みだけで発火し得ます。付随して flask_wtf/csrf.py:291 の Referer 検証は request.is_secure を条件とするため、HTTP 運用では一度も走りません。

```
app/__init__.py:37-40（以降 :69 の return app まで Cookie 属性の設定は無し）
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=540)
→ SESSION_COOKIE_SECURE|SESSION_COOKIE_SAMESITE|SESSION_PROTECTION|REMEMBER_COOKIE|ProxyFix を venv 除外で全体 grep した結果、ヒットは tests/conftest.py:42 の "WTF_CSRF_ENABLED": False のみ。Talisman / after_request / set_cookie / Strict-Transport-Security も0件。

venv/Lib/site-packages/flask/app.py:193-196（既定値）
            "SESSION_COOKIE_HTTPONLY": True,
            "SESSION_COOKIE_SECURE": False,
            "SESSION_COOKIE_SAMESITE": None,

nginx/default.conf:1-3（ssl / listen 443 / return 301 / HSTS は0ヒット、X-Forwarded-Proto も
```

**修正**: (1) nginx/default.conf を listen 443 ssl; ＋証明書指定に変更し、80番は return 301 https://$host$request_uri; のみにしてください。add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always; を追加し、docker-compose.yml の ports に "443:443" を追加します。(2) app/__init__.py の基本設定に SESSION_COOKIE_SECURE = True、SESSION_COOKIE_SAMESITE = "Lax"、SESSION_COOKIE_HTTPONLY = True を明示してください。(3) TLS を上位ロードバランサで終端する構成を採るなら、default.conf にも host_proxy.conf:10 と同じ proxy_set_header X-Forwarded-Proto $scheme; を追加したうえで、create_app 内で app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1) を適用し、Flask 側の request.is_secure と Secure Cookie が正しく機能するようにしてください。

### [HIGH] add-04 本番Dockerイメージが完全に無ピンの requirements.txt からビルドされ再現性がゼロ（ロックファイルも不在）

- area: infra / file: `requirements.txt:1`

**問題**: Dockerfile:24-26 がビルドに使う requirements.txt は21行すべてバージョン指定が無く（== の出現数0）、poetry.lock / requirements.lock / constraints.txt / pyproject.toml のいずれもリポジトリに存在しません（git ls-files で確認、追跡されている依存記述は requirements.txt / requirementsCPU.txt / requirementsGPU.txt / Rehab_RAG 配下2本の計5本のみ）。同じコミットから docker compose build しても、実行した日によって別のライブラリ構成のイメージが出来上がります。しかもドリフトは仮説ではなく既に発生済みで、リポジトリ内の venv/ を実測すると、唯一ピン留めされた requirementsGPU.txt の想定構成から google-genai 1.31.0→2.12.1、chromadb 1.0.20→1.5.9、bcrypt 4.3.0→5.0.0、protobuf 6.32.0→7.35.1 と主要4パッケージがメジャーを跨いで乖離しています。具体的な被害としては、リハビリ計画書の文面が「先週と違う」という報告を受けても、先週のイメージを再現する手段が存在しません。たとえば chromadb が 1.0→1.5 へ黙って上がることで Rehab_RAG/rag_components/retrievers/chromadb_retriever.py:39-42 の get_or_create_collection(name=..., metadata={"hnsw:space": "cosine"}) の挙動（既存コレクションのメタデータ扱い）が変わり、検索結果すなわち計画書に引用される診療ガイドラインが再ビルド前後で変化しても、どのバージョン差で変わったのかを事後に特定できません。医療文書の生成根拠を後から検証できないという監査上の欠陥になります。なお README.md:182 および :357 も開発者に pip install -r requirements.txt を案内しており、Docker ビルドと開発環境の双方が無ピン経路です。

```
requirements.txt（全21行、== / >= / ~= の出現は0件）
Flask / Flask-Login / Flask-WTF / gunicorn / Werkzeug / SQLAlchemy / PyMySQL / google-genai / google-api-core / googleapis-common-protos / chromadb / rank-bm25 / mecab-python3 / pydantic / python-dotenv / openpyxl / bcrypt / requests / ollama

Dockerfile:24-26（ピン留め済みの requirementsGPU.txt は Dockerfile から一切参照されない）
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

実際の解決結果（venv/Lib/site-packages の dist-info。pytest 系が無く gunicorn-26.0.0 があるため requirements.txt 由来と確定）:
google_genai-2.12.1 / chromadb-1.5.9 / bcrypt-5.0.0 / protobuf-7.35.1 / pydantic-2.13.4 / flask-3.1.3 / werkzeug-3.1.8 /
```

**修正**: requirements.txt を「直接依存の意図バージョン範囲」を書く入力ファイルと位置づけ、pip-compile（pip-tools）または uv pip compile で全推移依存をハッシュ付きで固定した requirements.lock を生成してリポジトリにコミットしてください。Dockerfile:24-26 を COPY requirements.lock . → RUN pip install --no-cache-dir --require-hashes -r requirements.lock に変更します。最低限の暫定対応としては、現在 venv で動作確認済みのバージョンを pip freeze して requirements.txt に == で書き戻し、requirementsGPU.txt との差分を意図的なものだけに整理してください。依存更新は必ずロックファイルの差分を伴う独立したコミットとし、更新時に生成物の回帰確認を行う運用にします。

### [HIGH] add-05 知識ベースに削除経路が存在せず、BM25（全上書き）とChromaDB（upsertのみ）の更新セマンティクス非対称で撤回・改訂済みガイドラインが孤児チャンクとして残り続ける

- area: ai / file: `Rehab_RAG/experiments/hybrid_search_experiment/build_database.py:49`

**問題**: build_database.py:44-50 は「# 既存DBを削除」というコメントの直下で shutil.rmtree をコメントアウトして pass に置き換えており（しかも import 節19-23行に shutil が無いため、49行を復活させても NameError になります）、この状態は7つの experiments/*/build_database.py 全てで同一です。一方 ChromaDBRetriever の書き込み経路は :79 の upsert のみで、Rehab_RAG 配下に .delete( や delete_collection は1件も存在しません。つまりベクトル索引は追記しかできない構造であり、撤回・改訂されたガイドライン本文を取り除く手段がコード上に一切ありません。さらに structured_markdown_chunker.py:94-95,129-130 の chunk_id は sha256(f"{file_path}:{chunk_index}:{text_content}") で、本文が1文字変わるか節が1つ挿入・削除されるだけで以降の全チャンクのIDが変わるため、upsert は「更新」にならず旧チャンクが恒久的に残留します。ここに更新セマンティクスの非対称が重なります。HybridRetriever.add_documents（:96-97）は同じ chunks を両索引へ渡しますが、BM25 側は bm25_retriever.py:56-63 で index_path を 'wb' で開き pickle.dump((self.bm25, self.chunks), f) と今回分だけで丸ごと書き潰す（過去分は消える）のに対し、ChromaDB 側は残ります。しかも HybridRetriever の RRF（hybrid_retriever.py:48-59）は各索引のランクを単純加算するだけで、片側にしか存在しない文書を除外・減点する仕組みがありません。具体的な被害としては、あるガイドラインが改訂され「早期からの full weight bearing を推奨する」が「推奨しない（禁忌）」に変わった、あるいは文献が完全に撤回されて担当者が source_documents から md を削除して再構築した場合、BM25 側からは正しく消えるのに ChromaDB 側には旧本文が残り、ベクトル検索でのみヒットする孤児になります。rag_executor.py:254 は n_results=20 で検索し、孤児チャンクも 1/(k+rank+1) の正のRRFスコアを得て最終結果に残るため、rag_executor.py:182 の「医学的な正確性を担保するために参照してください」というプロンプトに旧版本文が {context} として混入し、LLM が撤回済みの推奨に沿った運動負荷を計画書に書き出します。confirm.html:1120 の参照情報パネルには「出典[n]: ファイル名」としか出ないため療法士は旧版であることを判別できず、しかも BM25 からは消えているためキーワード検索で混入を確認することすらできません。README.md:317 は「一度実行すればOK」と書いており、再構築・更新の手順自体が文書化されていません（docker-compose.yml:39 は名前付きボリュームではなく ./rag_db_data のバインドマウントなので、README.md:341 の docker-compose down -v でも消えません）。なお本パイプラインは実験用の死蔵コードではなく、ルートの rag_config.yaml:4 が active_pipeline: "hybrid_search_experiment" を指し、docker-compose がその db ディレクトリをマウントする本番構成です。

```
Rehab_RAG/experiments/hybrid_search_experiment/build_database.py:44-50（7ファイル全てで同一）
    # 既存DBを削除
    if os.path.exists(full_db_path):
        # print(f"既存のデータベース '{full_db_path}' を削除します。")
        # shutil.rmtree(full_db_path)
        pass
→ import 節(19-23行)に shutil が無い。リポジトリ全体(venv除く)で rmtree|delete_collection|\.delete\( は上記コメント行以外0ヒット。

chromadb_retriever.py:79（クラス唯一の書き込み経路。delete系メソッドは1-119行に存在しない）
            self.collection.upsert(

bm25_retriever.py:56-63（今回のチャンクで全上書き）
        self.chunks = chunks
        with open(self.index_path, 'wb') as f:
            pickle.dump((self.bm25, self.chunks), f)

hybrid_retriever.py:48-52（ベクトル側だけに居るIDにも無条件でRRFスコアが付く）
        for rank, doc_id in enumera
```

**修正**: (1) build_database.py の削除処理を復活させる（shutil の import 追加を含む）か、少なくとも --rebuild フラグで明示的に全消去できるようにしてください（7ファイル全て）。(2) 恒久策として ChromaDBRetriever に delete_by_source(source_filename) を実装し、build 時に「その md ファイル由来の既存チャンクを collection.delete(where={"source": ...}) で全削除 → 新チャンクを add」という source 単位の入れ替えに、BM25 側と揃えてください。(3) source_documents から md を削除した場合に備え、build 後に「DB内に存在するが今回のチャンク集合に無いID」を検出して削除する孤児掃除ステップを追加してください。(4) 移行期の安全策として、HybridRetriever.retrieve の最後で keyword_retriever.chunks のID集合に含まれないベクトル側IDを孤児として除外またはログ警告してください。(5) 構築完了時に ChromaDB の count() と BM25 の len(chunks) が一致するかを検証し、不一致なら明示的にエラー終了させてください（現行 build_database.py:122-125 は件数を表示するだけです）。(6) 知識ベース更新手順（改訂時に何を実行するか、誰が承認するか）を README に明記してください。

### [MEDIUM] add-06 Gemini APIクライアントにタイムアウトが無く、SSE生成がgunicornスレッドを無期限に占有する

- area: ai / file: `app/services/llm/gemini.py:35`

**問題**: app/services/llm/gemini.py:35 が genai.Client() を http_options 無しで生成しているため、SDK が構築する httpx クライアントの timeout が None になり、さらにリクエスト単位でも None が渡されて（_api_client.py:1349 → :1361 → :1417）全タイムアウトが無効化されます。サーバ側デッドラインヘッダも付きません。唯一のAPI呼び出し口である :315-319 の generate_content にも timeout 指定はなく、リポジトリ全体を grep しても他所でタイムアウトを注入している箇所は存在しません。具体的な被害としては、Gemini エンドポイントがTCP接続は受け付けるが応答を返さない状態（ネットワーク分断や Google 側障害）になると、_call_api_with_retry の generate_content が戻らず、/api/generate/general の SSE レスポンスを生成中のスレッドが解放されません。docker-compose.yml:29 の gunicorn は --workers 1 --threads 8 なので、この状態のリクエストが8本たまるとログイン画面を含む全リクエストが処理不能になります。gunicorn の --timeout 300 は救いになりません。threads>1 により gthread ワーカーが選択され、gthread.py:369-380 の accept ループが毎周 notify するため、リクエストスレッドがブロックしていてもアービタのタイムアウトで殺されず、restart: always も発火しません。nginx/default.conf:25-27 の proxy_read_timeout 300 はクライアント側接続を切るだけで、Google 側読み取りでブロック中のワーカースレッドは解放されません。ResourceExhausted / ServiceUnavailable しか捕捉していないためリトライにも乗らず、療法士側の画面は「生成中」のまま無限に待たされます。app/services/llm/__init__.py:19 で LLM_CLIENT_TYPE の既定が "gemini" であるため、これは既定経路です。対比として app/services/llm/ollama.py:29,107-108 は GENERATION_TIMEOUT_SEC = 60 で自前のタイムアウトを持っており、Gemini 経路だけが無防備という非対称になっています。

```
app/services/llm/gemini.py:35
    client = genai.Client()

app/services/llm/gemini.py:315-319（唯一のAPI呼び出し口。timeout指定なし）
                return client.models.generate_content(
                    model="gemini-2.5-flash-lite",
                    contents=prompt,
                    config=config
                )

venv/Lib/site-packages/google/genai/types.py:2510-2511
    HttpOptions.timeout: Optional[int] = Field(default=None)

venv/Lib/site-packages/google/genai/_api_client.py:1068-1069 / 1349 / 1361 / 1412-1417
      if 'timeout' not in args: args['timeout'] = None
      timeout_in_seconds = get_timeout_in_seconds(patched_http_options.timeout)  # None のまま
      HttpRequest(timeout=timeout_
```

**修正**: genai.Client(http_options=types.HttpOptions(timeout=120_000))（ミリ秒指定）でリクエスト単位のタイムアウトを設定し、送出される httpx.TimeoutException / genai.errors.APIError を _call_api_with_retry（gemini.py:320）のリトライ対象例外に加えてください。あわせて gunicorn の --timeout（300秒）より小さい値を選び、タイムアウト時は error イベントを SSE で返して画面を復帰させてください。Rehab_RAG/rag_components/embedders/gemini_embedder.py:40 と Rehab_RAG/rag_components/llms/gemini_llm.py:39 も同様に http_options 無しなので、併せて対処してください。

### [MEDIUM] add-07 CSRFトークンの有効期限（既定1時間）がセッション想定の9時間より短く、長時間の計画書編集が保存時に400で全損する

- area: backend / file: `app/__init__.py:51`

**問題**: app/__init__.py:39-40 はコメントで「9時間後(労働時間8時間+1時間)にタイムアウトする設定」という運用を宣言していますが、WTF_CSRF_TIME_LIMIT はリポジトリ全体で0ヒット（唯一のヒットは tests/conftest.py:42 の WTF_CSRF_ENABLED: False のみ）で、導入済み Flask-WTF の既定値3600秒（60分）がそのまま使われます。csrf.py:222 の setdefault、:99 の _get_config、:110-112 の s.loads(data, max_age=time_limit) → SignatureExpired → ValidationError("The CSRF token has expired.") という経路です。confirm.html:7 と :176-177 の csrf_token はページ描画時に一度だけ生成され、更新機構も下書き保存もありません。CSRFProtect の before_request は POST を無条件に保護し、app/ 配下に @csrf.exempt も CSRFError ハンドラも0ヒットです。重要な点として、app/routers/plan/views.py:38-95 の generate_plan は AI生成の前に confirm.html を返すため、SSE による生成待ち時間もトークンの60分カウントに含まれます。具体的な被害としては、療法士が confirm.html を開き、生成待ちと24項目のAI提案の確認・修正に合計60分超を費やしてから「保存してExcel出力」を押すと、素の 400 Bad Request ページが返り、入力した患者一人分の計画書内容がブラウザから完全に失われます（下書き保存も離脱警告も無く、localStorage / sessionStorage / beforeunload は confirm.html / edit_patient_info.html ともに0ヒット）。_get_csrf_token はフォームの csrf_token と X-CSRFToken ヘッダを同じ経路で検証するため、60分経過後は confirm.html:519 / 597 のいいね操作、:630 / 747 の再生成・プレビュー fetch も全て400になり、UI 上は原因不明の失敗として現れます。2,880行のフォームを持つ edit_patient_info.html の患者情報保存も同じ経路で失われます。なお付随事実として、app/ 全体に session.permanent = True の設定が無いため PERMANENT_SESSION_LIFETIME の540分設定自体が実質死んでおり、宣言された運用意図と実装の乖離はむしろ拡大しています。

```
app/__init__.py:38-40, :51
    # 9時間後(労働時間8時間+1時間)にタイムアウトする設定
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=540)
    ...
    csrf.init_app(app)
→ WTF_CSRF|csrf_exempt|CSRFError|csrf.exempt を venv 除外で全体 grep したヒットは tests/conftest.py:42 の1件のみ。

venv/Lib/site-packages/flask_wtf/csrf.py:222 / 99 / 110-112
        app.config.setdefault("WTF_CSRF_TIME_LIMIT", 3600)
        token = s.loads(data, max_age=time_limit)
    except SignatureExpired as e:
        raise ValidationError("The CSRF token has expired.") from e

venv/Lib/site-packages/flask_wtf/csrf.py:231-239 / 282 / 302-311 → before_request で POST を無条件検査、_is_exempt 該当は app/ 配下0件。

app/web/templates/confirm.html:7, :176-177（
```

**修正**: app/__init__.py の基本設定で CSRF の寿命をセッション寿命に揃えてください。WTF_CSRF_TIME_LIMIT = None（Flask-WTF 推奨。トークンはセッションに紐づくため、セッションCookie自体の寿命が実質の上限になります）にするか、最低でも int(timedelta(minutes=540).total_seconds()) を明示します。併せて @app.errorhandler(CSRFError) を登録し、素の400ではなく「セッションが切れました。再ログインしてください」を返してください。さらに confirm.html / edit_patient_info.html で入力内容を localStorage に退避し、CSRF失敗時に復元できるようにしてください。session.permanent = True が設定されておらず PERMANENT_SESSION_LIFETIME が効いていない点も併せて修正してください。

### [MEDIUM] add-08 BM25インデックス不在の例外がそのまま「安静度・リスク」欄のAI提案として書き込まれ、UIは正常終了と表示する

- area: ai / file: `Rehab_RAG/rag_components/retrievers/bm25_retriever.py:73`

**問題**: BM25Retriever.__init__（:20-42）は index_path を組み立てるだけで存在確認をせず、retrieve() 内の遅延ロード（:86-87）で初めて load_index() が呼ばれ、pkl が無いと :73 で FileNotFoundError を送出します。ChromaDBRetriever.__init__:28-42 は os.makedirs + get_or_create_collection のため DB 不在でも例外を出さず空コレクションになるので、HybridRetriever.retrieve()（:41-42 でベクトル→BM25の順）では例外は BM25 からのみ上がります。rag_executor.execute() の検索ループ（:250-258）にも execute() 全体にも try/except は無く、例外は app/services/llm/gemini.py:266 の包括 except に到達します。そこでは例外文字列（サーバの絶対パスを含む）が main_risks_txt の "update" イベントとして送出され、直後に finished も送られます。具体的な被害としては、インデックス未構築の環境（＝新規デプロイ直後。rag_db_data も experiments/*/db も .gitignore により配布物に含まれず、Dockerfile にも compose にも build_database を走らせる起動処理はありません）で、リポジトリ既定の active_pipeline: "hybrid_search_experiment" のまま「特化モデルのみ」を選んで計画書を生成すると、療法士の画面の「安静度・リスク」欄に `RAG実行エラー: BM25インデックスファイルが見つかりません: /app/Rehab_RAG/experiments/hybrid_search_experiment/db/rehab_rag_experiments_bm25.pkl` という文字列が入ります。confirm.html:1052-1067 は model_type を一切見ずに通常のAI提案として textContent へ描画し、bi-patch-check-fill（確認済みアイコン）まで付与します。model_choice=specialized の場合は :1069-1082 で本文テキストエリアへ直接代入され updateElementStyle まで走ります。続けて finished が送られるため :1146 の赤いエラー表示は一切出ず、checkAllFinished() が緑の「AIによる生成がすべて完了しました。」を表示します（残り16項目は空のまま）。療法士が気づかず保存すれば、患者・家族に交付する様式23_1のR8セル（app/services/excel/mappings.py:17 のマップ先）にサーバ内部の絶対パスが印字されます。この包括 except は BM25 不在に限らず埋め込みAPI失敗や Gemini クォータ超過などあらゆる例外を同じ経路に流し、緑の「完了」表示で全面失敗を隠します。

```
Rehab_RAG/rag_components/retrievers/bm25_retriever.py:66-73
    def load_index(self):
        if os.path.exists(self.index_path):
            with open(self.index_path, 'rb') as f:
                self.bm25, self.chunks = pickle.load(f)
        else:
            raise FileNotFoundError(f"BM25インデックスファイルが見つかりません: {self.index_path}")

app/services/llm/gemini.py:266-270
        except Exception as e:
            logger.error(f"RAG Stream Error: {e}", exc_info=True)
            yield self._create_event("update", {"key": "main_risks_txt", "value": f"RAG実行エラー: {e}", "model_type": "specialized"})
            yield "event: finished\ndata: {}\n\n"

到達性: app/services/rag_manager.py:19 は CWD相対の "rag_con
```

**修正**: (1) BM25Retriever.__init__ で index_path の存在を検証して起動時に失敗させ、retrieve() 内の遅延ロード（:86-87）をやめてください。(2) rag_executor.execute() の検索ループ（:250-258）を try/except で囲み、検索失敗は {"error": ...} という戻り値契約に正規化して返し、gemini.py:212 / ollama.py:277 の既存エラー分岐（全17項目にエラーを表示する側）に乗せてください。(3) gemini.py:266 の包括 except が計画書フィールド main_risks_txt に生の例外文字列を書き込むのをやめ、ollama.py:326-328 と同様に event: error として送出してください。ユーザ向けは汎用文言のみとし、サーバ内部の絶対パスや例外文字列を画面・保存データに出さないでください。

### [MEDIUM] add-09 計画書プレビュー画面が第三者CDNからSRI無しでスクリプトを読み込み、同一DOMに計画書Excel全体を埋め込んでいる

- area: frontend / file: `app/web/templates/preview_viewer.html:85`

**問題**: 患者の計画書そのものをレンダリングする preview_viewer.html は、luckysheet / luckyexcel の CSS 4本（:10-13）と JS 3本（:83-85）を cdn.jsdelivr.net から読み込んでいますが、integrity= 属性が1つも無く（リポジトリ全体の grep で0件）、CSP も存在しません（Content-Security-Policy / Talisman / add_header の全文検索でヒットしたのは nginx/README.md:156-160 のドキュメント例のみで、実際に読み込まれる nginx/default.conf には add_header が1行もありません）。:85 の luckyexcel はバージョン指定すら無く、常に最新版が配信されます。しかも同じページの :91 で計画書Excel全体を base64 で埋め込んでいます。自ホスト版への切り替えも直ちにはできません。コメントアウトされた :14-17, :86-88 の参照先 app/web/static/lib/luckysheet/ は実在せず、コミット bb2ae77「JSライブラリの除外」で 25,887行が削除され .gitignore に app/web/static/lib/* が追加されており、CDN が唯一の供給元です。具体的な被害としては、セラピストが確認画面で「プレビュー」を押すと /api/preview_plan が患者の氏名・生年月日・障害名・FIM/BI・目標・本人家族の希望まで含んだ計画書Excelを base64 で埋め込んだ HTML を返し、その同じページが cdn.jsdelivr.net から3本のJSを実行します。luckyexcel パッケージのnpmアカウント乗っ取りやCDNのキャッシュ汚染が1回起きれば、配信された luckyexcel.umd.js が LuckyExcel.transformExcelToLucky で受け取った ArrayBuffer（＝計画書Excelそのもの）を攻撃者サーバへ POST するだけで、以後プレビューを開いた全患者の計画書が外部へ流出します。SRI が無いためブラウザは改竄を検知せず、CSP が無いため外向き fetch も阻止されず、サーバ側のログにも痕跡が残りません。要配慮個人情報の漏えいが検知不能なまま継続します。さらに confirm.html:774 は iframe.srcdoc = html として描画し sandbox 属性が無いため、改竄されたJSは埋め込み計画書だけでなく親アプリのセッションで任意の同一オリジンAPIを叩けます。既報のXSS（fe-01 / fe-m01 / fe-m09）はアプリ側の出力エスケープ欠陥ですが、これはアプリのコードを一切変更せずに第三者が任意コードを実行できる供給網リスクで、経路も対策も別物です。なお同種のSRI無しCDN読み込みは preview_viewer.html だけでなく confirm.html:9,14,16,20,357（bootstrap / bootstrap-icons / marked / mermaid の5本）、edit_patient_info.html:2621（chart.js）、regeneration_summary.html:8 にも存在し、confirm.html は計画書本文・所見・患者識別情報を保持する親ページであるため影響範囲はより広くなります。

```
app/web/templates/preview_viewer.html:83-85（integrity 無し。:85 はバージョン指定も無し）
    <script src="https://cdn.jsdelivr.net/npm/luckysheet@2.1.13/dist/plugins/js/plugin.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/luckysheet@2.1.13/dist/luckysheet.umd.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/luckyexcel/dist/luckyexcel.umd.js"></script>

app/web/templates/preview_viewer.html:91
        const base64Data = "{{ excel_base64 }}";

app/web/templates/preview_viewer.html:86-88（自ホスト版はコメントアウト済み。参照先は実在しない）
    <!-- <script src="{{ url_for('static', filename='lib/luckysheet/luckyexcel.umd.js') }}"></script> -->

grep -rn "integrity=" --include=*.html . → 0件。nginx/default.conf 全
```

**修正**: (1) app/web/static/lib/luckysheet/ にベンダリングした自ホスト版へ戻し（:86-88 のコメントアウト行を復活させるだけでは動きません。bb2ae77 で削除されたファイル群の再ベンダリングと .gitignore の見直しが必要です）、外向き通信を不要にしてください。自ホスト化が直ちに困難な場合は最低限 integrity="sha384-..." crossorigin="anonymous" を全 <link>/<script> に付与し、:85 のバージョン無指定も固定してください。(2) nginx/default.conf に add_header Content-Security-Policy "default-src 'self'; script-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'" always; を追加し、少なくとも connect-src を自オリジンに限定して埋め込み計画書の外部送信を遮断してください。(3) 対策は preview_viewer.html 単体ではなく、confirm.html / edit_patient_info.html / regeneration_summary.html を含む全テンプレート横断で実施してください。(4) confirm.html:774 の srcdoc iframe に sandbox 属性を付与し、プレビューを親オリジンから隔離してください。

### [LOW] add-10 admin.pyが別ライブラリのIntegrityErrorを捕捉しており、重複割り当て分岐が到達不能で生SQLが画面に露出する

- area: backend / file: `app/routers/admin.py:78`

**問題**: app/routers/admin.py:3 は from pymysql.err import IntegrityError を import していますが、crud層が再送出するのは sqlalchemy.exc.IntegrityError です（app/crud/staff.py:1,77-79）。venv の sqlalchemy 2.0.51 / pymysql 1.2.0 で実測したところ、sqlalchemy.exc.IntegrityError の MRO は DatabaseError→DBAPIError→StatementError→SQLAlchemyError→HasDescriptionCode→Exception のみで、両者に継承関係はありません（issubclass は False）。したがって :78 の except 節は成立しません。具体的な被害としては、管理者が manage_assignments 画面で既に割り当て済みの職員×患者の組を再度「割り当てる」と、staff_patients の複合主キー制約違反（app/models/staff.py:10-15、schema.sql:61-67）により crud/staff.py:79 が sqlalchemy.exc.IntegrityError を再送出し、:81-82 の汎用ハンドラに落ちます。管理者には意図された「その担当者は既にその患者に割り当てられています。」ではなく、INSERT INTO staff_patients ... の生SQLとバインドパラメータを含む SQLAlchemy の例外文字列がそのまま flash 表示されます。しかも crud/staff.py:75 の staff.assigned_patients.append(patient) は unassign 側（:89 の patient in staff.assigned_patients）と異なり重複チェックが無く、manage_assignments.html:130-135 の患者セレクトが割当済みを絞り込まず全件列挙しているため、管理画面の通常操作だけで再現します。app/__init__.py に errorhandler の登録も無いため（grep 済み）、他所で救済されることもありません。

```
app/routers/admin.py:3
from pymysql.err import IntegrityError

app/routers/admin.py:75-82
        try:
            staff_crud.assign_patient_to_staff(staff_id, patient_id)
            flash("患者を割り当てました。", "success")
        except IntegrityError:
            flash("その担当者は既にその患者に割り当てられています。", "warning")
        except Exception as e:
            flash(f"割り当て中にエラーが発生しました: {e}", "danger")

実際に送出されるのは SQLAlchemy 側 — app/crud/staff.py:1,77-79
from sqlalchemy.exc import IntegrityError
    except IntegrityError:
        db.rollback()
        raise

実測: issubclass(sqlalchemy.exc.IntegrityError, pymysql.err.IntegrityError) → False
app/models/staff.py:10-15 / schema.sql:61-67 → PRIMARY KEY (staff_id, 
```

**修正**: admin.py:3 を from sqlalchemy.exc import IntegrityError に変更して型を一致させてください。さらに根本的には、app/crud/staff.py:75 の append 前に unassign 側（:89）と同じく if patient not in staff.assigned_patients: を挟んで冪等にし、例外に依存しない実装にしてください。:81-82 の汎用ハンドラも f"...{e}" をやめ、app.logger.exception でログに残して画面には定型文のみ返してください。manage_assignments.html:130-135 の患者セレクトから割当済みを除外することも併せて検討してください。

### [LOW] add-11 参照パネルの goals_dischage_destination_chk 綴り誤りで退院先チェックが常に未チェック表示になる

- area: frontend / file: `app/web/templates/components/patient_info_ref.html:1289`

**問題**: discharge が dischage になっており、Jinja の未定義属性は falsy になるため、退院先が設定済みでも参照パネルでは常に未チェックとして描画されます。リポジトリ全体を dischage で grep するとヒットは patient_info_ref.html:1289 と :1290 の2箇所のみで、他はすべて正綴り goals_discharge_destination_chk です（app/models/plan.py:239、schema.sql:289、app/schemas/schemas.py:380/776、app/services/excel/mappings.py:117、app/services/extraction/fast_extractor.py:280、edit_patient_info.html:1413、view_plan.html:711、liked_item_detail_view.html:1309）。app/crud/patient.py:26-47 の get_patient_data_for_plan は __table__.columns から dict を構築するため誤綴りキーは存在せず、app/__init__.py に StrictUndefined の設定も無いので、Flask 既定の Undefined として例外にならず黙って falsy になります。具体的な被害としては、edit_patient_info.html で「退院先」にチェックを入れ「自宅」と入力して保存した患者について、confirm.html:72 のインクルードおよび app/routers/plan/views.py:190 の /api/render_plan_history が patient_info_ref.html を描画すると、退院先チェックボックスが未チェックで表示されます。隣接する goals_discharge_destination_txt（綴り正常）には「自宅」が表示されるため、療法士は「退院先の目標は未設定なのに自宅と書かれている」という矛盾した参照画面を見ながら計画書を確認することになります。なお :1290 の data-bind 属性は読み手のJSがリポジトリ全体で皆無（*.js に0件）なので無害な死属性であり、実害は :1289 の Jinja 式のみです。影響は disabled の参照専用チェックボックスの表示に限られ、Excel 出力や view_plan.html は正綴りを使うため保存データや帳票には波及しません。

```
app/web/templates/components/patient_info_ref.html:1288-1290
                            <input class="form-check-input mt-0 me-1" type="checkbox" {% if
                                patient_data.goals_dischage_destination_chk %}checked{% endif %}
                                data-bind="goals_dischage_destination_chk" disabled> 退院先

正しいカラム名 — app/models/plan.py:239
    goals_discharge_destination_chk = Column(Boolean, default=False)

入力側は正しい綴り — app/web/templates/edit_patient_info.html:1413-1414
                                            name="goals_discharge_destination_chk" value="on" {% if
                                            patient_data.goals_discharge_destination_chk %}che
```

**修正**: 1289行と1290行の goals_dischage_destination_chk を goals_discharge_destination_chk に修正してください。再発防止として、テンプレート内の patient_data.* 参照キーが RehabilitationPlan.__table__.columns と Patient.__table__.columns に存在することを検証するテストを tests/ に追加してください。同種の綴り不整合はテンプレート約10,000行の他の箇所にも潜在し得るため、機械的な全キー照合を推奨します。

### [LOW] add-12 送信ボタンをdisabledにしたままbfcache復帰し、ブラウザバック後に計画書を作成できなくなる

- area: frontend / file: `app/web/templates/index.html:82`

**問題**: index.html:78-87 は DOMContentLoaded 内で submit ハンドラを登録し、:82-85 でボタンを恒久的に disabled へ変えていますが、解除コードがありません。pageshow / persisted / beforeunload / unload の grep は app/ 全体で0件で、復元ハンドラはどのテンプレートにも存在しません。app/web/static/ には style.css と空の lib/ しか無く共通JSも存在しません。app/routers/plan/views.py:38-96 の generate_plan は POST に対し redirect せず render_template("confirm.html", ...) を直接返すため、履歴は index.html(GET) → confirm.html(POST結果) となり、バックの戻り先は index.html の GET エントリで bfcache 対象になります。bfcache の阻害要因も無く（app/__init__.py に after_request やレスポンスヘッダ操作は無し、Cache-Control / no-store はコード全体で0件、nginx/default.conf の location / はキャッシュ制御ヘッダを付けない、index.html に unload/beforeunload/SSE も無し）、適格です。具体的な被害としては、療法士が患者Aを選び「計画書を作成」を押すとボタンが disabled かつ「作成中...」になって confirm.html へ遷移し、生成内容を見て「患者を間違えた」と気づいてブラウザバックすると、index.html は bfcache から復元されるがインラインスクリプトは再実行されないため、submit-button は disabled=true・textContent='作成中...' のまま固まります。患者Bを選び直してもボタンを押せず、画面には永遠に「作成中...」と表示されるため、利用者はシステムがハングしたと誤認します（復帰にはページのリロードが必要です）。なお confirm.html:352 の #submit-button は HTML 属性で初期 disabled、:952 の checkAllFinished() が SSE 完了時に disabled=false にするため、bfcache 復元時は有効化済み状態が保存され固着しません。したがって本件は index.html 固有です。

```
app/web/templates/index.html:78-87
    <script>
        document.addEventListener('DOMContentLoaded', function () {
            const form = document.getElementById('rehab-form');
            const submitButton = document.getElementById('submit-button');
            form.addEventListener('submit', function () {
                submitButton.disabled = true;
                submitButton.textContent = '作成中...';
            });
        });
    </script>

grep -rn "pageshow|persisted|beforeunload|unload" app/ → 0件。app/web/static/ には style.css と空の lib/ のみ。
app/routers/plan/views.py:38-96 → POST に対し redirect せず render_template("confirm.html", ...) を返す（戻り先の index.html GET が bfcache 対象）。
Cache-Contro
```

**修正**: index.html のスクリプトに復元ハンドラを追加してください: window.addEventListener('pageshow', function (e) { if (e.persisted) { submitButton.disabled = false; submitButton.textContent = '計画書を作成'; } });。あわせて、二重送信防止の共通処理を app/web/static/ 配下の静的JSに切り出し、今後同種のボタン制御を追加する画面でも再利用できるようにしてください。

### [LOW] add-13 1_generate.py が存在しないモジュールを import する完全な死蔵ファイル（入力データも参照カラムも不在）

- area: unused / file: `1_generate.py:10`

**問題**: リポジトリ直下の生成評価スクリプト 1_generate.py（23KB）は、LLM層のパッケージ化以前のトップレベルモジュール gemini_client / ollama_client を try/except 無しで import しており、それらは現在リポジトリに存在しないため起動時に必ず ModuleNotFoundError で死にます（git ls-files でも venv 除外の find でも0件。venv にあるのは ollama パッケージであって ollama_client ではなく、gemini_client に至ってはパッケージ自体が存在しません）。CELL_NAME_MAPPING の実体は app/services/llm/context_builder.py:9 へ移動済みです。加えて入力データ 0_validation_dataset.json も存在せず（.gitignore / .dockerignore にも記述が無いので単に未コミット）、:35 の MANUAL_MAPPING が参照する header_treatment_details_txt は作業ツリーの schema.sql から削除済みのカラムです（git show HEAD:schema.sql:84 にはあるが現行には grep 0件）。具体的な被害としては、生成品質を評価しようとした開発者が、同じルート直下にある debug_parser.py:13 / evaluate_extraction_accuracy.py:13（こちらは from app.services.llm.patient_info_parser import PatientInfoParser を使う現行API準拠で動作します）と同列に見えることから python 1_generate.py を実行すると、10行目で即 ModuleNotFoundError: No module named 'gemini_client' が送出されます。import を app/services/llm/ 側へ直しても、今度は INPUT_FILE の 0_validation_dataset.json が存在せず、さらに参照カラムも消えているため動きません。ルート直下に「動く評価スクリプト2本」と「起動不能な評価スクリプト1本」が混在し、どれが生きているのか判別する手段がありません（全 .py/.md/.yml/.bat/.html を grep しても 1_generate への参照は0件、README.md にも debug_parser / evaluate_extraction_accuracy / validation_dataset / evaluation_results いずれの記載もありません）。.dockerignore は *.md や create_hash.py は除外しますが 1_generate.py は除外しないためイメージには同梱されます。実行時のアプリ経路には一切影響せず、被害は開発者の混乱と誤解に限られます。

```
1_generate.py:10-13（try/except 無しのトップレベル import）
import gemini_client
import ollama_client
# マッピング定義を利用するためにインポート
from ollama_client import CELL_NAME_MAPPING

1_generate.py:17
INPUT_FILE = "0_validation_dataset.json"

1_generate.py:35（現行 schema.sql から削除済みのカラムを参照）
    "治療内容": "header_treatment_details_txt",

モジュール不在: git ls-files | grep -i client は0件、venv 除外の find -name "*client*.py" も0件。requirements.txt は google-genai と ollama のみ。
実体の移動先: app/services/llm/context_builder.py:9 の CELL_NAME_MAPPING（:421/:449 で使用）。
入力データ: ls 0_validation_dataset.json → No such file or directory。
カラム消失: git show HEAD:schema.sql:84 に header_treatment_details_txt があるが作業ツリーの schema.sql には0件。
対比（動く方）: debug_parser.py
```

**修正**: 1_generate.py を削除してください（gemini_client / ollama_client 時代の遺物であり、入力データも参照カラムも現行構成と整合しません）。生成品質の評価ハーネスを残す必要があるなら、from app.services.llm import get_llm_client と from app.services.llm.context_builder import CELL_NAME_MAPPING に書き換えたうえで 0_validation_dataset.json（架空患者データ）をコミットし、生きている debug_parser.py・evaluate_extraction_accuracy.py とまとめて tools/ 配下へ移して、README に実行可能なスクリプト一覧を明記してください。

## 残存する未調査範囲（自己申告）

本追補を経てもなお、以下は未点検のまま残っています。完全性は主張できません。

【動的検証は一切していない】アプリの起動、DB の構築、pytest の実行、Excel 出力の実生成のいずれも行っていません。すべて静的読解と venv 内ライブラリのソース確認、および schema.sql のハッシュに対する scrypt 再計算のみに基づいています。したがって、実行時にしか現れない不具合（並行アクセス、SSE の実挙動、MeCab 辞書 user.dic の実効果、openpyxl と template.xlsx の相互作用）は本監査の射程外です。

【テスト群そのものが未レビュー】tests/ 配下18ファイル・約1,850行のうち、個別に読んだのは arch-01 で扱った conftest.py だけです。test_llm_comprehensive.py（250行）、test_llm_detailed_interaction.py（191行）、test_api_routes.py（143行）、test_excel_writer.py（136行）などが「何を検証しているつもりで実際には何も検証していないか」は未確認で、偽陽性の緑（モックが厚すぎて回帰を検出できない類）は洗い出せていません。

【個別精査していないアプリケーションコード】app/utils/decorators.py（19行、権限デコレータ。be-04 の IDOR に直結するにもかかわらず実装そのものは未レビュー）、app/utils/helpers.py、app/core/database.py、app/auth_models.py、app/constants.py、app/models/patient.py、app/models/staff.py、app/services/excel/writer.py（146行）、app/services/fact_db.py（321行）、app/services/patient_service.py（150行）、app/services/extraction/nlp_loader.py、app/services/llm/base.py、app/services/llm/ollama.py（458行。gemini.py と対比した際の言及に留まり通読はしていません）は、いずれも独立した精査対象になっていません。とくに app/schemas/schemas.py は1,177行あり、Pydantic スキーマ・app/models/plan.py・schema.sql の三者間のカラム整合を総当たりで照合していません。add-11 の綴り誤りは同種の不整合が他にも残っている可能性を示す一例と見るべきです。

【テンプレートは通読していない】テンプレート合計約10,000行のうち、行単位で読み切ったものはありません。liked_item_detail_view.html（2,064行）、view_plan.html（1,098行）、edit_patient_info.html（2,880行）、components/patient_info_ref.html（1,874行）はキーワード検索ベースの確認に留まり、data-bind 属性や Jinja 変数名の網羅照合、各画面の XSS シンクの全列挙は未実施です。_suggestion_details.html、liked_details_viewer.html、login.html、signup.html、regeneration_summary.html は事実上ほぼ未点検です。

【Rehab_RAG は本番経路以外が空白】Rehab_RAG 配下46の Python ファイルのうち、実際に精査したのは hybrid_search_experiment 経路（build_database.py、hybrid_retriever.py、bm25_retriever.py、chromadb_retriever.py、structured_markdown_chunker.py、gemini_embedder.py、self_reflective_filter.py、rag_executor.py）に限られます。graph_builder.py、raptor_builder.py、graph_retriever.py、combined_retriever.py、nli_filter.py、retrieval_judge.py、hyde_generator.py、multi_query_generator.py、cross_encoder_reranker.py、gemini_embedding_reranker.py、sentence_transformer_embedder.py、ollama_llm.py、Rehab_RAG/schemas.py、Rehab_RAG/query_rag.py、Rehab_RAG/evaluation/evaluate_rag.py、および graph_rag / raptor / multi_query / self_rag_full_pipeline / graph_hybrid_combined 各 experiment の build_database.py・test.py・config.yaml は未読です。これらは rag_config.yaml の active_pipeline を切り替えるだけで本番経路になります。

【その他の未点検領域】tools/ 配下は unused-m20 で liked_details_viewer.py に触れただけで、check_schema_coverage.py、create_hash.py、Create-Hash.ps1、test.sql、tools/docker-compose.yml は未レビューです。schema.sql は53KB あり、staff / patients / rehabilitation_plans の主要部分以外（suggestion_likes 周辺のインデックス設計、schema_facts.sql、辞書ファイル user.dic / user_dic.csv の内容）は通読していません。依存ライブラリ自体の既知脆弱性照合（chromadb 1.5.9、google-genai 2.12.1 等に対する CVE スキャン）も行っていません。.history/ 配下の履歴ファイルに機微情報が残っていないかも確認していません。

【領域として依然として薄い】「unused」は今回 1_generate.py の1件を回復したにとどまり、未使用関数・未参照テンプレート・死んだ設定項目の体系的な棚卸しはできていません。「architecture」は arch-01 の1件のままで、レイヤ責務の分離、循環依存、トランザクション境界、エラー伝播契約の一貫性といった構造的評価は今回も実施できていません。また、元の監査で個別検証されずに丸められた86件の medium/low 候補群について、本追補で検証できたのは13件相当であり、残余プールを網羅的に再導出したわけではありません。同種の指摘がまだ埋もれている前提で扱ってください。

## 完全性クリティックが特定した未調査領域 (10件)

1. **[backend]** Excelの結合セル解決コードが現行openpyxlで必ず例外を出し、失敗が握り潰されるため、様式23テンプレート（結合セルだらけ）では多数の項目が無言で空欄のまま出力される。実機検証済み: openpyxl 3.1.5 で `ws.merged_cell_ranges` は `TypeError: 'set' object is not subscriptable` を送出し（compat の deprecated シムが `self.merged_cells.ranges[:]` を実行するが ranges は set）、仮にそこを通っても `MergedCellRange` に `min_cell` 属性は存在せず AttributeError になる。既報のbe-10（mappings.pyの_slct二重定義）とは別の欠陥。

2. **[backend]** 「9時間でセッションタイムアウト」というコメント付きの設定が完全な死に設定で、実際にはセッション有効期限が一切存在しない。さらにCookieのセキュリティ属性が一つも設定されておらず、nginxはHTTPのみ。既報のbe-05（ログアウトがDBのsession_tokenを消さない）と組み合わさると、盗まれたセッションCookieを失効させる手段がゼロになる。

3. **[backend]** アプリのエントリポイントが `debug=True` を無条件でハードコードしており、しかもそれがドキュメント化された唯一のローカル起動手段。Werkzeugインタラクティブデバッガ（コンソールからの任意コード実行）と、環境変数・ソース・スタックトレースを晒すエラーページが、患者DBに接続した状態で 0.0.0.0 にバインドされてLANに公開される。30体のエージェントは誰も run.py を見ていない。

4. **[infra]** docker-composeが初回起動時に自動実行するschema.sqlが、平文パスワードをコメントに併記したまま管理者アカウントを投入する。デプロイした時点で既知の管理者資格情報が必ず存在し、初回パスワード変更の強制も無い。既報のbe-03（サンプルINSERTのカラム不整合）とinfra-01（compose内のDB認証情報）とは別問題。

5. **[infra]** 本番イメージが完全に無ピンの依存リストからビルドされており、ビルドの再現性がゼロ。医療文書を生成するシステムで、昨日と今日で異なるライブラリ構成のイメージが出来上がる。既報のbe-12（spacy/ginzaが requirements.txt に無い）は「欠落」の話で、こちらは「バージョン固定の不在」という別の問題。しかもGPU版だけは210行すべてピン留めされており、意図の不整合が明白。

6. **[ai]** ナレッジベースの更新ライフサイクルが壊れており、改訂・撤回されたガイドライン本文がChromaDBに永久に残って計画書生成の「根拠」として引用され続ける。ビルドスクリプトが既存DB削除を明示的に無効化しており、チャンクIDは内容のsha256なので、mdを1文字直すだけで旧チャンクは削除されず新IDが追加される。誰もインデックスの陳腐化を検討していない。

7. **[ai]** RAGインデックスが「空」または「不在」のときの挙動が誰も検証していない。デプロイ直後は必ずこの状態になるのに、片方は無言で空の知識ベースを作り、もう片方は例外を投げ、どちらもハンドリングされていない。既報のai-06（マウント先のパイプライン名ハードコード）とは別で、こちらは起動時検証の不在そのもの。

8. **[frontend]** 患者の計画書そのものをレンダリングする画面が、SRIもCSPも無しで第三者CDNからスクリプトを読み込んでいる。しかも一部はバージョン指定なし（常に最新）。院内クローズド運用を前提にしたシステムなのに、臨床端末からの外向き通信が必須で、CDN側の改竄・破壊的更新がそのまま本番に届き、患者計画書の全内容にアクセスできるDOM権限を持つ。既報のXSS系（fe-01/fe-m01/fe-m09）とは別の供給網リスク。

9. **[infra]** docker-compose.yml が2系統存在し、より完成度の高い方が tools/ に放置され、欠陥のある方が本番用として使われている。既報のinfra-01/02/m17/m19（認証情報直書き・0.0.0.0:3306公開・healthcheck無し・root実行）は、すべて tools/docker-compose.yml では既に解決済み。つまり「修正案が既にリポジトリ内にある」という事実と、その分岐が誰にも管理されていないことが見落とされている。

10. **[unused]** リハビリ専門用語の表記揺れ吸収のために作られたMeCabユーザー辞書（コンパイル済みバイナリ530行相当＋定義CSV 471行）が、実際に検索精度を必要としている経路のどこからも使われていない。唯一の利用者が到達不能なデモモジュールで、その中でも失敗が無言でフォールバックする。BM25をハイブリッド検索に入れている目的（固有名詞・専門用語の取りこぼし防止）が実質達成されていない。

## 反証により棄却 (51件)

- 旧関数 save_liked_item_details が呼び出し0件のまま残置（docstring自身が「削除予定」と宣言）
  - `app/crud/plan.py`
  - コードを実読して検証した（app/crud/plan.py 全体、app/services/plan_service.py:55-95、app/crud/README.md、app/crud/__init__.py、リポジトリ全体grep）。

【事実として認めた点】
- app/crud/plan.py:336-367 に save_liked_item_details は実在し、339行の docstring も確かに「【旧関数・削除予定】いいねされた項目の詳細情報を liked_item_details テーブルに保存する」。
- venv/.git/node_modules を除く全ファイルを include フィルタ無しで grep しても、ヒットは app/crud/plan.py:336 の定義行と __pycache__/plan.cpython-311.pyc のみ。稼働

- get_all_liked_item_details はリポジトリ全体で参照ゼロの死にコード（患者スナップショット全件ロード実装）
  - `app/crud/plan.py`
  - 【1. 参照ゼロ自体は事実だが、指摘の弁別根拠が成立しない】リポジトリ全体（venv除く）を grep した結果、get_all_liked_item_details のヒットは app/crud/plan.py:259 の定義行のみで、参照ゼロは事実。しかし本指摘は「同系統の get_plans_with_liked_details_for_patient / get_liked_item_details_by_plan_id は tools/liked_details_viewer.py から名指しされているのに、これだけがゼロ」という対比を独立欠陥の根拠にしている。この対比は実体を伴わない。tools/liked_details_viewer.py:9 は `from app import ITEM_KEY_TO_JAPANESE` だが、ITEM_KEY_TO_JAPANESE の

- /api/plan_history/<patient_id> エンドポイントに呼び出し元が存在しない（未検証の認可コードが公開URLとして残存）
  - `app/routers/plan/api.py`
  - 「呼び出し元が無い」という事実部分だけは正しいが、指摘の実害（failure_scenario）は成立せず、残るのは死にコード削除という体裁上の意見に過ぎないため棄却する。

1) 事実確認：`app/routers/plan/api.py:211` に `@plan_bp.route("/api/plan_history/<int:patient_id>")` が存在し、リポジトリ全体を `plan_history` / `get_plan_history` で grep しても、ヒットは api.py:211,213 の定義自身と、無関係な別物（`app/routers/plan/views.py:169` の `render_plan_history`、`app/services/patient_service.py:86,133`、`app/routers/plan/views.p

- 権限チェック共通化ヘルパー get_plan_checked がどこからも import されず、各ルートで重複実装が続いている
  - `app/utils/helpers.py`
  - 事実関係（コードの存在と未参照）は確認できたが、指摘は「実害のない設計意見」に留まるため棄却する。

1) 事実確認: app/utils/helpers.py:26-45 に get_plan_checked が定義され、リポジトリ全体（venv除く）の grep 結果は定義行 app\utils\helpers.py:26 の1件のみ。import 側も app/routers/plan/views.py:19、app/routers/plan/api.py:20、tests/test_utils.py:3 が全て has_permission_for_patient のみで、evidence 自体は正しい。

2) しかし「呼ばれていない関数」は実行パスが存在せず、この配備で発生する障害はゼロ。failure_scenario は「新しいルートを追加する開発者が片方を書き忘れうる」と

- 未使用の get_standardization_prompt が _standardize_text 内のインラインプロンプトと二重管理になっている
  - `app/services/llm/patient_info_parser.py`
  - 事実関係は概ね正しいが、指摘内容は実行時の欠陥ではなく整理整頓（デッドコード）に関する意見であり、報告に値する不具合とは言えないため refute する。

【確認した内容】
1. app/services/llm/patient_info_parser.py:74-105 に `def get_standardization_prompt(text: str) -> str:` が存在することは確認した。リポジトリ全体（テンプレート/tests/tools/*.md/*.yaml 含む）を grep した結果、ヒットは定義行 patient_info_parser.py:74 の 1 件のみで、参照 0 件であることも確認した。
2. 実行経路も指摘どおり。app/services/llm/patient_info_parser.py:504 `def parse_text` → :51

- _build_generation_prompt が呼び出し元ゼロ、かつ138行のコメントアウト旧 parse_text が同居し実挙動が読めない
  - `app/services/llm/patient_info_parser.py`
  - 機械的事実（_build_generation_prompt が285-321行に存在し呼び出し元ゼロ／364-501行が旧 parse_text のコメントアウト）は確認できたが、この指摘は「実害のあるバグ」ではなく死蔵コードの整理という体裁上の意見であり、かつ中核の根拠が誤読に基づくため棄却する。

1) 実行経路に一切影響しない（到達不能な失敗）。リポジトリ全体を grep した結果、_build_generation_prompt の出現は app/services/llm/patient_info_parser.py:285 の def 行のみ（他のヒットは venv/Lib/site-packages/click/termui.py 等の無関係な同名関数）。364-501行は全行が `#` で始まる純粋なコメントで、モジュール内の parse_text 定義は504行の1つだけ

- app/services/fact_db.py が孤立モジュール、専用資産 user.dic(117KB)/user_dic.csv(68KB) も未参照でイメージに片方だけ同梱される
  - `app/services/fact_db.py`
  - 事実関係（fact_db.py が import 0件、user.dic/user_dic.csv が同ファイル以外から未参照、.dockerignore:28 が `*.csv` のみ除外）は grep で確認でき正しい。しかし本件は既報の重複＋提示された3つの failure_scenario がいずれも成立しないため、medium の独立指摘としては棄却する。

(1) 重複: covered.json の infra-05「SQLite方言のschema_facts.sqlをMySQLのinitdb.dにマウントしている（**かつ死蔵テーブル**）」が、事実DB機能一式が死蔵であることを既に報告済み。docker-compose.yml:65 が `./schema_facts.sql:/docker-entrypoint-initdb.d/2_schema_facts.sql` 

- bcrypt と requests が requirements.txt に宣言されているが第一者コードに import が0件、READMEも誤った前提を記載
  - `requirements.txt`
  - 前提（未使用・ビルド肥大・README誤記）がいずれも実コードで否定されるため棄却する。

1) `requests` は「未使用」ではなく、Gemini 呼び出し経路で必ずロードされる実行時依存である。`app/services/llm/gemini.py:8` が `from google import genai` を行い、`venv/Lib/site-packages/google/genai/_api_client.py:53` は `import requests` / `:54 from requests.structures import CaseInsensitiveDict` をトップレベルで実行する。`google_genai-2.12.1.dist-info/METADATA` も `Requires-Dist: requests<3.0.0,>=2.28.1`（e

- style.css の .is-invalid-field ルールがどのテンプレート・JSからも参照されない死んだCSS
  - `app/web/static/style.css`
  - 事実関係（8行の未使用CSSが存在すること）は確認できたが、指摘の中核である「障害シナリオ」が実コードで成立せず、実質は死んだCSS 8行の整頓（スタイル上の意見）に留まるため refute する。

1) evidence 自体は正しい。`app/web/static/style.css:412-419` に `.is-invalid-field` / `.is-invalid-field:focus` が存在し、リポジトリ全体を `is-invalid-field` で grep してもヒットはこの2件のみ。JS が付与するのは `is-invalid` だけ（`app/web/templates/edit_patient_info.html:2344,2346,2359,2361,2375,2377,2384,2386`）。`app/web/static/` 配下は `style.c

- models/README.md と crud/README.md が現行コードと正反対の設計方針・安全性保証を記載している
  - `app/models/README.md`
  - 引用文自体はファイルに存在するが（app/models/README.md:19 の「NoSQL（JSON型）に逃げることなく…個別のカラムとして厳密に定義」、:61 の ALTER 文の注意書き、app/crud/README.md:56 の「動的マッピング…一致するものだけを保存します…安全性が保たれます」を実読して確認）、「現行コードと正反対」という前提が成立せず、残る実質は既報告項目の言い換えである。

(1) models/README.md は app/models/ ディレクトリの解説文書であり、その対象である app/models/plan.py は今も RehabilitationPlan を個別カラムで定義したままである（同ファイルを機械的に数えて `Column(` が415箇所、文字列 `plan_data` は0箇所＝JSONカラムは未定義）。つまり README

- core/README.md が存在しない get_db を解説し、Base の依存方向を実装と逆に説明している
  - `app/core/README.md`
  - 実コードを読んだ結果、これは実行時の欠陥ではなくドキュメント文言の不正確さ（doc drift）に過ぎず、しかも指摘の中核前提が事実誤認のため棄却する。

1) 実害ゼロ（どの実行パスも壊れない）。`get_db` を app/ tests/ tools/ Rehab_RAG/ で grep した結果、ヒットは app/core/README.md:20,30 の2件のみ（他は venv/ 配下の pymysql/sqlalchemy の無関係な `_get_db`/`get_dbapi_type`）。実際の利用側は app/crud/patient.py:4, app/crud/staff.py:3, app/crud/plan.py:8 が `import app.core.database as database`、app/services/patient_service.py:4・

- admin.py が例外を一切ログに残さず、生の例外メッセージをそのままブラウザへ表示している
  - `app/routers/admin.py`
  - 引用コード自体は実在する（app/routers/admin.py は 1-8 行目に logging の import が無く、62/81/94/110 行が `flash(f"...: {e}")` のみ）。しかし本指摘の中核主張2点がいずれも成立しない。

(1) 失敗シナリオが到達不能。示された「staff_crud.get_all_staff() が DB 接続断/認証失敗で例外→62-64 行が捕捉→pymysql の Access denied 文字列がブラウザに描画され、logs/ には一行も残らない」という経路は本デプロイでは発生しない。app/__init__.py:91-99 の user_loader が全認証リクエストで `staff_crud.get_staff_by_id(int(staff_id))` を呼び、app/crud/staff.py:18-26 

- 「患者の計画書履歴」クエリが3箇所に重複実装され、うち2箇所はCRUD層を経由せずSessionLocalを直叩きしている
  - `app/services/patient_service.py`
  - 引用コード自体は実在するが（app/services/patient_service.py:127-133、app/routers/plan/views.py:71-80、app/routers/plan/api.py:219-227 を実読、いずれも一字一句そのまま存在）、指摘の実質は「実害のないDRY/層構造の好み」に還元され、かつ実害として挙げられた部分は既報告分の重複であるため棄却する。

1) 移行によって3箇所を直す必要は実際には生じない。schema.sql（作業ツリー版、73-88行）を読むと、移行後の rehabilitation_plans に残るのは plan_id / patient_id / created_by_staff_id / created_at / liked_items_json / header_* 4本 / plan_data。3箇所の重複クエリ

- 計画生成パスに safety_settings が無く、安全フィルタによるブロックが原因不明の生成失敗になる
  - `app/services/llm/gemini.py`
  - 反論する。指摘の「対照構造」自体が成立しておらず、機能的な障害メカニズムが存在しない。

(1) モデル差が存在しない。app/services/llm/gemini.py:316 の呼び出しモデルは `model="gemini-2.5-flash-lite"`。一方、アプリが実際に使うRAGパイプラインは ./rag_config.yaml の `active_pipeline: "hybrid_search_experiment"` であり、Rehab_RAG/experiments/hybrid_search_experiment/config.yaml:164-170 の query_components.llm は `class: GeminiLLM` / `model_name: "gemini-2.5-flash-lite"` / `safety_block_none: t

- HyDEがOllama専用の /no_think トークンをGeminiプロンプト末尾に混入させている(現行のactive_pipelineで発火)
  - `Rehab_RAG/rag_components/query_enhancers/hyde_generator.py`
  - 実コードを確認した結果、引用箇所自体は存在するが「障害」と呼べる事象が成立しないため棄却する。

【事実確認（引用は概ね正しい）】
- Rehab_RAG/rag_components/query_enhancers/hyde_generator.py:72-79 に `prompt += " /no_think"` は実在する。
- rag_config.yaml:4 `active_pipeline: "hybrid_search_experiment"`、app/services/rag_manager.py:17-38 が同ファイルを読む、Rehab_RAG/experiments/hybrid_search_experiment/config.yaml の query_components.llm=GeminiLLM(gemini-2.5-flash-lite)／query_en

- FIM/BIの開始時スコアがプロンプトから完全に脱落し、目標設定が改善傾向を無視する
  - `app/services/llm/context_builder.py`
  - 引用コードの存在自体は確認したが、「欠陥」ではなくプロンプト設計の改善要望であり、指摘された害も既存の人手レビュー経路で緩和されているため棄却する。

1) コードは「取りこぼし」ではなく明示的な設計。context_builder.py:384 で facts の器が `"ADL評価": {"FIM(現在値)": {}, "BI(現在値)": {}}` とハードコードされ、468-476 のループもキー名・カテゴリ名ともに「現在値」と自己整合的にラベル付けされている。ADL項目は CELL_NAME_MAPPING(9-341) に一切登録されておらず、この ADL ブロックは start を意図的に含めずに手書きされたもの。壊れたマッピングでも到達不能な分岐でもなく、start_val を渡すべきという仕様・コメント・テスト（tests/test_llm_comprehensive.p

- 患者情報パーサのタイムアウト予算が破綻し、gunicornのワーカータイムアウトを超えうる
  - `app/services/llm/patient_info_parser.py`
  - 引用コード自体は実在する（patient_info_parser.py:512-514 の get_remaining_time、551 の予算チェック、559 の with ThreadPoolExecutor、587-588 の future.result(timeout=180)）が、この指摘の中核である failure_scenario（gunicornワーカーがkillされ、--workers 1 のため同ワーカーの他リクエストも道連れで502）は、実際のデプロイ構成を読む限り成立しない。

1) gunicornのworkerクラスとtimeoutの意味が前提と違う。docker-compose.yml:29 は `--workers 1 --threads 8 --timeout 300`。同梱のgunicorn 26.0.0（venv/Lib/site-packages/g

- 存在しない職員・患者IDでも「割り当てました」「解除しました」と成功表示される
  - `app/routers/admin.py`
  - 引用コード自体は実在するが（app/routers/admin.py:74-83, 86-96、app/crud/staff.py:69-93）、主張されている障害シナリオと被害が成立しない。

(1) 前提の「別の管理者Bが患者ID=7を削除する」経路がアプリに存在しない。app/ 配下で `db.delete|DELETE FROM|.delete(` を grep した結果、ヒットは app/crud/staff.py:51 の職員削除と app/crud/plan.py:169,184 の SuggestionLike 削除のみで、患者を削除する CRUD もルートも一切ない（`delete_patient` 等も 0 件）。患者削除は DB 直接操作でしか起きず、この deployment の実経路では到達しない。

(2) 唯一実在する削除経路である delete_staff（

- 例外文字列をそのままクライアントへ返しており、SQL文とバインドされた患者データが露出する
  - `app/routers/plan/views.py`
  - コードの文字列自体（views.py:34/103/135/166/193/213, admin.py:63/82/95/111 の `str(e)` 埋め込み）は実在するが、指摘の核心である「SQL文とバインドされた患者データ（患者ID・傷病名などの要配慮個人情報）がブラウザに露出する」という主張は、実際のコードでは成立しない。

1) 主たる引用箇所 views.py:193 の本文はUIに一切表示されない。app/web/templates/confirm.html:1289-1294 が唯一の呼び出し元で、`if (!response.ok) { throw new Error(\`HTTP error! status: ${response.status}\`); }` としてレスポンス本文を読まずに捨て、:1308 で表示されるのは「通信エラーが発生しました: HTTP err

- 編集ページの例外ハンドラが全例外を「無効な患者IDです。」に潰し、障害原因を隠蔽する
  - `app/services/patient_service.py`
  - 引用行自体は実在する（app/services/patient_service.py:144-146 の `except Exception as e: logger.error(f"prepare_edit_page_data error: {e}") / result["error_message"] = "無効な患者IDです。"`、および 141-142 の患者不在メッセージ）。しかし主張されている実害の大半がコードに照らして成立しない。

(1)「運用者にも誤った原因を提示する／後追い調査も困難」は誤り。ログには str(e) がそのまま出る。SQLAlchemy の ProgrammingError/OperationalError の文字列表現には DB ドライバのエラーコード・本文に加え `[SQL: ...] [parameters: ...]` が含まれるため、想定シナリ

- schema.sqlのDROP一覧からsuggestion_likesが漏れており、再実行時に前の患者のいいね評価が別人に引き継がれる
  - `schema.sql`
  - 証拠自体（schema.sql:17-22 の DROP 一覧に suggestion_likes が無く、schema.sql:101 が CREATE TABLE IF NOT EXISTS である）はコード上に実在するが、記述された失敗シナリオはこのデプロイでは到達不能であり、かつ既報項目に包含されるため棄却する。

(1) 実デプロイ経路では schema.sql は既存DBに対して二度と走らない。docker-compose.yml:64 は `./schema.sql:/docker-entrypoint-initdb.d/1_schema.sql` としてマウントしており、mysql:8.0 の entrypoint は /var/lib/mysql（compose では ./mysql_data バインド）が空の初回初期化時にしか initdb.d を実行しない。READM

- confirm.htmlがサーバ提供の editable_keys を自前定義で上書きし、両者が既に乖離している
  - `app/web/templates/confirm.html`
  - 証拠のうち「テンプレートが editable_keys をシャドウイングしている」「cs_motor_details が plan_service.py:20 にしか存在しない」の2点は事実だが、そこから主張される具体的な障害はいずれも実際のコードパス上で発生しない。

1) 「AIが生成しても表示・編集・いいね評価ができない」— AI は cs_motor_details を生成しない。app/schemas/schemas.py の RehabPlanSchema（LLM 出力スキーマ）は main_risks_txt〜goal_s_3rd_party_action_plan_txt の24フィールドのみで、cs_motor_details は無い（RisksAndPrecautions / FunctionalLimitations / Goals / TreatmentPolicy

- nginxが/static/を30日キャッシュする一方でキャッシュバスターが無く、CSS/JS修正が最大30日間反映されない
  - `nginx/default.conf`
  - 【判定: 反証】引用された断片自体（nginx/default.conf:11-15 の `expires 30d;`、各テンプレートのバージョン無し `url_for('static', ...)`、app/ 配下に SEND_FILE_MAX_AGE / url_defaults が無いこと）は実在する。しかし failure_scenario の中核が本リポジトリの実態と食い違っており、指摘としての実害が成立しない。

(1) nginx の `location /static/` が配信する実ファイルは style.css 1本のみ。docker-compose.yml:15 で `./app/web/static:/usr/share/nginx/html/static:ro` をマウントしているが、app/web/static/ の中身は実測で `style.css`（12,9

- 結合セル解決コードが openpyxl 3.1 系で必ず例外を出し、失敗が print だけで握り潰される（結合セル対応は実質デッドコード）
  - `app/services/excel/writer.py`
  - openpyxl 側の技術的主張は実測で正しい（venv/Lib/site-packages/openpyxl/worksheet/worksheet.py:618-622 が `return self.merged_cells.ranges[:]`、cell_range.py:428-434 で `ranges` は `set` なので TypeError、worksheet/merge.py:55-70 の MergedCellRange は `start_cell` のみで `min_cell` は存在しない＝hasattr False を確認）。しかしこの分岐は本配備の実経路で到達不能である。app/services/excel/mappings.py の TEXT_MAPPING/DATE_MAPPING/SELECTION_MAPPING/GENDER_MAPPING の全44

- Flask-Loginのセッション保護が実質no-op（basic既定＋fresh_login_required未使用）で、識別子のIPもクライアントから偽装可能
  - `app/__init__.py`
  - 引用自体は正確（SESSION_PROTECTIONはvenv除外で0ヒット、flask_login 0.6.3の login_manager.py:86 の既定 "basic"、:397-409 の basic 分岐、utils.py:383-389 のXFF先頭採用、nginx/default.conf:22 の $proxy_add_x_forwarded_for を実際に読んで確認）だが、指摘として成立しない。(1) XFF偽装の半分は現コードで不活性：`remote_addr|X-Forwarded|X-Real-IP|ProxyFix` を venv 除外でリポジトリ全体(.py/.html)に grep すると0ヒットで、アプリは認証・監査・レート制限のどこでもクライアントIPを読まない。_get_remote_addr() の唯一の呼び出し元 _create_identif

- 未認証の POST /login でパスワード欄を省略すると例外が伝播し、デバッグトレースバックが認証なしで返る
  - `app/routers/auth.py`
  - 機構そのものは成立するが、本指摘の核である「デバッグトレースバックが認証なしで返る／severity high」は本デプロイでは成立しないため refute する。

【確認できた事実（機構部分）】
- app/routers/auth.py:20-26 に指摘どおり `password = request.form.get("password")` → `check_password_hash(staff_info["password"], password)` があり、None ガードは無い。
- venv/Lib/site-packages/werkzeug/security.py:36-38 の `_hash_internal()` は `password_bytes = password.encode()` を実行するため None で AttributeError になる。sc

- DB例外メッセージ（SQL全文＋バインド値）がそのままHTTPレスポンスとログに出力される
  - `app/core/database.py`
  - 指摘の中核メカニズム（SQLAlchemy が `[SQL: %s]` / `[parameters: %r]` を例外文へ連結する）自体は venv/Lib/site-packages/sqlalchemy/exc.py の `StatementError._sql_message()` を読んで確認でき、app/core/database.py:25 に hide_parameters 指定が無いことも事実。しかし本指摘は (1) 一次アンカーと推奨修正が的外れ、(2) failure_scenario の具体的主張が実コードと3点で矛盾、(3) 残る実害部分は既報告と重複、のため報告価値のある新規欠陥として成立しない。

(1) file/line/evidence が app/core/database.py:25（create_engine に hide_parameters 未

- READMEのローカル起動手順が存在しない app.py を指しており、実際に動く起動手段がdebugモードのstart_app.batだけになっている
  - `README.md`
  - 引用文自体（README.md:384 の `python app.py`、:413 の「`app.py` が環境変数を読み取り」）は実在し、リポジトリ直下のPythonは 1_generate.py / debug_parser.py / evaluate_extraction_accuracy.py / run.py のみで app.py は無いこと（ls 済み、grep でも app.py の実体ヒットは venv 内の外部ライブラリだけ）は事実です。しかし本指摘の中核である「実際に動く起動手段が debug モードの start_app.bat だけ」「安全な起動手順がどこにも文書化されていない」は、コードを読む限り誤りです。

(1) docker-compose.yml:29 に `command: gunicorn --bind :8080 --workers 1 --thr

- tools/test.sqlが平文パスワード1234を共有する管理者アカウントを40件投入する
  - `tools/test.sql`
  - 生データ自体は再現できたが（tools/test.sql の `INSERT INTO staff` ブロックは40個、staff.id=101〜140、username=test1〜test40、role は VALUES 句・ON DUPLICATE KEY UPDATE 句とも全件 'admin'、パスワードハッシュは1種類のみで、hashlib.scrypt(b'1234', salt=b'0QtDM5HWhwXYeWiP', n=32768, r=8, p=1, dklen=64, maxmem=2**30) と一致=True を自分でも確認）、high として計上する根拠が4点とも崩れる。

(1) 実行経路が存在しない。docker-compose.yml:64-65 が /docker-entrypoint-initdb.d にマウントするのは `./schema.sql`

- README記載の「初期管理者パスワード変更」手順がschema.sqlの実体と乖離し実行不能になっている
  - `README.md`
  - 実ファイルを読んだ結果、引用箇所自体は存在するが、この指摘が主張する「実行不能」「唯一の緩和策の破綻」という中身は成立しない。

1) 「READMEの4列INSERTをそのまま実行するとoccupation NOT NULL違反になる」は誤読。README.md:217-227 は「`schema.sql`ファイルを開き、末尾にある`staff`テーブルへの`INSERT`文を探します。そして、コピーしたハッシュ値を指定の場所に貼り付けてください」であり、続くSQLブロックは冒頭に `-- 変更前` と明示された“編集対象行のイメージ”に過ぎない。単体で実行せよとは書かれておらず、実際にDBへ流すのはファイル全体（README.md:235 `source schema.sql` / README.md:371 `mysql -u your_db_user -p rehab_db < s

- アプリにパスワード変更・リセット機能が一切存在せず漏洩した資格情報を無効化できない
  - `app/routers/admin.py`
  - 【事実確認】列挙されたルートは実在する（app/routers/admin.py:13,41,67,86,99 の5ルート、app/routers/auth.py:16,62 の2ルート）。app/ 配下の password grep でも書き込みは admin.py:28-30 の generate_password_hash → staff_crud.create_staff（app/crud/staff.py:29-36）のみで、crud にも update password 相当の関数は無い。app/web/templates で type="password" を持つのは login.html（うち24-34行はコメントアウトされた旧フォーム、実体は37-48行）と signup.html:29 のみ。ここまでは指摘どおり。しかし以下の理由で報告価値が無いと判断する。

【1. 

- 唯一ピン留めされた requirementsGPU.txt が PyPI に存在しない +cu121 ホイールを index 指定なしで要求し、そのままでは install 不能
  - `requirementsGPU.txt`
  - 実ファイルを読んだ結果、指摘の中核となる前提が3点とも成立しない。

【1】「README の指示どおり pip install -r requirementsGPU.txt を実行すると全体が中断する」という failure_scenario は、リポジトリ内に該当する指示が存在しない。全文 grep（.history/venv 除外）で `requirementsGPU` を含むのは `app/services/extraction/README.md:43` のただ1行のみで、その本文は「`requirementsGPU.txt` または `requirementsCPU.txt` に含まれる `gliner2` と `torch` をインストールしてください」＝**パッケージ名の参照リスト**として挙げているだけで、`pip install -r` を指示していない。実際のインスト

- PyYAML と tqdm が requirements.txt に宣言されておらず chromadb の推移的依存にのみ依存している（無ピンのため消失リスクが常時ある）
  - `app/services/rag_manager.py`
  - 実コードを読んだ上で、以下の理由により指摘を退けます（refuted=true）。

【1】「宣言が無い」という評価が事実として不正確。指摘は requirements.txt と requirementsCPU.txt しか確認していないが、リポジトリ内には両パッケージを固定版で宣言した requirements ファイルが実在する。
- C:/Users/yumah/OneDrive/Desktop/kcr_Rehab-Plan-Generator/requirementsGPU.txt:19 `chromadb==1.0.20`、:152 `PyYAML==6.0.2`、:190 `tqdm==4.67.1`（全体が pip freeze 形式の完全固定リスト）
- C:/Users/yumah/OneDrive/Desktop/kcr_Rehab-Plan-Generator/Re

- ベースイメージ・OSパッケージ・pip 自身も無ピンで、ミドルウェアタグも可変（イメージ層すべてが非再現）
  - `Dockerfile`
  - 引用箇所自体は実在する（Dockerfile:3 `FROM python:3.11-slim-bookworm as builder`、Dockerfile:12-16 のバージョン無指定 apt、Dockerfile:25 `RUN pip install --no-cache-dir --upgrade pip`、docker-compose.yml:5 `nginx:1.25-alpine`、:52 `mysql:8.0`、bm25_retriever.py:35）。しかし指摘は「一般的なサプライチェーン衛生の推奨」の域を出ず、示された故障シナリオは因果が誤帰属で、この配備では到達しない。

(1) 故障シナリオが Debian stable の性質上成立しない。タグは `-bookworm` まで固定されており trixie へ流れることはない。bookworm は凍結された s

- requirementsCPU.txt が requirements.txt のほぼ複製で、公式手順書が実在しない依存を指している
  - `app/services/extraction/README.md`
  - refuted。引用文自体は実在する（app/services/extraction/README.md:43 の記述、requirementsCPU.txt が requirements.txt + pytest/pytest-mock の23行であること、requirementsGPU.txt:47 の gliner2 / :188 の torch==2.5.1+cu121 はいずれも確認）。しかし指摘された故障メカニズムが現行コードに存在せず、実体のある部分は既報 be-12 の重複である。

(1) gliner2 / torch はもはや当モジュールの依存ではない。app/services/extraction/fast_extractor.py を全文読んだところ、クラス docstring:19 が「GLiNERなどのDeep Learningモデルを使用しないため、CPUの

- チャンクIDが絶対パス＋通し番号＋本文のsha256のため、1文字の修正で以降の全チャンクが重複挿入される
  - `Rehab_RAG/rag_components/chunkers/structured_markdown_chunker.py`
  - 引用されたコード自体は実在する（structured_markdown_chunker.py:94-95/129-130 の `unique_string = f"{file_path}:{chunk_index}:{text_content}"`、chromadb_retriever.py:79 の `self.collection.upsert(`、build_database.py:25/100/105 の絶対パス、README.md:314 と :378 の二重の構築手順、docker-compose.yml:39 の `./rag_db_data:/app/Rehab_RAG/experiments/hybrid_search_experiment/db`）。しかし、この指摘が主張する「実害」は既に別の場所で潰されており、指摘の失敗シナリオは成立しない。

1) 「重複した1文書

- チャンクmetadataに版・改訂日・取込日が無く、参照情報パネルからは引用が現行版か旧版か判別できない
  - `Rehab_RAG/rag_components/chunkers/structured_markdown_chunker.py`
  - 実コードを読んだ結果、本指摘は「未実装の将来機能に対する要望」であり、既存コードの欠陥として成立しないため反証する。

1) 引用証拠が不正確（UIはファイル名だけではない）。app/web/templates/confirm.html:1117-1124 は実際には
`const sectionPath = [ctx.section, ctx.subsection, ctx.subsubsection].filter(...).join(' > ');` を作り、
`出典[n]: ${ctx.source}` に加えて `<small>${ctx.disease}</small>` と `セクション: ${sectionPath}` を表示している。
app/services/llm/gemini.py:250-261 も source / disease / section を前段へ渡

- RAGインデックスが空/不在でも起動時に検証されず、根拠ゼロの計画書が「正常生成」として出力される
  - `Rehab_RAG/rag_components/retrievers/chromadb_retriever.py`
  - この指摘の中核である「インデックスが空でも一切例外にならず、根拠ゼロの計画書が正常生成として出力される」は、本デプロイで実際に走る経路では成立しない。

1) 実行されるパイプラインは ChromaDBRetriever ではない。rag_config.yaml の有効行は `active_pipeline: "hybrid_search_experiment"` の1行のみ（他の raptor_experiment / multi_query_experiment / self_rag_full_pipeline / structured_… は全てコメントアウト）。app/services/rag_manager.py:38 が `DEFAULT_RAG_PIPELINE = load_active_pipeline_from_config()` でこれを読み、app/routers/

- RAGインデックスと知識源がどの配布経路にも含まれず、新規環境は必ず空の知識ベースで正常起動する
  - `.dockerignore`
  - 引用文字列自体は実在する（.dockerignore:41-42/47-50、docker-compose.yml:36-39、.gitignore:17/21/28/29 を実読。`git ls-files | grep -E "source_documents|/db/|rag_db_data"` は0件、実ファイルも Rehab_RAG/experiments/hybrid_search_experiment/ には build_database.py・config.yaml・test.py のみで db/ は不在、Rehab_RAG/source_documents も存在しない）。しかし「どの配布経路にも含まれない＝欠陥」「新規デプロイの既定状態」という主張は成立しない。

(1) .dockerignore の除外は意図された正しい設計。41行目のコメント「RAGのDBデータ 

- プレビュー用iframeがsandbox属性を持たずsrcdocで生成されるため、CDNスクリプトが親画面のCSRFトークンとフォーム全体を同一オリジンで掌握する
  - `app/web/templates/confirm.html`
  - 【反証】証拠の引用自体は正確だが、指摘の因果関係と修正提案が成立しない。

1) 前提となる攻撃経路が iframe を経由しない。confirm.html は親文書自身が cdn.jsdelivr.net から3本のスクリプトを SRI なしでトップレベル実行している（confirm.html:16 `<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js">`、:20 `mermaid@10/dist/mermaid.min.js`、:357 `bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js`）。一方 iframe 内の luckysheet/luckyexcel も同じ cdn.jsdelivr.net（preview_viewer.html:83-85）。failu

- CDNスクリプトの一部がバージョン未指定で常に最新を取得し、上流の破壊的更新・悪意ある公開がレビュー無しで本番に届く
  - `app/web/templates/preview_viewer.html`
  - 引用されたURL自体は実在する（preview_viewer.html:85 luckyexcel、confirm.html:16 marked、confirm.html:20 mermaid@10、edit_patient_info.html:2621 chart.js。grepでCDN参照は全9箇所、うち5箇所は luckysheet@2.1.13 / bootstrap@5.3.0 / bootstrap-icons@1.11.3 で厳密固定済み）。しかし本Findingの中核主張と重大度は、コードとgit履歴を読むと成立しない。

(1)「どのバージョンで動作確認したのか記録・再現・ロールバックする手段が無い」は事実誤認。直近のフロントエンドコミット bb2ae77「JSライブラリの除外」（git show --stat）を見ると、それ以前は当該ライブラリ一式が app/web/s

- ローカル版JSライブラリがコミットbb2ae77で削除・.gitignore除外され、外向きHTTPSが無い環境では計画書プレビューが復旧不能に壊れる
  - `.gitignore`
  - 指摘の中核である「bb2ae77で壊れた」「復旧不能」の2点がいずれもコードと履歴で否定される。

(1) 因果関係が誤り — bb2ae77は挙動を一切変えていない。
`git show bb2ae77^:app/web/templates/preview_viewer.html` を読むと、削除コミットの**直前時点で既に** 83-85行はCDN（cdn.jsdelivr.net/npm/luckysheet@2.1.13 …）が有効で、86-88行のローカル `lib/luckysheet/*` は既にコメントアウト済みだった。confirm.html も同様に、bb2ae77^ の時点で9/14/16/20行がCDN、10/13/18/21行がコメントアウト済み。つまりbb2ae77が消したのは「既にどのテンプレートからも参照されていない死んだファイル」であり、ランタイム挙動の差

- アプリ全体でセキュリティレスポンスヘッダ（CSP/X-Frame-Options等）が1つも設定されていない
  - `nginx/default.conf`
  - 証拠の事実関係自体は正しい（nginx/default.conf 全29行に add_header は無く、app/ 配下を after_request|Talisman|headers[ でgrepしてもヒット0、app/__init__.py:29-69 の create_app は CSRFProtect と LoginManager のみ初期化）。しかし報告に値しないと判断した。(1) nginx/README.md の「3. 実践的な設定パターン」§A「HTTPS化 (SSL/TLS) [必須]」(130-148行) と §B「セキュリティヘッダーの追加」(150-162行) に add_header X-Frame-Options "SAMEORIGIN" / X-XSS-Protection / X-Content-Type-Options nosniff が本番デプロイ手順

- docker-compose.ymlが2系統に分岐し、堅牢な方(tools/)が放置され欠陥のある方が本番用になっている
  - `docker-compose.yml`
  - この指摘は前提が事実と異なり、かつ残る内容が既報の重複です。

1) 「tools/ 側が堅牢な代替本番構成として並走している」が成立しない。tools/ の中身は `ls tools/` の通り Create-Hash.ps1 / check_schema_coverage.py / create_hash.py / docker-compose.yml / liked_details_viewer.py / test.sql の6点のみで、Dockerfile も .env も schema.sql も nginx/ も app/ も存在しない。tools/docker-compose.yml L23 は `build: .`、L34-35 は `env_file: - .env`、L13 `./nginx/default.conf`、L15 `./app/web/static`、L7

- tools/docker-compose.ymlは自分の置き場所から起動できず、参照される「良い方の設定」が誰にも検証されていない
  - `tools/docker-compose.yml`
  - 引用された行は実在する（tools/docker-compose.yml の L13 `./nginx/default.conf`、L15 `./app/web/static`、L23 `build: .`、L34-35 `env_file: - .env`、L75 `./schema.sql`、および `ls -a tools/` の結果は Create-Hash.ps1 / check_schema_coverage.py / create_hash.py / docker-compose.yml / liked_details_viewer.py / test.sql のみ）。しかし指摘の中身は「実際の障害」ではなく死蔵ファイルの所在に関する整理事項であり、以下の理由で退けます。

1) 前提となる「参照される『良い方の設定』」が事実ではない。リポジトリ全体を grep しても to

- tools/docker-compose.ymlのhealthcheckは資格情報が展開されず、DB初期化完了の待機保証になっていない
  - `tools/docker-compose.yml`
  - 引用行自体は実在する（C:/Users/yumah/OneDrive/Desktop/kcr_Rehab-Plan-Generator/tools/docker-compose.yml L78-83 に `test: ["CMD","mysqladmin","ping","-h","localhost","-u$$DB_USER","-p$$DB_PASSWORD"]`）。$$→リテラル$、exec形式のため非展開、mysqladmin ping が Access denied でも exit 0、`-h localhost`＝UNIXソケット、という機構論も概ね正しい。しかし本デプロイでは到達不能であり、かつ既報の重複であるため棄却する。

(1) tools/docker-compose.yml は「実行できない退避コピー」である。`ls tools/` の中身は Create-Has

- 名前付きボリュームからバインドマウントへの退行で README の `docker-compose down -v` が無効化されている
  - `docker-compose.yml`
  - 指摘の中核前提「名前付きボリューム→バインドマウントへの退行」がコードに存在せず、残る実質は既報findingの重複であるため棄却する。

1) 「退行」は事実誤認。`git diff docker-compose.yml`（作業ツリー）は @@ -44,6 +44,30 @@ の純追加のみで、`db:` サービス丸ごと（image/environment/volumes/ports）が新規追加されている。つまりHEADの docker-compose.yml には db サービスも `- ./mysql_data:/var/lib/mysql` も存在しない。名前付きボリューム `mysql_data:` を消したのは今回の作業ツリー変更ではなく、コミット済みの a08f7c5「AmazonRDSなどデータベースを分けるためにdocker-composeを編集」(2026-01-19) 

- リハビリ専門用語のMeCabユーザー辞書(472語)が本番RAGのBM25経路から一切ロードされず死蔵している
  - `Rehab_RAG/rag_components/retrievers/bm25_retriever.py`
  - 【事実確認：一部は正しい】user.dic / user_dic.csv は実在し git 追跡下にある（git ls-files で確認、user_dic.csv は 471 行、user.dic のバイナリヘッダを読むと lexsize=0x1d8=472、charset="utf-8"、lsize/rsize=1316=ipadic 2.7.0 互換）。app/services/fact_db.py:56 の init_mecab_with_user_dic() が唯一の参照で、grep -rn "fact_db" の結果は fact_db.py 自身と app/services/README.md:45 と docker-compose.yml:65(schema_facts.sql) のみ、import 元は皆無。bm25_retriever.py:32-39 に -u が無いこ

- user_dic.csv が .dockerignore の *.csv で除外され、辞書のコンパイル工程もDockerイメージに存在しない
  - `.dockerignore`
  - 証拠の「事実」部分（.dockerignore:28 の `*.csv` がルート直下の user_dic.csv を除外する／Dockerfile:11-18 に mecab-dict-index が無い）は確かにコードどおりだが、この欠落が実デプロイ上のどの経路でも障害にならないため refute する。

1) 実行時に user.dic を読むコードが存在しない（＝到達不能）。リポジトリ全体を grep した結果、`user.dic` を参照するのは app/services/fact_db.py:10 の `USER_DIC_FILE = "user.dic"` と同 66 行 `mecab_args.append(f"-u {USER_DIC_FILE}")` の 1 箇所のみ。その fact_db.py は `from app.services import ...` の g

- init_mecab_with_user_dic() が辞書ロード失敗を握り潰したまま「正常に初期化されました」と出力し、辞書パスもCWD依存
  - `app/services/fact_db.py`
  - 実コードを読んだ結果、この指摘は「到達不能なデモスクリプト内のprint文言」に過ぎず、かつ死蔵部分は既報と重複するため棄却する。

1) 引用コード自体は実在する（app/services/fact_db.py:60-80 の mecab_args 組み立て・except RuntimeError での `MeCab.Tagger("-Owakati")` フォールバック・:79 の無条件 print、および :209-218 の固有名詞分岐）。しかし呼び出し元が存在しない。`init_mecab_with_user_dic()` の唯一の呼び出しは同ファイル :281（`main()` 内）であり、`main()` は :320-321 の `if __name__ == "__main__":` からしか呼ばれない。リポジトリ全体を venv/.git 除外で grep しても `f

- 472語の専門用語辞書に対しエイリアス表が5事実9キーしかなく、fact_db を復活させても辞書語の98%が空振りする
  - `app/services/fact_db.py`
  - 【却下】数値自体（user_dic.csv は 472行、fact_db.py:159-174 のエイリアスは9件、core_facts は5件）は実在するが、指摘の性質が「デモスクリプトのサンプルデータがサンプルデータであること」への意見であり、実デプロイ上の欠陥ではない。

(1) 到達不能かつ本指摘自身が仮定条件付き。`grep -rn "fact_db"` をリポジトリ全体（venv/.history除く）に掛けた結果、ヒットは `app/services/README.md:45` のファイル名言及のみで、`import` は0件。routers/plan_service/llm/rag_manager のどこからも呼ばれず、docker-compose の `gunicorn ... run:app` からも到達しない。fact_db.py の唯一の入口は `if __name

