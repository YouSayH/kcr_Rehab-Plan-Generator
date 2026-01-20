import json
import textwrap
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel

FIM_GUIDELINES = """
    【FIM（機能的自立度評価法）の点数目安】
    ・7点：完全自立（安全にかつ合理的な時間内で遂行）
    ・6点：修正自立（補助具の使用や時間を要するが自立）
    ・5点：監視または準備（監視下での実施）
    ・4点：最小介助（患者が75%以上を自分で行う）
    ・3点：中等度介助（50%以上～75%未満を自分で行う）
    ・2点：最大介助（25%以上～50%未満を自分で行う）
    ・1点：全介助（25%未満しか行えない）
"""

def build_group_prompt(
    group_schema: Type[BaseModel],
    patient_facts_str: str,
    generated_plan_so_far: Dict[str, Any],
    is_ollama: bool = False
) -> str:
    """
    グループ生成用のプロンプトを構築する

    Args:
        group_schema: 生成対象のPydanticスキーマクラス
        patient_facts_str: 整形済みの患者事実情報（JSON文字列）
        generated_plan_so_far: これまでに生成された計画書の辞書
        is_ollama: Ollama向けにプロンプトを調整するかどうかのフラグ
    """

    instruction_suffix = ""
    if is_ollama:
        # Ollamaの場合、最後に生成を促すサフィックスを追加することが有効
        instruction_suffix = f"\n        --- \n        生成するJSON ({group_schema.__name__} の項目のみ):"

    return textwrap.dedent(f"""
        # 役割
        あなたは、患者様とそのご家族にリハビリテーション計画を説明する、経験豊富で説明上手なリハビリテーション科の専門医です。
        専門用語を避け、誰にでも理解できる平易な言葉で、誠実かつ丁寧に説明する文章を使用して、患者の個別性を最大限に尊重し、一貫性のあるリハビリテーション総合実施計画書を作成してください。

        # 患者データ (事実情報)
        これは、患者の客観的な評価結果や基本情報です。
        ```json
        {patient_facts_str}
        ```

        # これまでの生成結果
        これは、あなたがこれまでに生成した計画書の一部です。
        この内容を十分に参照し、矛盾のない、より質の高い記述を生成してください。
        ```json
        {json.dumps(generated_plan_so_far, indent=2, ensure_ascii=False, default=str)}
        ```

        # 重要な参照基準
        {FIM_GUIDELINES}

        # 作成指示
        上記の「患者データ」と「これまでの生成結果」を統合的に解釈し、以下のJSONスキーマに厳密に従って、各項目を日本語で生成してください。
        - **最重要**: 生成する文章は、患者様やそのご家族が直接読んでも理解できるよう、**専門用語を避け、できるだけ平易な言葉で記述してください**。
        - **例外**: 正式な診断名（病名・疾患名）のみは正確性を期すためそのまま使用して構いませんが、その症状や状態の説明には平易な言葉を使用してください。        
        - **FIM整合性**: 患者データにFIMの点数が含まれている場合、上記の【FIMの点数目安】を参照してください。ただし、**「修正自立」や「最小介助」といった点数の区分名（専門用語）は絶対に使用せず**、その点数が意味する具体的な状態（例：「時間はかかりますが一人でできます」「半分くらいはご自身でできますが、手助けが必要です」など）を、日常会話で使う言葉で記述してください。
        - **言葉選びのルール**: 「医療従事者ではないご家族」が直感的に理解できる言葉を選んでください。漢字の熟語よりも、ひらがなや動詞を使った表現を優先してください（例：「歩行」→「歩くこと」、「摂取」→「食べること」）。
        - **具体的な動作への変換**: 禁忌事項や注意点を記述する際は、「過度な屈曲禁止」のような抽象的な表現ではなく、「正座や横座りはしない」「深いソファーに座らない」「あぐらをかかない」「重い荷物を持たない」など、**日常生活で避けるべき具体的な動作**を明記してください。
        - 専門用語の言い換え例:
          - 「ADL」→「日常生活の動作」
          - 「ROM訓練/可動域訓練」→「関節を動かす練習」
          - 「嚥下」→「飲み込み」
          - 「拘縮」→「関節が硬くなって動かしにくくなること」
          - 「麻痺」→「手足が動きにくくなること」
          - 「立位」→「立つ姿勢」
          - 「端坐位」→「ベッドの端に座ること」
          - 「清拭」→「お体を拭くこと」
        - 患者データから判断して該当しない、または情報が不足している場合は、必ず「特記なし」とだけ記述してください。
        - スキーマの`description`をよく読み、具体的で分かりやすい内容を記述してください。
        - 各項目は、他の項目との関連性や一貫性を保つように記述してください。

        ```json
        {json.dumps(group_schema.model_json_schema(), indent=2, ensure_ascii=False)}
        ```
        {instruction_suffix}
    """)


