import pytest
from sqlalchemy import create_engine, delete
from fastapi.testclient import TestClient

from main import app
from source.conf import settings
from source.models.user import User


REGISTER_URL = "/v1/auth/registration"
LOGIN_URL = "/v1/auth/login"
ME_URL = "/v1/user/me"
DB_URL = settings.db_url_sync


@pytest.fixture(autouse=True)
def cleanup_user():
    emails = ["user2@example.com"]
    engine = create_engine(DB_URL)
    with engine.begin() as conn:
        for email in emails:
            conn.execute(delete(User).where(User.email == email))
    yield
    with engine.begin() as conn:
        for email in emails:
            conn.execute(delete(User).where(User.email == email))
    engine.dispose()


def create_and_login(client, email, username, password):
    reg = client.post(REGISTER_URL, json={
        "email": email,
        "username": username,
        "password": password,
    })
    assert reg.status_code == 200
    login = client.post(LOGIN_URL, json={
        "email": email,
        "password": password,
    })
    assert login.status_code == 200
    return login.json()


def test_user_me():
    with TestClient(app) as client:
        email = "user2@example.com"
        username = "user2"
        password = "Passw0rd123"
        login_json = create_and_login(client, email, username, password)
        access_token = login_json["access_token"]
        resp = client.get(ME_URL, headers={"Authorization": f"Bearer {access_token}"})
        assert resp.status_code == 200
        me = resp.json()
        assert me["email"] == email
        assert me["username"] == username
        assert me["permissions"] == "default"


def test_user_me_without_token():
    with TestClient(app) as client:
        resp = client.get(ME_URL)
        assert resp.status_code == 401


def test_user_me_with_invalid_token():
    with TestClient(app) as client:
        resp = client.get(ME_URL, headers={"Authorization": "Bearer not-a-jwt"})
        assert resp.status_code == 401

