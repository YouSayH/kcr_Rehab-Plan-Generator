# Rehab_RAG/rag_components/rerankers/gemini_embedding_reranker.py
import numpy as np
from ..embedders.gemini_embedder import GeminiEmbedder # Embedderをインポート

class GeminiEmbeddingReranker:
    """
    [手法解説: Reranking with Gemini Embeddings]
    Gemini Embeddingモデルを用いて取得したベクトル間の類似度に基づいて、
    文書をリランキングするコンポーネント。

    仕組み:
    1. 質問と各候補文書をGemini Embeddingモデルでベクトル化する。
    2. 質問ベクトルと各文書ベクトルの類似度（内積）を計算する。
    3. 類似度スコアが高い順に文書を並べ替える。

    期待される効果:
    - CrossEncoderより高速に動作する可能性がある（特に候補文書が多い場合）。
    - Embeddingモデルの性能に依存するが、意味的に近い文書を上位表示できる。
    """
    def __init__(self, embedder: GeminiEmbedder):
        """
        コンストラクタ。Gemini Embedderのインスタンスを受け取ります。

        Args:
            embedder (GeminiEmbedder): 初期化済みのGeminiEmbedderインスタンス。
        """
        if not isinstance(embedder, GeminiEmbedder):
            raise TypeError("embedder must be an instance of GeminiEmbedder")
        self.embedder = embedder
        print(f"Gemini Embedding Rerankerが初期化されました (Embedder: {self.embedder.model_name})。")

    def _calculate_similarity(self, query_embedding: list[float], doc_embeddings: list[list[float]]) -> np.ndarray:
        """ベクトル間の類似度（内積）を計算"""
        query_vec = np.array(query_embedding)
        doc_vecs = np.array(doc_embeddings)
        # Gemini Embeddingは正規化されていることが多いので、内積計算で類似度を測る
        scores = np.dot(doc_vecs, query_vec.T)
        return scores

    def rerank(self, query: str, documents: list[str], metadatas: list[dict]) -> tuple[list[str], list[dict]]:
        """
        Gemini Embeddingモデルを使用して、文書をクエリとの類似度スコアで並べ替える。

        Args:
            query (str): ユーザーの元の質問文。
            documents (list[str]): 検索された文書チャンクのリスト。
            metadatas (list[dict]): 各文書チャンクに対応するメタデータのリスト。

        Returns:
            tuple[list[str], list[dict]]: スコアに基づいて並べ替えられた文書とメタデータのタプル。
        """
        if not documents:
            return [], []

        try:
            # 質問をベクトル化
            print("  - Reranker: 質問をベクトル化中...")
            query_embedding = self.embedder.embed_query(query)

            # 候補文書を一括でベクトル化
            print(f"  - Reranker: {len(documents)}件の候補文書をベクトル化中...")
            doc_embeddings = self.embedder.embed_documents(documents) # バッチ処理とリトライはembed_documents内で行われる

            # 類似度を計算
            print("  - Reranker: 類似度を計算中...")
            scores = self._calculate_similarity(query_embedding, doc_embeddings)

            # スコアに基づいてソート (スコアが高い順)
            sorted_indices = np.argsort(scores)[::-1]

            reranked_docs = [documents[i] for i in sorted_indices]
            reranked_metadatas = [metadatas[i] for i in sorted_indices]

            return reranked_docs, reranked_metadatas

        except Exception as e:
            print(f"  - Reranker: Gemini Embeddingによるリランキング中にエラーが発生: {e}")
            # エラー発生時は元の順序で返すなどのフォールバック処理も検討可能
            return documents, metadatas