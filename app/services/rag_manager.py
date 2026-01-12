import logging
import os
import threading

import yaml

from app.services.llm.patient_info_parser import PatientInfoParser
from app.services.llm.rag_executor import RAGExecutor

# ロガー設定
logger = logging.getLogger(__name__)


LLM_CLIENT_TYPE = os.getenv("LLM_CLIENT_TYPE", "gemini")
USE_HYBRID_MODE = os.getenv("USE_HYBRID_MODE", "false").lower() == "true"

def load_active_pipeline_from_config():
    """設定ファイルから使用するRAGパイプライン名を読み込む"""
    config_path = "rag_config.yaml"
    # デフォルトのフォールバック値
    fallback_pipeline = "hybrid_search_experiment"

    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                pipeline = config.get("active_pipeline")
                if pipeline:
                    print(f"--- このRAGを使用します。: {pipeline} ---")
                    return pipeline
        except Exception as e:
            print(f"Warning: RAG選択ファイルが読み込めませんでした。 {config_path}: {e}")

    print(f"--- デフォルトのRAGを使用します。: {fallback_pipeline} ---")
    return fallback_pipeline

# アプリケーション全体で共有する定数
DEFAULT_RAG_PIPELINE = load_active_pipeline_from_config()

# 患者情報解析パーサーの初期化 (シングルトンとして管理)
patient_info_parser = None
print("Initializing Patient Info Parser in rag_manager...")
try:
    patient_info_parser = PatientInfoParser(
        use_hybrid_mode=USE_HYBRID_MODE
    )
    mode_name = "Hybrid Mode (GLiNER2 + LLM)" if USE_HYBRID_MODE else "Standard Mode (Multi-step LLM)"
    print(f"Patient Info Parser initialized successfully. [{mode_name}]")
except Exception as e:
    print(f"FATAL: Failed to initialize Patient Info Parser: {e}")


# --- RAG Executor Management ---

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
