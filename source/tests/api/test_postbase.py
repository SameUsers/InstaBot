import pytest
from sqlalchemy import create_engine, delete, select
from fastapi.testclient import TestClient

from main import app
from source.conf import settings
from source.models.user import User
from source.models.post_context import PostBase

REGISTER_URL = "/v1/auth/registration"
LOGIN_URL = "/v1/auth/login"
POSTBASE_URL = "/v1/postbase"
DB_URL = settings.db_url_sync


@pytest.fixture(autouse=True)
def cleanup_user_and_postbase():
    email = "postbaseuser@example.com"
    engine = create_engine(DB_URL)
    with engine.begin() as conn:
        user_ids = [row[0] for row in conn.execute(select(User.user_id).where(User.email == email))]
        for uid in user_ids:
            conn.execute(delete(PostBase).where(PostBase.user_id == uid))
        conn.execute(delete(User).where(User.email == email))
    yield
    with engine.begin() as conn:
        user_ids = [row[0] for row in conn.execute(select(User.user_id).where(User.email == email))]
        for uid in user_ids:
            conn.execute(delete(PostBase).where(PostBase.user_id == uid))
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


def test_create_postbase():
    with TestClient(app) as client:
        email = "postbaseuser@example.com"
        username = "postbaseuser"
        password = "Passw0rd!pb"
        login_json = create_and_login(client, email, username, password)
        headers = {"Authorization": f"Bearer {login_json['access_token']}"}

        ctx_data = {"content": "initial postbase context"}
        resp = client.post(POSTBASE_URL, json=ctx_data, headers=headers)
        assert resp.status_code == 201
        assert "saved successfully" in resp.json().get("message", "").lower()


def test_create_postbase_duplicate():
    with TestClient(app) as client:
        email = "postbaseuser@example.com"
        username = "postbaseuser"
        password = "Passw0rd!pb"
        login_json = create_and_login(client, email, username, password)
        headers = {"Authorization": f"Bearer {login_json['access_token']}"}

        ctx_data = {"content": "duplicate context"}
        resp_create1 = client.post(POSTBASE_URL, json=ctx_data, headers=headers)
        assert resp_create1.status_code == 201

        resp_create2 = client.post(POSTBASE_URL, json=ctx_data, headers=headers)
        assert resp_create2.status_code == 400
        assert "already exists" in resp_create2.json()["detail"].lower()


def test_create_postbase_without_auth():
    with TestClient(app) as client:
        ctx_data = {"content": "unauthorized context"}
        resp = client.post(POSTBASE_URL, json=ctx_data)
        assert resp.status_code == 401


def test_create_postbase_empty_content():
    with TestClient(app) as client:
        email = "postbaseuser@example.com"
        username = "postbaseuser"
        password = "Passw0rd!pb"
        login_json = create_and_login(client, email, username, password)
        headers = {"Authorization": f"Bearer {login_json['access_token']}"}

        ctx_data = {"content": ""}
        resp = client.post(POSTBASE_URL, json=ctx_data, headers=headers)
        assert resp.status_code == 422


def test_get_postbase():
    with TestClient(app) as client:
        email = "postbaseuser@example.com"
        username = "postbaseuser"
        password = "Passw0rd!pb"
        login_json = create_and_login(client, email, username, password)
        headers = {"Authorization": f"Bearer {login_json['access_token']}"}

        resp_get_missing = client.get(POSTBASE_URL, headers=headers)
        assert resp_get_missing.status_code == 404

        ctx_data = {"content": "test postbase context"}
        resp_create = client.post(POSTBASE_URL, json=ctx_data, headers=headers)
        assert resp_create.status_code == 201

        resp_get = client.get(POSTBASE_URL, headers=headers)
        assert resp_get.status_code == 200
        assert resp_get.json()["content"] == "test postbase context"


def test_get_postbase_without_auth():
    with TestClient(app) as client:
        resp = client.get(POSTBASE_URL)
        assert resp.status_code == 401


