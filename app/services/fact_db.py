import os
import platform
import sqlite3
from typing import List, Set

import MeCab

# --- 定数定義 ---
DB_FILE = "facts_sql.db"
USER_DIC_FILE = "user.dic"  # 前回コンパイルした辞書
MECAB_DIC_PATH_LINUX = "/var/lib/mecab/dic/ipadic-utf8"

# [v5.1 改善点] ストップワードリストを強化
STOP_WORDS = {
    "する",
    "いる",
    "なる",
    "ある",
    "ない",
    "いう",
    "行う",
    "おる",
    "術後",
    "患者",
    "治療",
    "場合",
    "ため",
    "こと",
    "もの",
    "的",
    "性",
    "的",
    "的",
    "よう",
    "られる",
    "これ",
    "それ",
    "あれ",
    "おける",
    "関する",
    "対する",
    "よる",
    "伴う",
    "含む",
    "教える",
    "さん",
    "について",
    "アルゴリズム",
    "何",
    "です",
    "ます",  # ノイズをさらに除去
}


# --- 1. MeCab初期化 (変更なし) ---
def init_mecab_with_user_dic() -> MeCab.Tagger:
    """
    OSに応じて適切な辞書パスを指定し、さらにユーザー辞書を読み込んでMeCab.Taggerを初期化します。
    """
    mecab_args = ["-Owakati"]
    if not os.path.exists(USER_DIC_FILE):
        print(f"[警告] ユーザー辞書 '{USER_DIC_FILE}' が見つかりません。")
        print("[警告] MeCabのコンパイルが実行されていない可能性があります。")
        print("[警告] 専門用語（THA, BM25など）が正しく解析されない可能性があります。")
    else:
        mecab_args.append(f"-u {USER_DIC_FILE}")
        print(f"INFO: ユーザー辞書 '{USER_DIC_FILE}' を読み込みます。")
    try:
        if platform.system() == "Linux" and os.path.exists(MECAB_DIC_PATH_LINUX):
            print(f"INFO: Linux環境を検出。システム辞書パス: {MECAB_DIC_PATH_LINUX}")
            mecab_args.append(f"-d {MECAB_DIC_PATH_LINUX}")
            tagger = MeCab.Tagger(" ".join(mecab_args))
        else:
            print("INFO: Windows/macOS環境を検出。デフォルトのシステム辞書を使用します。")
            tagger = MeCab.Tagger(" ".join(mecab_args))
    except RuntimeError as e:
        print(f"[警告] MeCabの初期化に失敗: {e}... 引数なしで再試行します...")
        tagger = MeCab.Tagger("-Owakati")  # フォールバック
    print("MeCab Taggerが正常に初期化されました。")
    return tagger


# --- 2. データベースのセットアップ (v5) ---
def setup_database_v5(tagger: MeCab.Tagger):
    """
    正規化された「事実テーブル」と「エイリアス（検索キー）テーブル」を作成します。
    [v5] facts_data のタプル項目数を修正。エイリアス登録ロジックを改善。
    """
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        # メインの事実（禁忌など）を格納するテーブル
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS core_facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disease_name TEXT NOT NULL,      -- 例: '人工股関節全置換術'
            description TEXT,                -- 例: '変形性股関節症の末期に行われる...'
            contraindications TEXT,          -- 例: '後方アプローチ後は、深屈曲・内転・内旋...'
            risks TEXT                       -- 例: 'DVTのリスクあり...'
        )
        """)

        # 検索キーワード（エイリアス）と事実IDを紐付けるテーブル
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS fact_aliases (
            alias TEXT NOT NULL,             -- 例: 'tha' (MeCabで抽出するキー)
            fact_id INTEGER NOT NULL,        -- core_factsのID
            PRIMARY KEY (alias, fact_id),    -- [v5.1 改善] (key, id) のペアでユニークに
            FOREIGN KEY (fact_id) REFERENCES core_facts (id)
        )
        """)

        # --- サンプルデータ挿入 (v5) ---

        # 1. core_facts に事実を登録
        facts_data = [
            # (disease_name, description, contraindications, risks) の4項目
            (
                "人工股関節全置換術",
                "THA (Total Hip Arthroplasty)",
                "後方アプローチ後は、脱臼リスクのため深屈曲・内転・内旋の複合動作は禁忌です。",
                "深部静脈血栓症(DVT)のリスクがあるため、早期離床と弾性ストッキングの着用が推奨されます。",
            ),
            (
                "人工膝関節全置換術",
                "TKA (Total Knee Arthroplasty)は、変形性膝関節症の末期に行われる手術です。",
                "術後早期の積極的な膝伸展筋力強化は骨癒合を妨げる危険があるためHTOでは禁忌だが、TKAでは推奨される。",
                "特になし",
            ),
            (
                "変形性股関節症",
                "寛骨臼蓋形成不全などに続発する二次性のものが多い。",
                "特になし",
                "運動療法と生活指導の併用が推奨される。",
            ),
            (
                "脳梗塞 (t-PA治療)",
                "t-PA (組織プラスミノーゲン活性化因子) 静注療法",
                "特になし",
                "治療後24時間は出血性梗塞のリスクが最も高いため、厳重な血圧管理が必要。",
            ),
            # [v5 修正] 5項目あったタプルを4項目に修正
            (
                "BM25",
                "BM25は、テキスト検索の関連性を評価するためのアルゴリズムで、キーワードの出現頻度と希少性に基づいています。",
                "特になし",
                "特になし",
            ),
        ]
        cursor.executemany(
            "INSERT INTO core_facts (disease_name, description, contraindications, risks) VALUES (?, ?, ?, ?)", facts_data
        )
        print(f"'{DB_FILE}' (core_facts) に {len(facts_data)} 件の事実を挿入。")

        # 2. fact_aliases に検索キーを登録
        aliases_data = [
            # ID: 1 (THA) へのエイリアス
            ("tha", 1),
            ("人工股関節", 1),
            # ID: 2 (TKA) へのエイリアス
            ("tka", 2),
            ("人工膝関節", 2),
            ("変形性膝関節症", 2),  # [v5 改善] TKAは変形性膝関節症の一種
            # ID: 3 (変形性股関節症) へのエイリアス
            ("変形性股関節症", 3),
            # ID: 4 (脳梗塞 t-PA) へのエイリアス
            ("t-pa", 4),
            ("脳梗塞", 4),
            # ID: 5 (BM25) へのエイリアス
            ("bm25", 5),
        ]

        # [v5.1 改善] INSERT OR IGNORE を使い、重複を許容する
        cursor.executemany("INSERT OR IGNORE INTO fact_aliases (alias, fact_id) VALUES (?, ?)", aliases_data)

        conn.commit()
        print(f"'{DB_FILE}' (fact_aliases) のセットアップ完了。{len(aliases_data)} 件の紐付けを試行。")

    except sqlite3.Error as e:
        print(f"[エラー] FTS5データベースのセットアップに失敗: {e}")
        conn.rollback()
    finally:
        conn.close()


