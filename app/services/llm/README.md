# LLM Integration Layer (`app/services/llm/`)

このディレクトリは、大規模言語モデル (LLM) へのインターフェースと、RAG (検索拡張生成) パイプラインの実行ロジックを提供するレイヤーです。

**Strategyパターン** を採用し、クラウドAI (Gemini) とローカルAI (Ollama) を環境変数一つで切り替えられる柔軟な設計になっています。また、**Server-Sent Events (SSE)** に対応したストリーミング生成をサポートしており、ユーザーにリアルタイムな生成体験を提供します。

## 🏗 アーキテクチャと設計思想

### 1. Strategyパターンによる抽象化 (`base.py`)
`LLMClient` という抽象基底クラス (Abstract Base Class) を定義し、全てのLLM実装（`GeminiClient`, `OllamaClient`）はこれを継承しています。
これにより、上位レイヤー（`routers` や `services`）は、現在使用されているモデルがGeminiなのかOllamaなのかを意識することなく、共通のメソッド（`generate_plan_stream` など）を呼び出すだけで済みます。

### 2. ストリーミング生成 (Streaming Generation)
AIの回答生成には時間がかかります。ユーザーを待たせないため、全ての生成メソッドは Pythonの **Generator (`yield`)** として実装されています。
LLMからトークンが届くたびに即座にフロントエンドへプッシュ送信することで、ChatGPTのような「文字が打たれていく」UIを実現しています。

### 3. RAGとの疎結合 (`rag_executor.py`)
RAG機能は、検索ロジックを持つ `RAGExecutor` と、生成能力を持つ `LLMClient` が連携して動作します。
`RAGExecutor` が関連文書を検索してコンテキストを構築し、それを `LLMClient` に渡して回答を生成させるという役割分担が明確になされています。

---

## 📁 主要ファイル詳細

### `base.py`
* **役割**: LLMクライアントのインターフェース定義（契約）。
* **主要メソッド**:
    * `generate_plan_stream()`: 通常モデルによる計画書生成。
    * `generate_rag_plan_stream()`: RAGを用いた専門的な計画書生成。
    * `regenerate_plan_item_stream()`: ユーザー指示による特定項目の書き直し。
    * `generate_json()`: テキスト解析用の構造化データ生成（非ストリーミング）。

### `gemini.py`
* **役割**: Google **Gemini API** (Gemini 1.5 Pro/Flash) の実装。
* **特徴**:
    * `google.generativeai` ライブラリを使用。
    * APIキー認証。
    * 高速かつ高品質な生成が可能。

### `ollama.py`
* **役割**: ローカルLLMランナー **Ollama** の実装。
* **特徴**:
    * `ollama` ライブラリを使用し、ローカルサーバー (`localhost:11434`) と通信。
    * プライバシー重視やオフライン環境での利用を想定。
    * `qwen2.5` や `llama3` などのモデルに対応。

### `rag_executor.py`
* **役割**: `Rehab_RAG` ライブラリへのブリッジ。
* **ロジック**:
    1. `rag_config.yaml` を読み込み、パイプラインコンポーネント（Retriever, Reranker等）を初期化。
    2. 患者情報をクエリとして関連ガイドラインを検索。
    3. 検索結果 (`contexts`) と患者情報を組み合わせてプロンプトを作成。
    4. LLMに生成を依頼し、回答と根拠文書をセットで返却。

### `patient_info_parser.py`
* **役割**: 雑多なテキスト（申し送り事項など）から、患者情報を抽出して構造化データ（JSON）に変換するパーサー。
* **ロジック**:
    * `FastExtractor` (GLiNER) と連携する「ハイブリッドモード」と、LLMのみで抽出する「標準モード」を搭載。
    * Pydanticモデル (`schemas.py`) を使用して、出力フォーマットを厳密に制御・検証しています。

### `prompts.py`
* **役割**: AIへの指示書（プロンプト）テンプレートを管理。
* **内容**:
    * システムプロンプト（「あなたは熟練した理学療法士です...」）。
    * 各入力項目（ADL、リスク等）を出力させるための具体的な指示。
    * 変数埋め込み用プレースホルダー (`{age}`, `{disease_name}` 等)。

### `context_builder.py`
* **役割**: 患者データや検索されたドキュメントを、LLMに入力するための文字列形式に整形するヘルパー。

## 🔗 依存関係

* **Uses `app/schemas/`**: LLMの出力形式（JSON構造）を定義したPydanticモデルを参照します。
* **Uses `Rehab_RAG/`**: 高度な検索機能を利用するために外部ライブラリとしてインポートします。
* **Used by `app/services/rag_manager.py`**: シングルトン管理のために呼び出されます。
* **Used by `app/routers/plan/api.py`**: APIエンドポイントから生成リクエストを受け取ります。

## 📝 開発者向けメモ

* **新しいLLMの追加**: 例えば `OpenAIClient` を追加したい場合は、`base.py` の `LLMClient` を継承したクラスを作成し、`app/__init__.py` や設定読み込みロジックに追加するだけで実装可能です。
* **プロンプトエンジニアリング**: 生成の質を改善したい場合は、コードロジックではなく `prompts.py` のテキストを修正するのが最も効果的です。