def build_regeneration_prompt(
    patient_facts_str: str,
    generated_plan_so_far: Dict[str, Any],
    item_key_to_regenerate: str,
    current_text: str,
    instruction: str,
    rag_context: Optional[str] = None,
    schema: Optional[Type[BaseModel]] = None
) -> str:
    """
    項目再生成用のプロンプトを構築する

    Args:
        patient_facts_str: 整形済みの患者事実情報（JSON文字列）
        generated_plan_so_far: これまでに生成された計画書の辞書（修正対象を除く）
        item_key_to_regenerate: 再生成する項目のキー
        current_text: 現在の（修正前の）テキスト
        instruction: ユーザーからの修正指示
        rag_context: RAGによって検索された専門知識（任意）
        schema: 再生成用のPydanticスキーマ（任意・OllamaのJSONモード強制用）
    """

    schema_block = ""
    if schema:
        try:
            schema_json = json.dumps(schema.model_json_schema(), indent=2, ensure_ascii=False)
            schema_block = f"\n        JSONスキーマ:\n        ```json\n        {schema_json}\n        ```\n        ---\n        生成するJSON:"
        except Exception:
            pass

    rag_section = ""
    if rag_context:
        rag_section = f"""
        # 参考情報 (専門知識)
        これは、あなたの知識を補うための専門的な参考情報です。この情報を最優先で活用し、より根拠のある文章に修正してください。
        ```text
        {rag_context}
        ```
        """

    return textwrap.dedent(f"""
        # 役割
        あなたは、経験豊富なリハビリテーション科の専門医です。
        これから提示する「現在の文章」を、与えられた「修正指示」に従って、より質の高い内容に書き換えてください。
        ただし、文章全体の構成や他の項目との一貫性も考慮し、不自然にならないように修正してください。
        専門用語を避け、誰にでも理解できる平易な言葉遣いを心がけてください。

        # 患者データ (事実情報)
        これは、文章を修正する上で参考となる患者の客観的な評価結果や基本情報です。
        ```json
        {patient_facts_str}
        ```

        # これまでの生成結果
        これは、あなたがこれまでに生成した計画書の一部です。修正する項目以外の内容です。
        この内容を十分に参照し、矛盾のない、より質の高い記述を生成してください。
        ```json
        {json.dumps(generated_plan_so_far, indent=2, ensure_ascii=False, default=str)}
        ```
        {rag_section}

        # 修正対象の項目
        `{item_key_to_regenerate}`

        # 現在の文章
        ```text
        {current_text}
        ```

        # 修正指示
        `{instruction}`

        # 作成指示
        上記のすべての情報を踏まえ、「現在の文章」を「修正指示」に従って書き直してください。
        - **重要**: 最終的な出力は、印刷して使用されることを想定したプレーンテキスト形式にしてください。
        - 箇条書きが必要な場合は、Markdownの `*` や `-` ではなく、全角の「・」や「■」を使用し、**各項目の後で必ず改行を入れてください**。
        - 例: 「・項目1\n・項目2\n・項目3」のように、`\n` を使って改行してください。
        - 完成した文章のみを出力し、他の前置きや解説は一切不要です。
        {schema_block}
    """)
