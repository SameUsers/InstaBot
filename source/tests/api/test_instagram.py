import pytest
from sqlalchemy import create_engine, delete, select
from fastapi.testclient import TestClient

from main import app
from source.conf import settings
from source.models.user import User
from source.models.instagram import InstagramCredentials
from source.models.user import User


REGISTER_URL = "/v1/auth/registration"
LOGIN_URL = "/v1/auth/login"
INSTAGRAM_URL = "/v1/botservice/register"
INSTAGRAM_CREDS_URL = "/v1/botservice/creds"
DB_URL = settings.db_url_sync


@pytest.fixture(autouse=True)
def cleanup_user_and_instagram():
    email = "iguser@example.com"
    inst_ids = [9445551, 111, 222]
    engine = create_engine(DB_URL)
    with engine.begin() as conn:
        for inst_id in inst_ids:
            conn.execute(delete(InstagramCredentials).where(InstagramCredentials.instagram_id == inst_id))
        conn.execute(delete(User).where(User.email == email))
    yield
    with engine.begin() as conn:
        for inst_id in inst_ids:
            conn.execute(delete(InstagramCredentials).where(InstagramCredentials.instagram_id == inst_id))
        conn.execute(delete(User).where(User.email == email))
    engine.dispose()

@pytest.fixture(autouse=True)
def cleanup_extra_instagram_users():
    engine = create_engine(DB_URL)
    with engine.begin() as conn:
        emails = ["igbadpayload@example.com"]
        conn.execute(delete(User).where(User.email.in_(emails)))
    yield
    with engine.begin() as conn:
        emails = ["igbadpayload@example.com"]
        conn.execute(delete(User).where(User.email.in_(emails)))
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


def test_instagram_creds_register():
    with TestClient(app) as client:
        email = "iguser@example.com"
        username = "iguser"
        password = "Passw0rd!ig"
        login_json = create_and_login(client, email, username, password)
        access_token = login_json["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        inst_id = 9445551
        inst_token = "IGQVJ1234567890XabcdefBLAblablaBIKE"
        data = {"instagram_id": inst_id, "instagram_token": inst_token}
        resp = client.post(INSTAGRAM_URL, json=data, headers=headers)
        assert resp.status_code in (200, 201)
        assert "saved successfully" in resp.json().get("message", "")

        resp2 = client.post(INSTAGRAM_URL, json=data, headers=headers)
        assert resp2.status_code == 400


def test_instagram_creds_get_update_delete_flow():
    with TestClient(app) as client:
        email = "iguser@example.com"
        username = "iguser"
        password = "Passw0rd!ig"
        login_json = create_and_login(client, email, username, password)
        headers = {"Authorization": f"Bearer {login_json['access_token']}"}

        resp_get_missing = client.get(INSTAGRAM_CREDS_URL, headers=headers)
        assert resp_get_missing.status_code == 404

        data = {"instagram_id": 111, "instagram_token": "IGQVJtokentoken_token_token"}
        resp_create = client.post(INSTAGRAM_URL, json=data, headers=headers)
        assert resp_create.status_code in (200, 201)

        resp_get = client.get(INSTAGRAM_CREDS_URL, headers=headers)
        assert resp_get.status_code == 200
        body = resp_get.json()
        assert body["instagram_id"] == 111

        upd = {"instagram_id": 222, "instagram_token": "IGQVJupdated_updated_token_token"}
        resp_upd = client.put(INSTAGRAM_CREDS_URL, json=upd, headers=headers)
        assert resp_upd.status_code == 200

        resp_get2 = client.get(INSTAGRAM_CREDS_URL, headers=headers)
        assert resp_get2.status_code == 200
        body2 = resp_get2.json()
        assert body2["instagram_id"] == 222

        resp_del = client.delete(INSTAGRAM_CREDS_URL, headers=headers)
        assert resp_del.status_code == 204

        resp_get_missing2 = client.get(INSTAGRAM_CREDS_URL, headers=headers)
        assert resp_get_missing2.status_code == 404


def test_instagram_register_without_auth():
    with TestClient(app) as client:
        data = {"instagram_id": 1234567, "instagram_token": "IGQVJinvalidTOKENxxxx"}
        resp = client.post(INSTAGRAM_URL, json=data)
        assert resp.status_code == 401


def test_instagram_register_invalid_payload():
    with TestClient(app) as client:
        email = "igbadpayload@example.com"
        username = "igbad"
        password = "Passw0rd!ig"
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
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        bad_data = {"instagram_id": 1234567, "instagram_token": "short"}
        resp = client.post(INSTAGRAM_URL, json=bad_data, headers=headers)
        assert resp.status_code == 422

        
