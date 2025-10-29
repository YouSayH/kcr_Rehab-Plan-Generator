"""
SelfReflectiveFilter: 検索結果の関連性を自己評価・フィルタリングするコンポーネント
"""
import time
import math
from typing import List, Dict
from pydantic import BaseModel, Field
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)

class DocumentRelevance(BaseModel):
    document_index: int = Field(description="評価対象ドキュメントのバッチ内でのインデックス (0から始まる)")
    is_relevant: bool = Field(description="質問に対して関連性があるか (True: 関連あり, False: 関連なし)")

class RelevanceEvaluationBatch(BaseModel):
    evaluations: List[DocumentRelevance] = Field(description="各ドキュメントの関連性評価のリスト")

class SelfReflectiveFilter:
    """
    [Filter解説: SelfReflectiveFilter (自己反省フィルタ)]
    これは、Self-RAGのもう一つの重要な要素で、データベースから検索してきた情報が
    「本当にユーザーの質問に答える上で役に立つか？」をLLM自身が一つ一つ吟味し、
    不要な情報をふるい落とすフィルタです。

    [フィルタリングの仕組み]
    1. Retrieverが検索してきた文書のリストを受け取ります。
    2. 各文書について、LLMに「この文書は、元の質問に答えるための適切な根拠になりますか？」と尋ねます。
    3. LLMは、文書と質問の関係を分析し、以下のいずれかの「評価トークン」を返します。
       - [RELEVANT]: 関連性が高く、回答の根拠として適切。
       - [IRRELEVANT]: 関連性が低い、またはノイズ。
    4. [RELEVANT]と評価された文書だけを残し、[IRRELEVANT]と評価された文書は捨てます。

    [期待される効果]
    - ベクトル検索だけでは排除しきれない、文脈的に微妙にずれた情報を正確に除去します。
    - 最終的な回答を生成するLLMに、本当に質の高い情報だけを提供することで、
      回答の精度と信頼性を大幅に向上させます。
    - ハルシネーション（AIがもっともらしい嘘をつく現象）のリスクを低減します。
    """
    def __init__(self, llm, batch_size: int = 10):
        self.llm = llm
        self.batch_size = batch_size
        print(f"Self-Reflective Filterが初期化されました。(バッチサイズ: {self.batch_size})")
        logger.info(f"Self-Reflective Filterが初期化されました。(バッチサイズ: {self.batch_size})")

    def filter(self, query: str, documents: list[str], metadatas: list[dict]) -> tuple[list[str], list[dict]]:
        """
        LLMを使って、クエリと関連性の低いドキュメントを除外します。
        """
        filtered_docs = []
        filtered_metadatas = []
        
        num_batches = math.ceil(len(documents) / self.batch_size)
        print(f"  - {len(documents)}件の文書を{num_batches}バッチに分割して自己評価フィルタリング中...")
        logger.info(f"  - {len(documents)}件の文書を{num_batches}バッチに分割して自己評価フィルタリング中...")

        for i in tqdm(range(num_batches), desc="Self-Reflecting Batches"):
            start_index = i * self.batch_size
            end_index = start_index + self.batch_size
            batch_docs = documents[start_index:end_index]
            batch_metadatas = metadatas[start_index:end_index]

            if not batch_docs:
                continue

            prompt = f"""あなたは、与えられた複数の文書がユーザーの質問に答える上で関連性があるか評価する専門家です。
以下の「質問」と「文書リスト」を比較し、各文書が質問に対する直接的な答えや有用な根拠を含むか評価してください。

# 質問
"{query}"

# 文書リスト (各文書には [index] が付与されています)
"""
            
            for idx, doc in enumerate(batch_docs):
                prompt += f"--- Document [ {idx} ] ---\n{doc}\n"

            prompt += f"""
# あなたの評価
各文書について、質問との関連性を評価し、以下のJSON形式で結果を返してください。
`is_relevant` は、関連性がある場合は true、ない場合は false としてください。
```json
{{
  "evaluations": [
    {{ "document_index": 0, "is_relevant": <true_or_false> }},
    {{ "document_index": 1, "is_relevant": <true_or_false> }},
    ... (文書リストの全インデックスについて評価)
  ]
}}
```"""



            
            time.sleep(1) # APIレート制限対策            
            response = self.llm.generate(
                prompt,
                temperature=0.0,
                response_schema=RelevanceEvaluationBatch # 定義したスキーマを指定
            )

            if isinstance(response, RelevanceEvaluationBatch) and response.evaluations:
                valid_indices = {eval_item.document_index for eval_item in response.evaluations if eval_item.is_relevant}
                
                for idx, (doc, meta) in enumerate(zip(batch_docs, batch_metadatas)):
                    if idx in valid_indices:
                        filtered_docs.append(doc)
                        filtered_metadatas.append(meta)
                logger.debug(f"バッチ {i+1}/{num_batches}: {len(valid_indices)}件が関連ありと判断されました。")

            elif isinstance(response, dict) and "error" in response:
                 logger.error(f"バッチ {i+1}/{num_batches} の評価中にLLMエラーが発生しました: {response['error']}")
            else:
                logger.warning(f"バッチ {i+1}/{num_batches} の評価で予期しない応答形式を受け取りました。応答: {response}")
                # エラー時は安全のため、このバッチのドキュメントは含めないか、あるいは全て含めるか選択
                # ここでは含めない選択とする
                # filtered_docs.extend(batch_docs)
                # filtered_metadatas.extend(batch_metadatas)


        logger.info(f"  - フィルタリングの結果、{len(filtered_docs)}件の文書が残りました。")
        return filtered_docs, filtered_metadatas
