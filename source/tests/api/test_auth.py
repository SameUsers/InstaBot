import pytest
from sqlalchemy import create_engine, delete
from fastapi.testclient import TestClient

from main import app
from source.conf import settings
from source.models.user import User


REGISTER_URL = "/v1/auth/registration"
LOGIN_URL = "/v1/auth/login"
REFRESH_URL = "/v1/auth/refresh"
DB_URL = settings.db_url_sync


@pytest.fixture(autouse=True)
def cleanup_users():
    emails = [
        "testuser@example.com",
        "dup@example.com",
        "wrongpass@example.com",
        "noone@example.com",
    ]
    engine = create_engine(DB_URL)
    with engine.begin() as conn:
        for email in emails:
            conn.execute(delete(User).where(User.email == email))
    yield
    with engine.begin() as conn:
        for email in emails:
            conn.execute(delete(User).where(User.email == email))
    engine.dispose()


def test_registration_login_refresh_flow():
    with TestClient(app) as client:
        email = "testuser@example.com"
        username = "testuser"
        password = "Str0ngPassw!rd"

        reg_resp = client.post(REGISTER_URL, json={
            "email": email,
            "username": username,
            "password": password,
        })
        assert reg_resp.status_code == 200

        login_resp = client.post(LOGIN_URL, json={
            "email": email,
            "password": password,
        })
        assert login_resp.status_code == 200
        login_json = login_resp.json()

        refresh_resp = client.post(REFRESH_URL, params={
            "refresh_token": login_json["refresh_token"],
        })
        assert refresh_resp.status_code == 200

        fail_resp = client.post(REFRESH_URL, params={
            "refresh_token": login_json["refresh_token"],
        })
        assert fail_resp.status_code == 400


def test_registration_duplicate_email():
    with TestClient(app) as client:
        email = "dup@example.com"
        username = "dupuser"
        password = "Str0ngPassw!rd"

        first = client.post(REGISTER_URL, json={
            "email": email,
            "username": username,
            "password": password,
        })
        assert first.status_code == 200

        second = client.post(REGISTER_URL, json={
            "email": email,
            "username": username,
            "password": password,
        })
        assert second.status_code == 400


def test_login_wrong_password_and_unknown_email():
    with TestClient(app) as client:
        email = "wrongpass@example.com"
        username = "wpuser"
        password = "CorrectPass1!"

        reg = client.post(REGISTER_URL, json={
            "email": email,
            "username": username,
            "password": password,
        })
        assert reg.status_code == 200

        wrong = client.post(LOGIN_URL, json={
            "email": email,
            "password": "TotallyWrong!1",
        })
        assert wrong.status_code == 401

        unknown = client.post(LOGIN_URL, json={
            "email": "noone@example.com",
            "password": "Whatever1!",
        })
        assert unknown.status_code == 401


def test_refresh_with_invalid_token():
    with TestClient(app) as client:
        bad = client.post(REFRESH_URL, params={"refresh_token": "not-a-jwt"})
        assert bad.status_code == 400


def test_registration_invalid_email():
    with TestClient(app) as client:
        resp = client.post(REGISTER_URL, json={
            "email": "not-an-email",
            "username": "validuser",
            "password": "ValidPass123"
        })
        assert resp.status_code == 422


def test_registration_short_username():
    with TestClient(app) as client:
        resp = client.post(REGISTER_URL, json={
            "email": "test@example.com",
            "username": "ab",
            "password": "ValidPass123"
        })
        assert resp.status_code == 422


def test_registration_long_username():
    with TestClient(app) as client:
        resp = client.post(REGISTER_URL, json={
            "email": "test@example.com",
            "username": "a" * 33,
            "password": "ValidPass123"
        })
        assert resp.status_code == 422


def test_registration_short_password():
    with TestClient(app) as client:
        resp = client.post(REGISTER_URL, json={
            "email": "test@example.com",
            "username": "validuser",
            "password": "Sh0rt"
        })
        assert resp.status_code == 422


def test_registration_long_password():
    with TestClient(app) as client:
        resp = client.post(REGISTER_URL, json={
            "email": "test@example.com",
            "username": "validuser",
            "password": "A" * 65
        })
        assert resp.status_code == 422


def test_registration_empty_fields():
    with TestClient(app) as client:
        resp = client.post(REGISTER_URL, json={})
        assert resp.status_code == 422


def test_login_invalid_email():
    with TestClient(app) as client:
        resp = client.post(LOGIN_URL, json={
            "email": "not-an-email",
            "password": "ValidPass123"
        })
        assert resp.status_code == 422


def test_login_short_password():
    with TestClient(app) as client:
        resp = client.post(LOGIN_URL, json={
            "email": "test@example.com",
            "password": "Sh0rt"
        })
        assert resp.status_code == 422


def test_login_empty_fields():
    with TestClient(app) as client:
        resp = client.post(LOGIN_URL, json={})
        assert resp.status_code == 422


def test_refresh_empty_token():
    with TestClient(app) as client:
        resp = client.post(REFRESH_URL, params={"refresh_token": ""})
        assert resp.status_code == 400


def test_refresh_expired_token():
    with TestClient(app) as client:
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyMzkwMjJ9.invalid_signature"
        resp = client.post(REFRESH_URL, params={"refresh_token": expired_token})
        assert resp.status_code == 400
