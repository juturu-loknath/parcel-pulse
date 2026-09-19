import uuid
from fastapi.testclient import TestClient
from app.auth import hash_password
from app.main import app
from app.models.database import SessionLocal, User

def test_login_persists_for_the_session_and_logout_revokes_access():
    client = TestClient(app); username = f"account{uuid.uuid4().hex[:12]}"
    session = SessionLocal(); session.add(User(username=username, password_hash=hash_password("test-only-password"))); session.commit(); session.close()
    assert client.get("/api/auth/me").status_code == 401
    login = client.post("/api/auth/login", json={"username": username, "password": "test-only-password"})
    assert login.status_code == 200
    assert login.headers["cache-control"] == "no-store"
    assert client.get("/api/auth/me").json()["username"] == username
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401

def test_invalid_credentials_are_throttled_without_revealing_account_existence():
    client = TestClient(app); username = f"missing{uuid.uuid4().hex[:12]}"
    for _ in range(5):
        assert client.post("/api/auth/login", json={"username": username, "password": "wrong-password"}).status_code == 401
    assert client.post("/api/auth/login", json={"username": username, "password": "wrong-password"}).status_code == 429
