import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

def _get_authenticated_client(base_client, username, password, db_session):
    from app.models.user import User
    from app.seed.seed_data import seed_database
    if not db_session.query(User).filter(User.username == username).first():
        seed_database(db_session)
    
    login_res = base_client.post("/api/auth/login", data={"username": username, "password": password})
    if login_res.status_code != 200:
        raise RuntimeError(f"Login failed for {username}: {login_res.text}")
    token = login_res.json()["access_token"]
    base_client.headers.update({"Authorization": f"Bearer {token}"})
    return base_client

@pytest.fixture
def admin_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield _get_authenticated_client(test_client, "admin", "Admin@123", db_session)
    app.dependency_overrides.clear()

@pytest.fixture
def alice_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield _get_authenticated_client(test_client, "alice", "User@123", db_session)
    app.dependency_overrides.clear()

@pytest.fixture
def bob_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield _get_authenticated_client(test_client, "bob", "User@123", db_session)
    app.dependency_overrides.clear()
