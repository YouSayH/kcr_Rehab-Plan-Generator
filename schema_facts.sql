-- 1. 既存のテーブルがあれば削除（初期化用）
DROP TABLE IF EXISTS fact_aliases;
DROP TABLE IF EXISTS core_facts;

-- 2. 事実データ本体のテーブル作成
CREATE TABLE core_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,          -- 正式名称
    category TEXT,                      -- カテゴリ (疾患, 手術, 合併症 etc.)
    description TEXT,                   -- 概要
    contraindications TEXT,             -- 禁忌
    risks TEXT                          -- リスク
);

-- 3. 検索用エイリアスのテーブル作成
CREATE TABLE fact_aliases (
    alias TEXT NOT NULL,                -- 検索キーワード (THA, 変形性膝関節症...)
    fact_id INTEGER NOT NULL,           -- 事実ID
    PRIMARY KEY (alias, fact_id),       -- 複合主キー
    FOREIGN KEY (fact_id) REFERENCES core_facts(id) ON DELETE CASCADE
);

-- 4. インデックスの作成（検索高速化のため）
CREATE INDEX idx_fact_aliases_alias ON fact_aliases(alias);