import logging

logger = logging.getLogger(__name__)

class NegationDetector:
    """
    係り受け解析 (GiNZA) とルールベース (近傍探索) を組み合わせて
    エンティティの否定判定を行うクラス。
    """
    def __init__(self, nlp):
        self.nlp = nlp
        # 否定語リスト
        self.negation_words = {
            "ない", "ず", "ぬ", "ん", "なし", "無く", "なく", "非", "不", 
            "陰性", "(-)", "（-）", "－", "ー", "消失", "認めず", "否定", "クリア", "せず"
        }

    def is_negated(self, text: str, entity_info: dict, doc=None) -> bool:
        """
        抽出されたエンティティが文脈的に否定されているか判定する。
        """
        is_negated = False
        start_char = entity_info['start']
        end_char = entity_info['end']
        
        # 1. GiNZAによる係り受け解析 (高精度)
        if doc:
            # エンティティ範囲内の代表トークン（通常は最後の名詞）を特定
            target_token = None
            for token in doc:
                if token.idx >= start_char and token.idx < end_char:
                    target_token = token
            
            if target_token:
                # A. 親(head)が否定語 (例: "麻痺" -> "なし")
                if target_token.head.lemma_ in self.negation_words:
                    is_negated = True
                
                # B. 親の子供に否定語がある (例: "麻痺" -> "認め" -> "ず")
                if not is_negated:
                    for child in target_token.head.children:
                        if child.lemma_ in self.negation_words:
                            is_negated = True
                            break

        # 2. ルールベース (NegEx Light) - GiNZA失敗時や補完用
        # エンティティの直後 10文字を確認
        if not is_negated:
            window_size = 10
            snippet_after = text[end_char : min(len(text), end_char + window_size)]
            
            # 簡易チェック: 否定語が含まれているか
            for neg in self.negation_words:
                if neg in snippet_after:
                    is_negated = True
                    break

        return is_negated

    def check_snippet_negation(self, text: str, keyword: str) -> bool:
        """
        正規表現で見つけたキーワード周辺の単純な否定チェック用
        """
        pos = text.find(keyword)
        if pos == -1:
            return False
        
        # 後方10文字を取得
        snippet = text[pos + len(keyword) : pos + len(keyword) + 10]
        return any(neg in snippet for neg in self.negation_words)