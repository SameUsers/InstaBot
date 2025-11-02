import pytest
from sqlalchemy import create_engine, delete, select
from fastapi.testclient import TestClient

from main import app
from source.conf import settings
from source.models.user import User
from source.models.wiki_context import Wikibase


REGISTER_URL = "/v1/auth/registration"
LOGIN_URL = "/v1/auth/login"
WIKIBASE_URL = "/v1/wikibase"
DB_URL = settings.db_url_sync


@pytest.fixture(autouse=True)
def cleanup_users_and_wikibase():
    email = "wikibaseuser@example.com"
    engine = create_engine(DB_URL)
    with engine.begin() as conn:
        user_ids = [row[0] for row in conn.execute(select(User.user_id).where(User.email == email))]
        for uid in user_ids:
            conn.execute(delete(Wikibase).where(Wikibase.user_id == uid))
        conn.execute(delete(User).where(User.email == email))
    yield
    with engine.begin() as conn:
        user_ids = [row[0] for row in conn.execute(select(User.user_id).where(User.email == email))]
        for uid in user_ids:
            conn.execute(delete(Wikibase).where(Wikibase.user_id == uid))
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


def test_wikibase_full_flow_create_get_update_delete():
    with TestClient(app) as client:
        email = "wikibaseuser@example.com"
        username = "wbuser"
        password = "Passw0rd!wb"
        login_json = create_and_login(client, email, username, password)
        headers = {"Authorization": f"Bearer {login_json['access_token']}"}

        resp_get_missing = client.get(WIKIBASE_URL, headers=headers)
        assert resp_get_missing.status_code == 404

        create_ctx = {"content": "initial user context"}
        resp_create = client.post(WIKIBASE_URL, json=create_ctx, headers=headers)
        assert resp_create.status_code in (200, 201)

        resp_create_dup = client.post(WIKIBASE_URL, json=create_ctx, headers=headers)
        assert resp_create_dup.status_code == 400

        resp_get = client.get(WIKIBASE_URL, headers=headers)
        assert resp_get.status_code == 200
        assert resp_get.json()["content"] == "initial user context"

        upd_ctx = {"content": "updated user context"}
        resp_upd = client.put(WIKIBASE_URL, json=upd_ctx, headers=headers)
        assert resp_upd.status_code == 200

        resp_get2 = client.get(WIKIBASE_URL, headers=headers)
        assert resp_get2.status_code == 200
        assert resp_get2.json()["content"] == "updated user context"

        resp_del = client.delete(WIKIBASE_URL, headers=headers)
        assert resp_del.status_code == 204

        resp_get_missing2 = client.get(WIKIBASE_URL, headers=headers)
        assert resp_get_missing2.status_code == 404


