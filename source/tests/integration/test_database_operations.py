import pytest
from datetime import datetime
from uuid import UUID

from source.auth.password import hash_password
from source.repositories.user import user_repository
from source.repositories.instagram import instagram_repository
from source.repositories.post import post_repository
from source.repositories.post_context import post_context_repository
from source.repositories.wiki_context import wiki_context_repository
from source.schemas.auth import RegistrationSchema
from source.schemas.instagram import CreateInstagramCredentials
from source.core.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
    InstagramCredsAlreadyExistsError,
    InstagramCredsNotFoundError,
    PostNotFoundError,
    PostBaseContextNotFoundError,
    WikibaseContextNotFoundError
)

SAMPLE_POST_DATA = {
    "instagram_creation_id": "test_creation_id_123",
    "caption": "Test post caption",
    "image_url": "http://localhost:9000/images/test_image.jpg"
}

SAMPLE_CONTEXT_CONTENT = "This is a sample context for testing purposes. It contains enough content to validate the system."


@pytest.mark.integration
class TestUserRepository:
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, sample_user_data):
        data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(data.password)
        
        user = await user_repository.create_user(data, hashed)
        
        assert user.email == data.email
        assert user.username == data.username
        assert isinstance(user.user_id, str)
        assert user.refresh_token_version == 0
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, sample_user_data):
        data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(data.password)
        
        await user_repository.create_user(data, hashed)
        
        with pytest.raises(UserAlreadyExistsError):
            await user_repository.create_user(data, hashed)
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, sample_user_data):
        data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(data.password)
        
        created_user = await user_repository.create_user(data, hashed)
        user = await user_repository.get_user_by_email(data.email)
        
        assert user.email == created_user.email
        assert user.user_id == created_user.user_id
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self):
        with pytest.raises(UserNotFoundError):
            await user_repository.get_user_by_email("nonexistent@example.com")
    
    @pytest.mark.asyncio
    async def test_check_user_exists_true(self, sample_user_data):
        data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(data.password)
        
        await user_repository.create_user(data, hashed)
        
        assert await user_repository.check_user_exists(data.email) is True
    
    @pytest.mark.asyncio
    async def test_check_user_exists_false(self):
        assert await user_repository.check_user_exists("nonexistent@example.com") is False
    
    @pytest.mark.asyncio
    async def test_increment_token_version(self, sample_user_data):
        data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(data.password)
        
        user = await user_repository.create_user(data, hashed)
        user_id = UUID(user.user_id)
        
        version_before = await user_repository.get_refresh_version(user_id)
        await user_repository.increment_token_version(user_id)
        version_after = await user_repository.get_refresh_version(user_id)
        
        assert version_after == version_before + 1


