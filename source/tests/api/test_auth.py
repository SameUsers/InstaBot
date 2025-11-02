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