def test_update_postbase():
    with TestClient(app) as client:
        email = "postbaseuser@example.com"
        username = "postbaseuser"
        password = "Passw0rd!pb"
        login_json = create_and_login(client, email, username, password)
        headers = {"Authorization": f"Bearer {login_json['access_token']}"}

        ctx_initial = {"content": "initial context"}
        resp_create = client.post(POSTBASE_URL, json=ctx_initial, headers=headers)
        assert resp_create.status_code == 201

        ctx_updated = {"content": "updated context"}
        resp_update = client.put(POSTBASE_URL, json=ctx_updated, headers=headers)
        assert resp_update.status_code == 200
        assert "updated successfully" in resp_update.json().get("message", "").lower()

        resp_get = client.get(POSTBASE_URL, headers=headers)
        assert resp_get.status_code == 200
        assert resp_get.json()["content"] == "updated context"


def test_update_postbase_not_found():
    with TestClient(app) as client:
        email = "postbaseuser@example.com"
        username = "postbaseuser"
        password = "Passw0rd!pb"
        login_json = create_and_login(client, email, username, password)
        headers = {"Authorization": f"Bearer {login_json['access_token']}"}

        ctx_data = {"content": "not found update"}
        resp = client.put(POSTBASE_URL, json=ctx_data, headers=headers)
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


def test_update_postbase_without_auth():
    with TestClient(app) as client:
        ctx_data = {"content": "unauthorized update"}
        resp = client.put(POSTBASE_URL, json=ctx_data)
        assert resp.status_code == 401


def test_delete_postbase():
    with TestClient(app) as client:
        email = "postbaseuser@example.com"
        username = "postbaseuser"
        password = "Passw0rd!pb"
        login_json = create_and_login(client, email, username, password)
        headers = {"Authorization": f"Bearer {login_json['access_token']}"}

        ctx_data = {"content": "context to delete"}
        resp_create = client.post(POSTBASE_URL, json=ctx_data, headers=headers)
        assert resp_create.status_code == 201

        resp_delete = client.delete(POSTBASE_URL, headers=headers)
        assert resp_delete.status_code == 204

        resp_get = client.get(POSTBASE_URL, headers=headers)
        assert resp_get.status_code == 404


def test_delete_postbase_not_found():
    with TestClient(app) as client:
        email = "postbaseuser@example.com"
        username = "postbaseuser"
        password = "Passw0rd!pb"
        login_json = create_and_login(client, email, username, password)
        headers = {"Authorization": f"Bearer {login_json['access_token']}"}

        resp = client.delete(POSTBASE_URL, headers=headers)
        assert resp.status_code == 404


def test_delete_postbase_without_auth():
    with TestClient(app) as client:
        resp = client.delete(POSTBASE_URL)
        assert resp.status_code == 401


def test_postbase_full_flow():
    with TestClient(app) as client:
        email = "postbaseuser@example.com"
        username = "postbaseuser"
        password = "Passw0rd!pb"
        login_json = create_and_login(client, email, username, password)
        headers = {"Authorization": f"Bearer {login_json['access_token']}"}

        resp_get_initial = client.get(POSTBASE_URL, headers=headers)
        assert resp_get_initial.status_code == 404

        ctx_create = {"content": "full flow context"}
        resp_create = client.post(POSTBASE_URL, json=ctx_create, headers=headers)
        assert resp_create.status_code == 201

        resp_get_created = client.get(POSTBASE_URL, headers=headers)
        assert resp_get_created.status_code == 200
        assert resp_get_created.json()["content"] == "full flow context"

        ctx_update = {"content": "updated full flow context"}
        resp_update = client.put(POSTBASE_URL, json=ctx_update, headers=headers)
        assert resp_update.status_code == 200

        resp_get_updated = client.get(POSTBASE_URL, headers=headers)
        assert resp_get_updated.status_code == 200
        assert resp_get_updated.json()["content"] == "updated full flow context"

        resp_delete = client.delete(POSTBASE_URL, headers=headers)
        assert resp_delete.status_code == 204

        resp_get_deleted = client.get(POSTBASE_URL, headers=headers)
        assert resp_get_deleted.status_code == 404

