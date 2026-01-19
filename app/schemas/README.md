# Schemas Layer (`app/schemas/`)

このディレクトリは、**Pydantic** を用いたデータスキーマ定義を管理しています。

一般的なWebアプリケーションにおける「APIリクエスト/レスポンスの型定義」としての役割に加え、本システムでは **「LLM (Generative AI) に対する出力形式の指示書」** という極めて重要な役割を担っています。

## 🏗 アーキテクチャと設計思想

### 1. Pydanticによる構造化出力 (Structured Output)
GeminiやOllamaなどのLLMに対し、自由なテキストではなく **「特定のJSONフォーマット」** で回答させるために、Pydanticモデルを使用しています。
LLMクライアントは、ここのクラス定義を参照して「どのようなキーが必要か」「値の型は何か（数値、文字列、Boolean）」を理解し、JSONを生成します。

### 2. Prompt Engineeringとしてのスキーマ定義
各フィールドの `Field(description="...")` は、単なるドキュメントではありません。
これは **AIへのプロンプト（指示）そのもの** です。
* **例**: `main_risks_txt` の `description` に「50文字程度で記述」と書くことで、AIの生成する文字数を制御しています。
* **メリット**: ロジックコード (`services/`) を変更することなく、スキーマの定義を書き換えるだけでAIの出力の質や内容を調整できます。

### 3. トークン制限対策のための分割 (Segmentation)
リハビリ計画書は項目数が数百に及ぶため、一度のAPIコールですべてを生成させようとすると、LLMの出力トークン制限を超えたり、精度が低下したりします。
そのため、`GENERATION_GROUPS` や `PATIENT_INFO_EXTRACTION_GROUPS` のように、巨大なスキーマを意味のある単位（「運動機能」「栄養」「目標」など）に分割して定義しています。

---

## 📁 内部ファイル詳細

### `schemas.py`
アプリケーションで使用される全てのPydanticモデルが集約されています。

#### 主なモデルクラス
* **`RehabPlanSchema`**:
    * リハビリ計画書の「生成」に関する全項目を定義したマスタースキーマ。
    * AIが生成すべき考察や目標文の指示（プロンプト）が記述されています。
* **`PatientMasterSchema`**:
    * カルテ等のテキストから情報を「抽出」するための全項目を定義したマスタースキーマ。
    * 抽出されたデータは、生成フェーズでの入力として使用されます。

#### グループ化定義 (Grouping)
処理のフェーズに合わせて、マスタースキーマを部分的に切り出したサブクラス群です。

* **生成用 (`CurrentAssessment`, `Goals`, `TreatmentPolicy` ...)**:
    * 計画書をセクションごとに段階的に生成するために使用します。
* **抽出用 (`PatientInfo_ADL`, `PatientInfo_Nutrition` ...)**:
    * 長文のカルテから特定のカテゴリ（例：ADLの点数だけ）に絞って情報を抽出するために使用します。
* **ハイブリッド用 (`HybridStep1B_Assessment` ...)**:
    * 正規表現やGLiNERで抽出できなかった部分をLLMで補完しつつ、生成も同時に行うための最適化されたスキーマです。

## 🔗 関係性

* **⬅️ Used by `app/services/llm/`**:
    * `gemini.py` や `ollama.py` が、`generation_config` や `response_schema` としてこれらのクラスを使用します。
* **⬅️ Used by `app/services/llm/patient_info_parser.py`**:
    * テキスト解析の結果をこれらのクラスのインスタンスとして受け取り、検証します。
* **Matches `app/models/`**:
    * 基本的にデータベースのモデル（SQLAlchemy）と同じフィールド名を持っていますが、こちらは「AIとの対話用」に特化しています。

## 📝 開発者向けメモ

### AIの回答精度を調整したい場合
コードのロジックを触る前に、まずは `schemas.py` 内の `description` を修正することを検討してください。
* 「もっと具体的に書いてほしい」
* 「断定的な表現にしてほしい」
* 「文字数を減らしてほしい」
といった要望は、`description` の変更で解決できる場合が大半です。

### 新しい項目を追加する場合
1.  `app/models/plan.py` (DB定義) にカラムを追加。
2.  `app/schemas/schemas.py` (Pydantic定義) にフィールドと `description` を追加。
3.  必要であれば `GENERATION_GROUPS` などのリストにも追加。