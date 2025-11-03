import pytest
from sqlalchemy import create_engine, delete, select
from fastapi.testclient import TestClient
from uuid import UUID

from main import app
from source.conf import settings
from source.models.user import User
from source.models.post import Post

REGISTER_URL = "/v1/auth/registration"
LOGIN_URL = "/v1/auth/login"
POSTS_URL = "/v1/posts"
DB_URL = settings.db_url_sync


@pytest.fixture(autouse=True)
def cleanup_user_and_posts():
    email = "postuser@example.com"
    engine = create_engine(DB_URL)
    with engine.begin() as conn:
        user_ids = [row[0] for row in conn.execute(select(User.user_id).where(User.email == email))]
        for uid in user_ids:
            conn.execute(delete(Post).where(Post.user_id == uid))
        conn.execute(delete(User).where(User.email == email))
    yield
    with engine.begin() as conn:
        user_ids = [row[0] for row in conn.execute(select(User.user_id).where(User.email == email))]
        for uid in user_ids:
            conn.execute(delete(Post).where(Post.user_id == uid))
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


def test_create_post_record():
    with TestClient(app) as client:
        email = "postuser@example.com"
        username = "postuser"
        password = "Passw0rd!post"
        login_json = create_and_login(client, email, username, password)
        headers = {"Authorization": f"Bearer {login_json['access_token']}"}

        post_data = {
            "instagram_creation_id": "178414123456789",
            "caption": "Test post caption",
            "image_url": "https://example.com/image.jpg"
        }
        resp = client.post(POSTS_URL, json=post_data, headers=headers)
        assert resp.status_code == 201
        body = resp.json()
        assert body["caption"] == "Test post caption"
        assert body["image_url"] == "https://example.com/image.jpg"
        assert body["instagram_creation_id"] == "178414123456789"
        assert body["post_id"] is not None
        assert body["published_at"] is None
        assert body["time_to_publish"] is None


def test_create_post_without_auth():
    with TestClient(app) as client:
        post_data = {
            "instagram_creation_id": "178414123456789",
            "caption": "Test post",
            "image_url": "https://example.com/image.jpg"
        }
        resp = client.post(POSTS_URL, json=post_data)
        assert resp.status_code == 401


def test_list_posts():
    with TestClient(app) as client:
        email = "postuser@example.com"
        username = "postuser"
        password = "Passw0rd!post"
        login_json = create_and_login(client, email, username, password)
        headers = {"Authorization": f"Bearer {login_json['access_token']}"}

        resp_list_empty = client.get(POSTS_URL, headers=headers)
        assert resp_list_empty.status_code == 200
        assert resp_list_empty.json()["items"] == []

        post_data = {
            "instagram_creation_id": "178414111111",
            "caption": "First post",
            "image_url": "https://example.com/1.jpg"
        }
        resp_create1 = client.post(POSTS_URL, json=post_data, headers=headers)
        assert resp_create1.status_code == 201

        post_data2 = {
            "instagram_creation_id": "178414222222",
            "caption": "Second post",
            "image_url": "https://example.com/2.jpg"
        }
        resp_create2 = client.post(POSTS_URL, json=post_data2, headers=headers)
        assert resp_create2.status_code == 201

        resp_list = client.get(POSTS_URL, headers=headers)
        assert resp_list.status_code == 200
        items = resp_list.json()["items"]
        assert len(items) == 2
        captions = {item["caption"] for item in items}
        assert "First post" in captions
        assert "Second post" in captions


def test_list_posts_without_auth():
    with TestClient(app) as client:
        resp = client.get(POSTS_URL)
        assert resp.status_code == 401


def test_get_post_by_id():
    with TestClient(app) as client:
        email = "postuser@example.com"
        username = "postuser"
        password = "Passw0rd!post"
        login_json = create_and_login(client, email, username, password)
        headers = {"Authorization": f"Bearer {login_json['access_token']}"}

        post_data = {
            "instagram_creation_id": "178414333333",
            "caption": "Single post",
            "image_url": "https://example.com/3.jpg"
        }
        resp_create = client.post(POSTS_URL, json=post_data, headers=headers)
        assert resp_create.status_code == 201
        post_id = resp_create.json()["post_id"]

        resp_get = client.get(f"{POSTS_URL}/{post_id}", headers=headers)
        assert resp_get.status_code == 200
        body = resp_get.json()
        assert body["post_id"] == post_id
        assert body["caption"] == "Single post"
        assert body["instagram_creation_id"] == "178414333333"


