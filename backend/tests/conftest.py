import os
import uuid
import pytest
from fastapi.testclient import TestClient

# Tests use an isolated SQLite file, never the active local-development database.
os.environ["DATABASE_URL"] = "sqlite:///./test-parcelpulse-auth.db"
os.environ["SESSION_SECRET"] = "test-only-session-secret-that-is-long-enough"

@pytest.fixture
def authenticated_client():
    from app.auth import hash_password
    from app.main import app
    from app.models.database import SessionLocal, User
    client = TestClient(app)
    session = SessionLocal()
    username = f"testuser{uuid.uuid4().hex[:12]}"
    session.add(User(username=username, password_hash=hash_password("test-only-password")))
    session.commit(); session.close()
    assert client.post("/api/auth/login", json={"username": username, "password": "test-only-password"}).status_code == 200
    return client
