import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

# アプリケーションのDB定義モジュールをインポート
import app.core.database as database

# ファクトリ関数をインポート
from app import create_app
from app.models import Base, Staff


# クラス定義にはデコレータをつけない
class MockUser:
    def __init__(self, id, role="staff", username="test_user", is_authenticated=True):
        self.id = id
        self.role = role
        self.username = username
        self.is_authenticated = is_authenticated

@pytest.fixture(scope="function")
def app():
    """Flaskアプリケーションのフィクスチャ (テストごとに初期化)"""

    # 1. テスト用のインメモリSQLiteエンジンを作成
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    # 2. databaseモジュールの engine と SessionLocal をテスト用に差し替える (モンキーパッチ)
    # これにより、アプリ本体のコード(auth.pyなど)が SessionLocal() を呼んだ時も、
    # このテスト用DBにつながるようになります。
    original_engine = database.engine
    original_session_local = database.SessionLocal

    database.engine = test_engine
    database.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # 3. テスト用設定でアプリを作成 (Application Factory)
    # create_app にテスト設定を渡すことで、configの更新もここで行われます
    flask_app = create_app(test_config={
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test_secret_key",
    })

    # テストごとにテーブルを作成
    # 【注意】Baseは app.models からインポートしたものを使用
    with flask_app.app_context():
        Base.metadata.create_all(bind=test_engine)
        yield flask_app
        Base.metadata.drop_all(bind=test_engine)

    # 4. テスト終了後に元の設定に戻す (後始末)
    database.engine = original_engine
    database.SessionLocal = original_session_local

@pytest.fixture(scope="function")
def client(app):
    """テストクライアントのフィクスチャ"""
    return app.test_client()

@pytest.fixture(scope="function")
def db_session(app): # appフィクスチャに依存させることでパッチ適用後のSessionを使う
    """データベースセッションのフィクスチャ"""
    session = database.SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
def login_staff(client, db_session):
    """ログイン済みのクライアントを提供するヘルパーフィクスチャ"""
    username = "test_user"
    password = "password"

    # ユーザー作成
    staff = db_session.query(Staff).filter_by(username=username).first()
    if not staff:
        staff = Staff(
            username=username,
            password=generate_password_hash(password),
            occupation="PT",
            role="staff",
            # 通常業務中の職員を想定する。既定値の True のままだと
            # パスワード変更の強制ガードにより全リクエストが 302 になる。
            must_change_password=False,
        )
        db_session.add(staff)
        db_session.commit()

    # ログイン
    client.post("/login", data={
        "username": username,
        "password": password
    }, follow_redirects=True)

    return client


@pytest.fixture(scope="function")
def assign_patient(db_session):
    """患者をログイン中の職員(test_user)の担当に割り当てるヘルパー。

    患者データを扱うルートは担当患者であることを要求するため、
    正常系のテストではこのフィクスチャで割り当てておく必要があります。
    担当外からのアクセスが拒否されることを確かめたい場合は、
    あえて割り当てずにテストしてください。
    """
    def _assign(patient, username="test_user"):
        staff = db_session.query(Staff).filter_by(username=username).first()
        assert staff is not None, f"職員 {username} が存在しません"
        staff.assigned_patients.append(patient)
        db_session.commit()
        return patient

    return _assign
