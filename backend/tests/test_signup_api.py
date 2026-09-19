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


def test_approved_signups_are_not_subject_to_a_fixed_account_cap(signup_setup):
    assert signup(signup_setup, "firstuser").status_code == 201
    assert signup(signup_setup, "seconduser").status_code == 201
    assert signup(signup_setup, "thirduser").status_code == 201

    from app.models.database import engine
    with engine.connect() as connection:
        assert connection.execute(text("select count(*) from users")).scalar_one() == 3


def test_signup_attempts_are_throttled(signup_setup):
    for _ in range(5):
        assert signup(signup_setup, code="wrong-code").status_code == 403
    assert signup(signup_setup, code="wrong-code").status_code == 429