def test_get_post_by_id_not_found():
    with TestClient(app) as client:
        email = "postuser@example.com"
        username = "postuser"
        password = "Passw0rd!post"
        login_json = create_and_login(client, email, username, password)
        headers = {"Authorization": f"Bearer {login_json['access_token']}"}

        fake_uuid = "12345678-1234-5678-1234-567812345678"
        resp = client.get(f"{POSTS_URL}/{fake_uuid}", headers=headers)
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


def test_get_post_without_auth():
    with TestClient(app) as client:
        fake_uuid = "12345678-1234-5678-1234-567812345678"
        resp = client.get(f"{POSTS_URL}/{fake_uuid}")
        assert resp.status_code == 401


def test_delete_post():
    with TestClient(app) as client:
        email = "postuser@example.com"
        username = "postuser"
        password = "Passw0rd!post"
        login_json = create_and_login(client, email, username, password)
        headers = {"Authorization": f"Bearer {login_json['access_token']}"}

        post_data = {
            "instagram_creation_id": "178414444444",
            "caption": "Post to delete",
            "image_url": "https://example.com/4.jpg"
        }
        resp_create = client.post(POSTS_URL, json=post_data, headers=headers)
        assert resp_create.status_code == 201
        post_id = resp_create.json()["post_id"]

        resp_delete = client.delete(f"{POSTS_URL}/{post_id}", headers=headers)
        assert resp_delete.status_code == 204

        resp_get = client.get(f"{POSTS_URL}/{post_id}", headers=headers)
        assert resp_get.status_code == 404


def test_delete_post_not_found():
    with TestClient(app) as client:
        email = "postuser@example.com"
        username = "postuser"
        password = "Passw0rd!post"
        login_json = create_and_login(client, email, username, password)
        headers = {"Authorization": f"Bearer {login_json['access_token']}"}

        fake_uuid = "12345678-1234-5678-1234-567812345678"
        resp = client.delete(f"{POSTS_URL}/{fake_uuid}", headers=headers)
        assert resp.status_code == 404


def test_delete_post_without_auth():
    with TestClient(app) as client:
        fake_uuid = "12345678-1234-5678-1234-567812345678"
        resp = client.delete(f"{POSTS_URL}/{fake_uuid}")
        assert resp.status_code == 401


def test_set_publish_time():
    with TestClient(app) as client:
        email = "postuser@example.com"
        username = "postuser"
        password = "Passw0rd!post"
        login_json = create_and_login(client, email, username, password)
        headers = {"Authorization": f"Bearer {login_json['access_token']}"}

        post_data = {
            "instagram_creation_id": "178414555555",
            "caption": "Scheduled post",
            "image_url": "https://example.com/5.jpg"
        }
        resp_create = client.post(POSTS_URL, json=post_data, headers=headers)
        assert resp_create.status_code == 201
        post_id = resp_create.json()["post_id"]

        time_data = {
            "post_id": post_id,
            "time_to_publish": "2025-12-31T12:00:00"
        }
        resp_set = client.put(f"{POSTS_URL}/set-publish-time", json=time_data, headers=headers)
        assert resp_set.status_code == 200
        body = resp_set.json()
        assert body["time_to_publish"] == "2025-12-31T12:00:00"


def test_set_publish_time_not_found():
    with TestClient(app) as client:
        email = "postuser@example.com"
        username = "postuser"
        password = "Passw0rd!post"
        login_json = create_and_login(client, email, username, password)
        headers = {"Authorization": f"Bearer {login_json['access_token']}"}

        fake_uuid = "12345678-1234-5678-1234-567812345678"
        time_data = {
            "post_id": fake_uuid,
            "time_to_publish": "2025-12-31T12:00:00"
        }
        resp = client.put(f"{POSTS_URL}/set-publish-time", json=time_data, headers=headers)
        assert resp.status_code == 404


