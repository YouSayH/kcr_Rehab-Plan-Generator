from unittest.mock import MagicMock, patch

from app.services.rag_manager import get_rag_executor, rag_executors


def test_get_rag_executor_caching():
    """同じパイプライン名ならキャッシュされたインスタンスを返すこと"""
    # app.services.rag_manager内でインポートされているRAGExecutorクラスをモック化
    with patch("app.services.rag_manager.RAGExecutor") as MockExecutor:
        # モックの戻り値を設定
        mock_instance = MagicMock()
        MockExecutor.return_value = mock_instance

        # 1. 最初の呼び出し
        executor1 = get_rag_executor("test_pipeline_A")

        # インスタンスが正しく返され、コンストラクタが1回呼ばれたか確認
        assert executor1 == mock_instance
        assert MockExecutor.call_count == 1
        assert "test_pipeline_A" in rag_executors

        # 2. 同じ名前で2回目の呼び出し
        executor2 = get_rag_executor("test_pipeline_A")

        # 同じインスタンスが返され、コンストラクタは再度呼ばれていないこと（キャッシュ利用）を確認
        assert executor2 == executor1
        assert MockExecutor.call_count == 1

def test_get_rag_executor_switching():
    """異なるパイプライン名が指定されたらキャッシュをクリアして新規作成すること"""
    # 状態を持つテストなので、テスト前にキャッシュをクリアしておく
    rag_executors.clear()

    with patch("app.services.rag_manager.RAGExecutor") as MockExecutor:
        mock_instance1 = MagicMock()
        mock_instance2 = MagicMock()
        # 1回目と2回目で違うインスタンスを返すように設定
        MockExecutor.side_effect = [mock_instance1, mock_instance2]

        # 1. パイプラインAを作成
        get_rag_executor("pipeline_A")
        assert len(rag_executors) == 1
        assert "pipeline_A" in rag_executors

        # 2. パイプラインBに切り替え
        get_rag_executor("pipeline_B")
        # パイプラインAが消え、Bだけが残っていること（メモリ節約ロジックの確認）
        assert "pipeline_A" not in rag_executors
        assert "pipeline_B" in rag_executors
        assert len(rag_executors) == 1
