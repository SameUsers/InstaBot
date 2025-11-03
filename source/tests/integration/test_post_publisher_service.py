import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import UUID

from source.services.post_publisher import post_publish_service
from source.repositories.post import post_repository
from source.repositories.user import user_repository
from source.repositories.instagram import instagram_repository
from source.schemas.auth import RegistrationSchema
from source.schemas.instagram import CreateInstagramCredentials
from source.auth.password import hash_password
from source.tests.fixtures.database import sample_user_data, sample_instagram_credentials
from source.tests.fixtures.sample_data import SAMPLE_POST_DATA
from source.utils.datetime_utils import utcnow


@pytest.mark.integration
class TestPostPublisherService:
    
    @pytest.mark.asyncio
    async def test_publish_pending_posts_no_posts(self):
        result = await post_publish_service.publish_pending_posts()
        assert result is None
    
    @pytest.mark.asyncio
    async def test_publish_pending_posts_no_credentials(self, sample_user_data):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = UUID(user.user_id)
        
        future_time = utcnow() + timedelta(hours=-1)
        
        post = await post_repository.create_post(
            user_id=user_id,
            instagram_creation_id="test_no_creds",
            caption="Test without credentials",
            image_url="http://test.com/image.jpg"
        )
        
        await post_repository.update_time_to_publish(
            user_id=user_id,
            post_id=post.post_id,
            time_to_publish=future_time
        )
        
        with patch('source.services.post_publisher.Publisher.publish_media') as mock_publish:
            await post_publish_service.publish_pending_posts()
            
            mock_publish.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_publish_pending_posts_with_credentials(self, sample_user_data, sample_instagram_credentials):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = UUID(user.user_id)
        
        insta_data = CreateInstagramCredentials(**sample_instagram_credentials)
        await instagram_repository.create_instagram_credentials(insta_data, user_id)
        
        past_time = utcnow() + timedelta(hours=-1)
        
        post = await post_repository.create_post(
            user_id=user_id,
            instagram_creation_id="test_publish",
            caption="Test publish",
            image_url="http://test.com/image.jpg"
        )
        
        await post_repository.update_time_to_publish(
            user_id=user_id,
            post_id=post.post_id,
            time_to_publish=past_time
        )
        
        with patch('source.services.post_publisher.Publisher.publish_media', new_callable=AsyncMock) as mock_publish:
            mock_publish.return_value = None
            
            await post_publish_service.publish_pending_posts()
            
            mock_publish.assert_called_once()
            
            refreshed_post = await post_repository.get_post(user_id=user_id, post_id=post.post_id)
            assert refreshed_post.published_at is not None
    
    @pytest.mark.asyncio
    async def test_publish_pending_posts_future_post_not_published(self, sample_user_data, sample_instagram_credentials):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = UUID(user.user_id)
        
        insta_data = CreateInstagramCredentials(**sample_instagram_credentials)
        await instagram_repository.create_instagram_credentials(insta_data, user_id)
        
        future_time = utcnow() + timedelta(hours=1)
        
        post = await post_repository.create_post(
            user_id=user_id,
            instagram_creation_id="test_future",
            caption="Test future post",
            image_url="http://test.com/image.jpg"
        )
        
        await post_repository.update_time_to_publish(
            user_id=user_id,
            post_id=post.post_id,
            time_to_publish=future_time
        )
        
        with patch('source.services.post_publisher.Publisher.publish_media', new_callable=AsyncMock) as mock_publish:
            await post_publish_service.publish_pending_posts()
            
            mock_publish.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_publish_pending_posts_already_published_not_published_again(self, sample_user_data, sample_instagram_credentials):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = UUID(user.user_id)
        
        insta_data = CreateInstagramCredentials(**sample_instagram_credentials)
        await instagram_repository.create_instagram_credentials(insta_data, user_id)
        
        past_time = utcnow() + timedelta(hours=-1)
        
        post = await post_repository.create_post(
            user_id=user_id,
            instagram_creation_id="test_already_published",
            caption="Test already published",
            image_url="http://test.com/image.jpg"
        )
        
        await post_repository.update_time_to_publish(
            user_id=user_id,
            post_id=post.post_id,
            time_to_publish=past_time
        )
        
        await post_repository.mark_published(
            user_id=user_id,
            instagram_creation_id=post.instagram_creation_id
        )
        
        with patch('source.services.post_publisher.Publisher.publish_media', new_callable=AsyncMock) as mock_publish:
            await post_publish_service.publish_pending_posts()
            
            mock_publish.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_publish_pending_posts_handles_publish_error_gracefully(self, sample_user_data, sample_instagram_credentials):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = UUID(user.user_id)
        
        insta_data = CreateInstagramCredentials(**sample_instagram_credentials)
        await instagram_repository.create_instagram_credentials(insta_data, user_id)
        
        past_time = utcnow() + timedelta(hours=-1)
        
        post = await post_repository.create_post(
            user_id=user_id,
            instagram_creation_id="test_error",
            caption="Test error handling",
            image_url="http://test.com/image.jpg"
        )
        
        await post_repository.update_time_to_publish(
            user_id=user_id,
            post_id=post.post_id,
            time_to_publish=past_time
        )
        
        with patch('source.services.post_publisher.Publisher.publish_media', new_callable=AsyncMock) as mock_publish:
            mock_publish.side_effect = Exception("Instagram API error")
            
            await post_publish_service.publish_pending_posts()
            
            mock_publish.assert_called_once()
            
            refreshed_post = await post_repository.get_post(user_id=user_id, post_id=post.post_id)
            assert refreshed_post.published_at is None

