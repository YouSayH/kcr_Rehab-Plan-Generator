import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

# アプリケーションのDB定義モジュールをインポート
import app.core.database as database
from app.core.database import Base, Staff
from app.main import app as flask_app


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

    # Flaskの設定更新
    flask_app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test_secret_key",
    })

    # テストごとにテーブルを作成
    with flask_app.app_context():
        Base.metadata.create_all(bind=test_engine)
        yield flask_app
        Base.metadata.drop_all(bind=test_engine)

    # 3. テスト終了後に元の設定に戻す (後始末)
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
            role="staff"
        )
        db_session.add(staff)
        db_session.commit()

    # ログイン
    client.post("/login", data={
        "username": username,
        "password": password
    }, follow_redirects=True)

    return client
