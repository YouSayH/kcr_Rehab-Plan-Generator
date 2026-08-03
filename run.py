import os
import sys

# appディレクトリをモジュール検索パスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

if __name__ == "__main__":
    # 開発サーバの設定は環境変数で切り替える。
    # 以前は debug=True と host="0.0.0.0" を固定していたため、Werkzeugの
    # 対話デバッガ（コンソールから任意コードを実行できる）と、環境変数や
    # ソースを晒すトレースバック画面が、患者DBに接続した状態でLANに
    # 公開されていた。既定は安全側（ループバック・デバッガ無効）にする。
    debug = os.getenv("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    host = os.getenv("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_RUN_PORT", "5000"))

    if debug:
        print("[警告] デバッグモードで起動します。開発端末以外では使用しないでください。")

    app.run(
        host=host,
        port=port,
        debug=debug,
        use_reloader=False,
        # デバッグモードでも対話コンソールは開かない。
        # PINは uuid.getnode() から決定的に生成され再起動しても変わらないため、
        # 一度画面共有などで漏れると永続的に有効になる。
        use_evalex=False,
    )