@pytest.mark.integration
class TestInstagramRepository:
    
    @pytest.mark.asyncio
    async def test_create_instagram_credentials_success(self, sample_user_data, sample_instagram_credentials):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = UUID(user.user_id)
        
        insta_data = CreateInstagramCredentials(**sample_instagram_credentials)
        await instagram_repository.create_instagram_credentials(insta_data, user_id)
        
        credentials = await instagram_repository.get_instagram_credentials(user_id)
        assert credentials is not None
        assert credentials.instagram_id == insta_data.instagram_id
        assert credentials.instagram_token == insta_data.instagram_token
    
    @pytest.mark.asyncio
    async def test_create_instagram_credentials_duplicate(self, sample_user_data, sample_instagram_credentials):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = UUID(user.user_id)
        
        insta_data = CreateInstagramCredentials(**sample_instagram_credentials)
        await instagram_repository.create_instagram_credentials(insta_data, user_id)
        
        with pytest.raises(InstagramCredsAlreadyExistsError):
            await instagram_repository.create_instagram_credentials(insta_data, user_id)
    
    @pytest.mark.asyncio
    async def test_update_instagram_credentials_success(self, sample_user_data, sample_instagram_credentials):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = UUID(user.user_id)
        
        insta_data = CreateInstagramCredentials(**sample_instagram_credentials)
        await instagram_repository.create_instagram_credentials(insta_data, user_id)
        
        updated_data = CreateInstagramCredentials(
            instagram_id=999888777,
            instagram_token="updated_token_987654321"
        )
        await instagram_repository.update_instagram_credentials(user_id, updated_data)
        
        credentials = await instagram_repository.get_instagram_credentials(user_id)
        assert credentials.instagram_id == updated_data.instagram_id
        assert credentials.instagram_token == updated_data.instagram_token
    
    @pytest.mark.asyncio
    async def test_update_instagram_credentials_not_found(self, sample_user_data):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = UUID(user.user_id)
        
        insta_data = CreateInstagramCredentials(
            instagram_id=12345,
            instagram_token="some_token_12345"
        )
        
        with pytest.raises(InstagramCredsNotFoundError):
            await instagram_repository.update_instagram_credentials(user_id, insta_data)
    
    @pytest.mark.asyncio
    async def test_delete_instagram_credentials_success(self, sample_user_data, sample_instagram_credentials):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = UUID(user.user_id)
        
        insta_data = CreateInstagramCredentials(**sample_instagram_credentials)
        await instagram_repository.create_instagram_credentials(insta_data, user_id)
        await instagram_repository.delete_instagram_credentials(user_id)
        
        credentials = await instagram_repository.get_instagram_credentials(user_id)
        assert credentials is None
    
    @pytest.mark.asyncio
    async def test_get_user_id_by_instagram_id(self, sample_user_data, sample_instagram_credentials):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = UUID(user.user_id)
        
        insta_data = CreateInstagramCredentials(**sample_instagram_credentials)
        await instagram_repository.create_instagram_credentials(insta_data, user_id)
        
        resolved_user_id = await instagram_repository.get_user_id_by_instagram_id(insta_data.instagram_id)
        assert resolved_user_id == user_id


@pytest.mark.integration
class TestPostRepository:
    
    @pytest.mark.asyncio
    async def test_create_post_success(self, sample_user_data):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = UUID(user.user_id)
        
        post = await post_repository.create_post(
            user_id=user_id,
            instagram_creation_id=SAMPLE_POST_DATA["instagram_creation_id"],
            caption=SAMPLE_POST_DATA["caption"],
            image_url=SAMPLE_POST_DATA["image_url"]
        )
        
        assert post.user_id == user_id
        assert post.instagram_creation_id == SAMPLE_POST_DATA["instagram_creation_id"]
        assert post.caption == SAMPLE_POST_DATA["caption"]
        assert post.image_url == SAMPLE_POST_DATA["image_url"]
        assert post.post_id is not None
    
    @pytest.mark.asyncio
    async def test_get_post_by_id_success(self, sample_user_data):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = UUID(user.user_id)
        
        created_post = await post_repository.create_post(
            user_id=user_id,
            instagram_creation_id="test_id",
            caption="Test caption",
            image_url="http://test.com/image.jpg"
        )
        
        post = await post_repository.get_post(user_id=user_id, post_id=created_post.post_id)
        assert post.post_id == created_post.post_id
        assert post.caption == created_post.caption
    
    @pytest.mark.asyncio
    async def test_get_post_by_id_not_found(self, sample_user_data):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = UUID(user.user_id)
        
        fake_post_id = UUID("12345678-1234-1234-1234-123456789abc")
        
        with pytest.raises(PostNotFoundError):
            await post_repository.get_post(user_id=user_id, post_id=fake_post_id)
    
    @pytest.mark.asyncio
    async def test_list_posts(self, sample_user_data):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = UUID(user.user_id)
        
        post1 = await post_repository.create_post(
            user_id=user_id,
            instagram_creation_id="test_id_1",
            caption="Caption 1",
            image_url="http://test.com/image1.jpg"
        )
        post2 = await post_repository.create_post(
            user_id=user_id,
            instagram_creation_id="test_id_2",
            caption="Caption 2",
            image_url="http://test.com/image2.jpg"
        )
        
        posts = await post_repository.list_posts(user_id=user_id)
        assert len(posts) >= 2
        post_ids = [p.post_id for p in posts]
        assert post1.post_id in post_ids
        assert post2.post_id in post_ids
    
    @pytest.mark.asyncio
    async def test_delete_post_success(self, sample_user_data):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = UUID(user.user_id)
        
        post = await post_repository.create_post(
            user_id=user_id,
            instagram_creation_id="delete_test",
            caption="To be deleted",
            image_url="http://test.com/delete.jpg"
        )
        
        await post_repository.delete_post(user_id=user_id, post_id=post.post_id)
        
        with pytest.raises(PostNotFoundError):
            await post_repository.get_post(user_id=user_id, post_id=post.post_id)
    
    @pytest.mark.asyncio
    async def test_mark_published(self, sample_user_data):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = UUID(user.user_id)
        
        post = await post_repository.create_post(
            user_id=user_id,
            instagram_creation_id="publish_test",
            caption="Publish test",
            image_url="http://test.com/publish.jpg"
        )
        
        assert post.published_at is None
        
        await post_repository.mark_published(
            user_id=user_id,
            instagram_creation_id=post.instagram_creation_id
        )
        
        updated_post = await post_repository.get_post(user_id=user_id, post_id=post.post_id)
        assert updated_post.published_at is not None


