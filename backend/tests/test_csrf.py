from fastapi.testclient import TestClient
from app.main import app

def test_cross_site_write_is_rejected_before_login():
    client = TestClient(app)
    response = client.post("/api/auth/login", headers={"Origin": "https://attacker.invalid"}, json={"username": "testuser", "password": "test-only-password"})
    assert response.status_code == 403
