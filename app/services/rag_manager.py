import logging
import threading

from app.services.llm.rag_executor import RAGExecutor

# ロガー設定
logger = logging.getLogger(__name__)

# pipeline_nameをキー、RAGExecutorインスタンスを値とする辞書（キャッシュ）
rag_executors = {}
# 複数ユーザーからの同時アクセスで問題が起きないようにするためのロック機構

rag_executor_lock = threading.Lock()



def get_rag_executor(pipeline_name: str) -> RAGExecutor:
    """
    RAGExecutorのインスタンスをキャッシュから取得または新規作成する関数。
    """
    # ロックを開始（このブロック内は1つのスレッドしか入れない）
    with rag_executor_lock:
        # 1. キャッシュに存在すれば、それを返す（高速）
        if pipeline_name in rag_executors:
            print(f"'{pipeline_name}' のExecutorをキャッシュから再利用します。")
            return rag_executors[pipeline_name]

        # 2. キャッシュにない場合、既存のキャッシュを全てクリアする (メモリ解放)
        # これにより、メモリ上には常に「今から作る1つ」しか存在しなくなる
        if rag_executors:
            print("メモリ節約のため、古いRAG Executorのキャッシュを破棄します。")
            rag_executors.clear()

            # 必要であればGCを実行
            # import gc
            # gc.collect()

        # 3. 新規作成処理
        print(f"'{pipeline_name}' のExecutorを新規に初期化します...")
        try:
            executor = RAGExecutor(pipeline_name=pipeline_name)
            rag_executors[pipeline_name] = executor  # キャッシュに保存
            print(f"'{pipeline_name}' の初期化が完了し、キャッシュに保存しました。")
            return executor
        except Exception as e:
            print(f"FATAL: RAG Executor ('{pipeline_name}') の初期化に失敗しました: {e}")
            # エラー時は変なキャッシュが残らないように念のため消しておく
            if pipeline_name in rag_executors:
                del rag_executors[pipeline_name]
            raise e
