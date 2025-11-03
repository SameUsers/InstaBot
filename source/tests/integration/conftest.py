import pytest
from sqlalchemy import create_engine, delete, select

from source.conf import settings
from source.models.user import User
from source.models.instagram import InstagramCredentials
from source.models.post import Post
from source.models.post_context import PostBase
from source.models.wiki_context import Wikibase

DB_URL = settings.db_url_sync


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


from source.tests.fixtures.database import db_session, sample_user_data, sample_instagram_credentials
from source.tests.fixtures.sample_data import (
    WEBHOOK_MESSAGING_PAYLOAD,
    WEBHOOK_CHANGES_PAYLOAD,
    WEBHOOK_VERIFICATION_REQUEST,
    SAMPLE_BASE64_IMAGE,
    SAMPLE_POST_DATA,
    SAMPLE_CONTEXT_CONTENT
)

__all__ = [
    "cleanup_test_data",
    "db_session",
    "sample_user_data",
    "sample_instagram_credentials",
    "WEBHOOK_MESSAGING_PAYLOAD",
    "WEBHOOK_CHANGES_PAYLOAD",
    "WEBHOOK_VERIFICATION_REQUEST",
    "SAMPLE_BASE64_IMAGE",
    "SAMPLE_POST_DATA",
    "SAMPLE_CONTEXT_CONTENT",
]