def test_set_publish_time_without_auth():
    with TestClient(app) as client:
        fake_uuid = "12345678-1234-5678-1234-567812345678"
        time_data = {
            "post_id": fake_uuid,
            "time_to_publish": "2025-12-31T12:00:00"
        }
        resp = client.put(f"{POSTS_URL}/set-publish-time", json=time_data)
        assert resp.status_code == 401


def test_mark_published():
    with TestClient(app) as client:
        email = "postuser@example.com"
        username = "postuser"
        password = "Passw0rd!post"
        login_json = create_and_login(client, email, username, password)
        headers = {"Authorization": f"Bearer {login_json['access_token']}"}

        post_data = {
            "instagram_creation_id": "178414666666",
            "caption": "Publish post",
            "image_url": "https://example.com/6.jpg"
        }
        resp_create = client.post(POSTS_URL, json=post_data, headers=headers)
        assert resp_create.status_code == 201
        creation_id = resp_create.json()["instagram_creation_id"]

        publish_data = {"creation_id": creation_id}
        resp_publish = client.put(f"{POSTS_URL}/publish", json=publish_data, headers=headers)
        assert resp_publish.status_code == 204


def test_mark_published_not_found():
    with TestClient(app) as client:
        email = "postuser@example.com"
        username = "postuser"
        password = "Passw0rd!post"
        login_json = create_and_login(client, email, username, password)
        headers = {"Authorization": f"Bearer {login_json['access_token']}"}

        publish_data = {"creation_id": "nonexistent_creation_id"}
        resp = client.put(f"{POSTS_URL}/publish", json=publish_data, headers=headers)
        assert resp.status_code == 404


def test_mark_published_without_auth():
    with TestClient(app) as client:
        publish_data = {"creation_id": "some_creation_id"}
        resp = client.put(f"{POSTS_URL}/publish", json=publish_data)
        assert resp.status_code == 401


def test_create_post_empty_fields():
    with TestClient(app) as client:
        email = "postuser@example.com"
        username = "postuser"
        password = "Passw0rd!post"
        login_json = create_and_login(client, email, username, password)
        headers = {"Authorization": f"Bearer {login_json['access_token']}"}

        resp = client.post(POSTS_URL, json={}, headers=headers)
        assert resp.status_code == 422


def test_create_post_missing_fields():
    with TestClient(app) as client:
        email = "postuser@example.com"
        username = "postuser"
        password = "Passw0rd!post"
        login_json = create_and_login(client, email, username, password)
        headers = {"Authorization": f"Bearer {login_json['access_token']}"}

        resp = client.post(POSTS_URL, json={"caption": "only caption"}, headers=headers)
        assert resp.status_code == 422


def test_set_publish_time_invalid_uuid():
    with TestClient(app) as client:
        email = "postuser@example.com"
        username = "postuser"
        password = "Passw0rd!post"
        login_json = create_and_login(client, email, username, password)
        headers = {"Authorization": f"Bearer {login_json['access_token']}"}

        time_data = {
            "post_id": "not-a-uuid",
            "time_to_publish": "2025-12-31T12:00:00"
        }
        resp = client.put(f"{POSTS_URL}/set-publish-time", json=time_data, headers=headers)
        assert resp.status_code == 422


def test_set_publish_time_invalid_datetime():
    with TestClient(app) as client:
        email = "postuser@example.com"
        username = "postuser"
        password = "Passw0rd!post"
        login_json = create_and_login(client, email, username, password)
        headers = {"Authorization": f"Bearer {login_json['access_token']}"}

        post_data = {
            "instagram_creation_id": "178414999999",
            "caption": "Test",
            "image_url": "https://example.com/img.jpg"
        }
        resp_create = client.post(POSTS_URL, json=post_data, headers=headers)
        post_id = resp_create.json()["post_id"]

        time_data = {
            "post_id": post_id,
            "time_to_publish": "not-a-date"
        }
        resp = client.put(f"{POSTS_URL}/set-publish-time", json=time_data, headers=headers)
        assert resp.status_code == 422

