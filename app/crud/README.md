# CRUD Layer (`app/crud/`)

このディレクトリは、**Data Access Layer (DAL)** として機能します。
ビジネスロジック (`services`) からの要求を受け、データベース (`models`) に対する具体的な操作（Create, Read, Update, Delete）をカプセル化しています。

## 🏗 設計思想とアーキテクチャ (Design & Architecture)

このレイヤーでは、以下の設計方針に基づいてコードが実装されています。

### 1. セッションライフサイクルの管理 (Session Management)
* **原則**: 各関数内で `SessionLocal()` を呼び出してDBセッションを生成し、`try...finally` ブロックで確実に `db.close()` を行います。これにより、コネクションリークを防ぎます。
* **依存性の注入 (DI)**: `get_patient_data_for_plan` のように、引数で `db_session` を受け取れる関数も用意しています。これは、複数のCRUD操作を一つのトランザクション（Atomic操作）で実行したい場合に、呼び出し元（Service層）からセッションを引き回せるようにするためです。

### 2. フォームデータのロバストな変換 (Robust Data Conversion)
Webフォーム（HTML）から送信されるデータはすべて「文字列」です。
このレイヤーでは、SQLAlchemyのモデル定義（`__table__.columns`）をイントロスペクション（動的に検査）し、入力値を適切な型（`Integer`, `Boolean`, `Date` など）に自動変換するロジックを実装しています。これにより、コントローラー側での型変換コードを削減し、堅牢性を高めています。

### 3. オブジェクトから辞書への変換 (DTO-like Output)
SQLAlchemyのモデルインスタンスをそのまま返すと、セッションクローズ後にアクセスした際に `DetachedInstanceError` が発生する可能性があります。
そのため、多くの取得系関数では、モデルの属性を **Pythonの辞書（dict）** に変換して返却しています。これにより、View（テンプレート）側でセッションの状態を気にする必要がなくなります。

### 4. 履歴とスナップショットの保存 (History & Snapshots)
リハビリ計画書は法的な文書としての性質も持つため、「その時点でのデータ」を正確に保持する必要があります。
* **履歴管理**: 患者情報が更新されるたびに、計画書データ(`RehabilitationPlan`)は上書き更新（Update）するのではなく、常に新しいレコードを作成（Insert）する設計にしています。
* **JSONスナップショット**: `liked_items` や `patient_info` などの構造化データや、後で変更される可能性のあるマスタ情報は、その時点の状態をJSON文字列としてレコード内に保存しています。

---

## 📁 モジュール詳細と実装ロジック

### 1. `patient.py` (患者データ操作)

患者情報(`patients`)と、それに紐づく最新の計画書(`rehabilitation_plans`)を統合して扱うロジックが含まれています。

* **`get_patient_data_for_plan`**:
    * **データマージ**: `Patient` テーブルと最新の `RehabilitationPlan` テーブルの情報を結合し、1つのフラットな辞書として返します。これにより、フロントエンドは「患者オブジェクト」と「計画書オブジェクト」を意識せずにデータを表示できます。
    * **欠損値ハンドリング**: 計画書がまだ存在しない場合でもエラーにならないよう、カラム定義に基づいて `None` で埋められたダミーデータを生成・マージします。
* **`save_patient_master_data`**:
    * **複合トランザクション**: 「患者基本情報の保存/更新」と「新しい計画書ドラフトの作成」を1つのトランザクションで実行します。
    * **日付処理**: フォームから `_year`, `_month`, `_day` とバラバラに送られてくる日付データを結合し、有効な `date` オブジェクトに変換するロジックを内包しています。

### 2. `staff.py` (職員・権限管理)

職員アカウント(`staff`)と、担当患者の割り当て管理を行います。

* **担当割り当て (`assigned_patients`)**:
    * SQLAlchemyの `relationship` 機能を使い、中間テーブルを意識せずにリスト操作（`append`, `remove`）だけで多対多の関係を更新しています。
* **`get_patients_for_staff_with_liked_items`**:
    * **複雑な結合クエリ**: `Patient` -> `RehabilitationPlan` -> `LikedItemDetail` という3段のテーブル結合を行い、「特定の職員が過去に『いいね』などのアクションを起こした患者」を抽出します。これは担当患者以外のアクセス履歴を追うために使用されます。

### 3. `plan.py` (計画書・評価データ)

計画書の保存、AI提案へのフィードバック（いいね）、履歴管理を行う、最もロジックが集中しているモジュールです。

* **`save_new_plan`**:
    * **動的マッピング**: `form_data` のキーとモデルのカラム名を突き合わせ、一致するものだけを保存します。これにより、フォームに不要なフィールドが含まれていても無視され、安全性が保たれます。
* **`save_suggestion_like` (UPSERT)**:
    * **MySQL固有機能**: `sqlalchemy.dialects.mysql.insert` を使用し、`ON DUPLICATE KEY UPDATE` 構文を生成しています。
    * **ロジック**: 同じ項目に対して既に「いいね」がある場合は更新、なければ挿入という処理を、1回のクエリで効率的に実行します。
* **`save_all_suggestion_details`**:
    * **バルクインサート**: `db.bulk_save_objects` を使用しています。AIが生成した大量の提案データを個別にINSERTするのではなく、一括で保存することでパフォーマンスを最適化しています。
    * **フィルタリング**: 内容が「特記なし」や空の提案は保存対象から除外するクレンジング処理を含みます。

---

## 💻 使用例 (Usage Example)

```python
from app.crud import patient, plan

# 1. 患者ID=1 の全データを取得（基本情報 + 最新計画 + いいね状況）
data = patient.get_patient_data_for_plan(1)

# 2. 取得した辞書データには、全てのカラムがフラットに含まれている
print(f"患者名: {data['name']}")
print(f"最新のADL評価: {data['activities_of_daily_living']}")

# 3. AI提案へのいいねを保存 (UPSERTロジックが働く)
# スタッフID 5 が、患者ID 1 の 'long_term_goal' に対して 'Gemini' 案にいいねした場合
plan.save_suggestion_like(
    patient_id=1,
    item_key='long_term_goal',
    liked_model='gemini',
    staff_id=5
)