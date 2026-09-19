from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text


@pytest.fixture
def signup_setup(monkeypatch):
    from app.main import app
    from app.models.database import engine

    monkeypatch.setenv("SIGNUP_ENABLED", "true")
    monkeypatch.setenv("PRIVATE_SIGNUP_CODE", "fictional-private-code")
    with engine.begin() as connection:
        connection.execute(text("delete from parcels"))
        connection.execute(text("delete from login_attempts"))
        connection.execute(text("delete from users"))
    return TestClient(app)


def signup(client, username="newuser", password="simple", code="fictional-private-code"):
    return client.post("/api/auth/signup", json={"username": username, "password": password, "signup_code": code})


def test_signup_is_disabled_by_default(monkeypatch):
    from app.main import app
    from app.models.database import engine

    monkeypatch.delenv("SIGNUP_ENABLED", raising=False)
    monkeypatch.delenv("PRIVATE_SIGNUP_CODE", raising=False)
    with engine.begin() as connection:
        connection.execute(text("delete from parcels")); connection.execute(text("delete from login_attempts")); connection.execute(text("delete from users"))
    assert signup(TestClient(app)).status_code == 403


def test_signup_rejects_incorrect_code(signup_setup):
    assert signup(signup_setup, code="wrong-code").status_code == 403


def test_signup_accepts_a_simple_nonempty_password_and_can_log_in(signup_setup):
    assert signup(signup_setup, password="a").status_code == 201
    assert signup_setup.post("/api/auth/logout").status_code == 204
    assert signup_setup.post("/api/auth/login", json={"username": "newuser", "password": "a"}).status_code == 200


def test_signup_stops_at_two_private_accounts(signup_setup):
    assert signup(signup_setup, "firstuser").status_code == 201
    assert signup(signup_setup, "seconduser").status_code == 201
    assert signup(signup_setup, "thirduser").status_code == 409


def test_concurrent_signup_attempts_cannot_exceed_two_accounts(signup_setup):
    def attempt(number):
        return signup(TestClient(signup_setup.app), f"person{number}").status_code

    with ThreadPoolExecutor(max_workers=4) as executor:
        statuses = list(executor.map(attempt, range(4)))

    assert statuses.count(201) == 2
    assert statuses.count(409) == 2


def test_signup_attempts_are_throttled(signup_setup):
    for _ in range(5):
        assert signup(signup_setup, code="wrong-code").status_code == 403
    assert signup(signup_setup, code="wrong-code").status_code == 429