# --- 3. キーワード抽出 (v5.1) ---
def extract_search_keys(text: str, tagger: MeCab.Tagger) -> List[str]:
    """
    テキストを形態素解析し、DBの 'fact_aliases' テーブルを検索するためのキーを抽出します。
    [v5.1] ストップワードを除外し、ユーザー辞書の単語を優先します。
    """
    node = tagger.parseToNode(text)
    keywords: Set[str] = set()

    while node:
        feature = node.feature.split(",")
        pos = feature[0]

        if pos in ["名詞", "動詞", "形容詞"]:
            original_form = feature[6].lower() if feature[6] != "*" else node.surface.lower()
            surface_form = node.surface.lower()
            pos_detail1 = feature[1]

            term_to_add = ""

            # 1. ユーザー辞書に登録された固有名詞を最優先 (例: "t-PA", "BM25")
            if pos == "名詞" and pos_detail1 == "固有名詞":
                term_to_add = surface_form

            # 2. その他の単語 (ハイフンは分割)
            elif original_form:
                # ハイフンを含む一般名詞などは分割
                if "-" in original_form and original_form not in ["t-pa"]:  # ユーザー辞書登録語は除外
                    keywords.update(t for t in original_form.split("-") if len(t) > 1 and t not in STOP_WORDS)
                    continue
                else:
                    term_to_add = original_form

            # 3. ストップワードリストと長さでフィルタリング
            if (
                len(term_to_add) > 1
                and term_to_add not in STOP_WORDS
                and pos_detail1 not in ["非自立", "代名詞", "数", "記号"]
            ):
                keywords.add(term_to_add)

        node = node.next

    return list(keywords)


# --- 4. DB検索 (SQL IN句を使用, 変更なし) ---
def search_facts_by_keys(keys: List[str]) -> List[dict]:
    """
    抽出されたキーリストに基づき、SQLのIN句で 'fact_aliases' テーブルを検索し、
    関連する事実を 'core_facts' テーブルから取得します。
    """
    if not keys:
        return []

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    placeholders = ",".join("?" * len(keys))

    sql_query = f"""
    SELECT DISTINCT
        T1.id,
        T1.disease_name,
        T1.description,
        T1.contraindications,
        T1.risks
    FROM core_facts AS T1
    JOIN fact_aliases AS T2 ON T1.id = T2.fact_id
    WHERE T2.alias IN ({placeholders})
    """

    try:
        cursor.execute(sql_query, tuple(keys))
        results = [dict(row) for row in cursor.fetchall()]
        return results
    except sqlite3.Error as e:
        print(f"[エラー] 事実DBの検索に失敗: {e} (Query: {sql_query}, Keys: {keys})")
        return []
    finally:
        conn.close()


# --- 5. メイン実行ブロック (エントリーポイント) ---
def main():
    """
    一連の処理を実行するメイン関数。
    """
    print("--- 事実DB (SQL完全一致 + MeCabユーザー辞書) デモ 開始 [v5.1] ---")

    try:
        tagger = init_mecab_with_user_dic()
    except Exception as e:
        print(f"[致命的エラー] MeCabの初期化に失敗しました: {e}")
        return

    setup_database_v5(tagger)

    test_cases = [
        "左変形性股関節症による人工股関節全置換術後（THA術後）",
        "脳梗塞でt-PA治療を行った患者",
        "TKA術後、変形性膝関節症の患者さんです",
        "BM25のアルゴリズムについて",
    ]

    print("\n--- 検索テスト開始 ---")

    for i, info_text in enumerate(test_cases):
        print("\n" + "=" * 50)
        print(f"【テストケース {i + 1}】")
        print(f"入力テキスト: 「{info_text}」")

        keys = extract_search_keys(info_text, tagger)
        print(f"抽出された検索キー: {keys}")

        search_results = search_facts_by_keys(keys)

        if search_results:
            print(f"\n--- 検索結果 ({len(search_results)}件) ---")
            for j, fact in enumerate(sorted(search_results, key=lambda x: x["id"])):  # ID順でソートして表示
                print(f"  [{j + 1}] {fact['disease_name']} (ID: {fact['id']})")
                print(f"      概要: {fact['description']}")
                print(f"      禁忌: {fact['contraindications']}")
                print(f"      ﾘｽｸ: {fact['risks']}")
        else:
            print("\n--- 検索結果 ---")
            print("  関連する事実は見つかりませんでした。")
        print("=" * 50)


if __name__ == "__main__":
    main()