@pytest.mark.integration
class TestPostContextRepository:
    
    @pytest.mark.asyncio
    async def test_create_post_context_success(self, sample_user_data):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = UUID(user.user_id)
        
        await post_context_repository.create_context(user_id, SAMPLE_CONTEXT_CONTENT)
        
        ctx = await post_context_repository.get_context(user_id)
        assert ctx is not None
        assert ctx.content == SAMPLE_CONTEXT_CONTENT
    
    @pytest.mark.asyncio
    async def test_update_post_context_success(self, sample_user_data):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = UUID(user.user_id)
        
        await post_context_repository.create_context(user_id, SAMPLE_CONTEXT_CONTENT)
        
        new_content = "Updated context content"
        await post_context_repository.update_context(user_id, new_content)
        
        ctx = await post_context_repository.get_context(user_id)
        assert ctx.content == new_content
    
    @pytest.mark.asyncio
    async def test_delete_post_context_success(self, sample_user_data):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = UUID(user.user_id)
        
        await post_context_repository.create_context(user_id, SAMPLE_CONTEXT_CONTENT)
        await post_context_repository.delete_context(user_id)
        
        ctx = await post_context_repository.get_context(user_id)
        assert ctx is None


@pytest.mark.integration
class TestWikiContextRepository:
    
    @pytest.mark.asyncio
    async def test_create_wiki_context_success(self, sample_user_data):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = UUID(user.user_id)
        
        await wiki_context_repository.create_context(user_id, SAMPLE_CONTEXT_CONTENT)
        
        ctx = await wiki_context_repository.get_context(user_id)
        assert ctx is not None
        assert ctx.content == SAMPLE_CONTEXT_CONTENT
    
    @pytest.mark.asyncio
    async def test_update_wiki_context_success(self, sample_user_data):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = UUID(user.user_id)
        
        await wiki_context_repository.create_context(user_id, SAMPLE_CONTEXT_CONTENT)
        
        new_content = "Updated wiki context"
        await wiki_context_repository.update_context(user_id, new_content)
        
        ctx = await wiki_context_repository.get_context(user_id)
        assert ctx.content == new_content
    
    @pytest.mark.asyncio
    async def test_delete_wiki_context_success(self, sample_user_data):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = UUID(user.user_id)
        
        await wiki_context_repository.create_context(user_id, SAMPLE_CONTEXT_CONTENT)
        await wiki_context_repository.delete_context(user_id)
        
        ctx = await wiki_context_repository.get_context(user_id)
        assert ctx is None

