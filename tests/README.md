# Test Suite (`tests/`)

このディレクトリには、アプリケーションの機能が正しく動作することを検証するための自動テストコードが含まれています。
テスティングフレームワークとして **pytest** を使用しており、データベースやAIモデル（LLM）などの外部依存を適切にモック（模擬）することで、安全かつ高速にテストを実行できる設計になっています。

## 📁 内部ファイルの構成と役割

### ⚙️ 設定・共通フィクスチャ
* **`conftest.py`**:
    * **役割**: テスト全体で共有される設定と「フィクスチャ (Fixture)」を定義するファイルです。
    * **主なフィクスチャ**:
        * `app`: テスト用のFlaskアプリケーションインスタンスを作成します（`TESTING=True`）。
        * `client`: ブラウザの代わりにHTTPリクエストを送るテスト用クライアント。
        * `db_session`: テストごとに作成・ロールバックされるデータベースセッション。これにより、テスト間のデータ汚染を防ぎます。
        * `init_database`: テスト開始時にインメモリSQLiteデータベースにテーブルを作成します。

### 🧪 テストファイル群
機能ごとにテストファイルが分割されています。

#### ルーティング・結合テスト (Integration Tests)
* **`test_auth.py`**: ログイン、ログアウト、サインアップ機能の正常系・異常系をテストします。
* **`test_admin.py`**: 管理者専用ページのアクセス権限や、職員管理機能をテストします。
* **`test_patient_routes.py`**: 患者情報の登録、一覧表示、編集機能のルーティングをテストします。
* **`test_plan_routes.py`**: 計画書作成ウィザードの画面遷移やデータ保存フローをテストします。
* **`test_api_routes.py`**: AIストリーミングAPIや「いいね」保存APIの動作を検証します。

#### ビジネスロジック・単体テスト (Unit Tests)
* **`test_patient_service.py`**: フォームデータの正規化ロジック (`normalize_form_data`) など、Service層の関数を単体でテストします。
* **`test_excel_writer.py`**: テンプレートを用いたExcel出力がエラーなく行われるか、正しいセルに書き込まれるかを検証します。
* **`test_utils.py`**: 権限チェックデコレータやヘルパー関数をテストします。

#### AI・LLM関連テスト
* **`test_llm_comprehensive.py`**: 実際のAPIを呼ばずに、LLMの応答をモック（偽装）して、ストリーミング生成のロジックが正しく動くかを検証します。
* **`test_rag_manager.py`**: RAGパイプラインのロードやシングルトン管理が機能しているかを確認します。

## 🏗 テスト設計と戦略

### 1. データベースの分離 (Isolation)
テスト実行時は、本番用MySQLデータベースではなく、**オンメモリのSQLiteデータベース**（またはテスト用DB）を使用するように構成されています。
`conftest.py` 内で `session` フィクスチャがトランザクション管理を行い、テスト関数が終了するたびにデータをロールバックするため、常にクリーンな状態でテストを開始できます。

### 2. LLMのモック化 (Mocking)
GeminiやOllamaへのAPIリクエストは、実行に時間がかかり、課金も発生します。
そのため、LLM関連のテストでは `unittest.mock` を使用してAPIクライアントを差し替え、**「AIが即座に返答したことにして」** アプリケーション側の処理（保存、表示など）をテストしています。

### 3. Factory Boy / Faker (データ生成)
（導入されている場合）テスト用のダミーデータ（患者名、IDなど）をランダムに生成し、様々なパターンの入力に対する堅牢性を検証します。

---

## 📖 Pytest ガイド (How to use Pytest)

### 1. テストの実行方法

プロジェクトのルートディレクトリで以下のコマンドを実行します。

```bash
# 全てのテストを実行
pytest

# 特定のファイルだけ実行
pytest tests/test_auth.py

# 詳細なログを表示 (-v: verbose)
pytest -v

# 標準出力（print文）を表示して実行 (-s)
pytest -s

```

### 2. Pytestの基本的な書き方

テストファイル名は `test_` で始め、関数名も `test_` で始める必要があります。

```python
# tests/test_example.py

def test_addition():
    """足し算のテスト"""
    assert 1 + 1 == 2

def test_login_page(client):
    """
    ログインページの表示テスト
    引数 'client' は conftest.py で定義されたフィクスチャが自動注入されます
    """
    response = client.get('/login')
    assert response.status_code == 200
    assert b"ログイン" in response.data

```

### 3. フィクスチャ (Fixture) の活用

前処理や後処理を共通化する機能です。`conftest.py` に書くと全テストで使えます。

```python
import pytest

@pytest.fixture
def sample_user():
    return {"name": "Test User", "role": "admin"}

def test_user_role(sample_user):
    # 引数名とフィクスチャ名を一致させるとデータを受け取れる
    assert sample_user["role"] == "admin"

```

### 4. モック (Mock) の活用

外部APIなどを偽装する場合に使用します。

```python
from unittest.mock import patch

def test_external_api():
    # app.services.llm.gemini.GeminiClient.generate メソッドを偽装
    with patch('app.services.llm.gemini.GeminiClient.generate') as mock_method:
        # 偽の返り値を設定
        mock_method.return_value = "AIからの返答です"
        
        # ここで実際の処理を呼ぶ...
        
        # モックが呼ばれたか確認
        mock_method.assert_called_once()

```

## 📝 開発者向けメモ

* **テスト駆動開発 (TDD)**: 新しい機能を追加する際は、先にテストケース（期待する動作）を書いてから実装を行うと、バグの少ないコードが書けます。
* **カバレッジ**: 全てのコード行をテストする必要はありませんが、重要なビジネスロジックや分岐条件は網羅するようにしましょう。
