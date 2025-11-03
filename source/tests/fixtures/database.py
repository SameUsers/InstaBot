import pytest
from sqlalchemy import create_engine, delete, select
from uuid import uuid4

from source.conf import settings
from source.models.user import User
from source.models.instagram import InstagramCredentials
from source.models.post import Post
from source.models.post_context import PostBase
from source.models.wiki_context import Wikibase


DB_URL = settings.db_url_sync


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(DB_URL)
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def cleanup_test_data():
    test_emails = [
        "integration_test@example.com",
        "test_db_user@example.com",
    ]
    
    engine = create_engine(DB_URL)
    with engine.begin() as conn:
        for email in test_emails:
            result = conn.execute(select(User.user_id).where(User.email == email))
            for row in result:
                user_id = row[0]
                conn.execute(delete(Post).where(Post.user_id == user_id))
                conn.execute(delete(InstagramCredentials).where(InstagramCredentials.user_id == user_id))
                conn.execute(delete(PostBase).where(PostBase.user_id == user_id))
                conn.execute(delete(Wikibase).where(Wikibase.user_id == user_id))
                conn.execute(delete(User).where(User.user_id == user_id))
    
    yield
    
    with engine.begin() as conn:
        for email in test_emails:
            result = conn.execute(select(User.user_id).where(User.email == email))
            for row in result:
                user_id = row[0]
                conn.execute(delete(Post).where(Post.user_id == user_id))
                conn.execute(delete(InstagramCredentials).where(InstagramCredentials.user_id == user_id))
                conn.execute(delete(PostBase).where(PostBase.user_id == user_id))
                conn.execute(delete(Wikibase).where(Wikibase.user_id == user_id))
                conn.execute(delete(User).where(User.user_id == user_id))
    
    engine.dispose()


@pytest.fixture
def sample_user_data():
    return {
        "email": "integration_test@example.com",
        "username": "integration_test_user",
        "password": "TestPassword123!@#"
    }


@pytest.fixture
def sample_instagram_credentials():
    return {
        "instagram_id": 1234567890,
        "instagram_token": "test_access_token_valid_12345"
    }

