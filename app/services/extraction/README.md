# Information Extraction Layer (`app/services/extraction/`)

このディレクトリは、医師やセラピストが記述した**自由記述のテキスト（非構造化データ）**から、リハビリ計画書に必要な**構造化データ（事実）**を抽出するためのロジックを提供します。

LLM（Generative AI）は柔軟ですが、時としてハルシネーション（嘘）をついたり、単純な事実を見落とすことがあります。
本モジュールでは、**Named Entity Recognition (NER)** モデルと**正規表現**を組み合わせることで、LLMの弱点を補完し、より堅牢な情報抽出パイプラインを実現しています。

## 🏗 アーキテクチャと抽出ロジック

### ハイブリッド抽出アプローチ (Hybrid Extraction Strategy)
`FastExtractor` クラスは、以下の3つの手法を順次実行し、情報の取りこぼしを防ぐ「3段構え」の設計になっています。

1.  **正規表現 (Regex) [高精度・高速]**:
    * 「年齢」「性別」「氏名」「発症日」など、フォーマットが決まっている情報は正規表現で確実に取得します。
    * 例: `r'(\d{1,3})歳'` というパターンで年齢を抽出。
2.  **GLiNER2 (Zero-shot NER) [文脈理解]**:
    * **GLiNER (Generalist Model for Named Entity Recognition)** という軽量かつ高性能なNERモデルを使用しています。
    * 事前に定義したラベル（例: 「高血圧」「麻痺」「嚥下障害」）に基づき、文脈の中から該当する表現を抽出します。
    * 「右片麻痺」という単語から `func_motor_paralysis_chk` (麻痺あり) を検出するなど、意味的なマッピングを行います。
3.  **キーワードバックアップ (Keyword Fallback) [安全性]**:
    * 「痛み」「拘縮」など、計画書作成において見落とすとクリティカルな項目については、単純なキーワード検索を行い、GLiNERが見落とした場合でも強制的にフラグを立てる安全策を講じています。

## 📁 内部ファイル詳細

### `fast_extractor.py`
* **役割**: 情報抽出の実行エンジン。
* **主な機能**:
    * **`label_mapping`**: アプリケーションのデータベースカラム（例: `func_risk_diabetes_chk`）と、自然言語での表現（例: "DM", "糖尿病", "血糖値が高い"）の対応関係を定義した辞書。
    * **`extract_facts(text)`**: テキストを受け取り、抽出された事実をフラットな辞書形式で返します。
* **依存ライブラリ**:
    * `gliner2`: NERモデル本体。
    * `torch`: PyTorch（GPUがあればCUDAを使用し、なければCPUで動作）。

## 🔗 関係性

* **⬅️ Used by `app/services/llm/patient_info_parser.py`**:
    * 「ハイブリッドモード」が有効な場合、`PatientInfoParser` はまずこの `FastExtractor` を呼び出して基礎的な事実を抽出します。その後、抽出された情報をLLMへのプロンプトに「ヒント」として埋め込み、最終的な整合性をLLMに判断させます。
* **➡️ Output Format**:
    * 返却される辞書のキーは、`app/models/plan.py` や `app/schemas/schemas.py` で定義されているフィールド名と一致するように設計されています。

## 📝 開発者向けメモ

* **セットアップ**: このモジュールを使用するには、追加のライブラリが必要です。`requirementsGPU.txt` または `requirementsCPU.txt` に含まれる `gliner2` と `torch` をインストールしてください。
* **ラベルの調整**: 新しい疾患や症状に対応させたい場合は、`fast_extractor.py` 内の `self.label_mapping` に単語を追加するだけで、再学習なしで認識精度を向上させることができます。