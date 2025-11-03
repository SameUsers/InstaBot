import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from uuid import UUID

from main import app
from source.repositories.user import user_repository
from source.repositories.instagram import instagram_repository
from source.repositories.post_context import post_context_repository
from source.repositories.post import post_repository
from source.schemas.auth import RegistrationSchema
from source.schemas.instagram import CreateInstagramCredentials
from source.auth.password import hash_password
from source.auth.jwt import token_service
from source.utils.datetime_utils import utcnow

SAMPLE_CONTEXT_CONTENT = "This is a sample context for testing purposes."


@pytest.mark.e2e
class TestPostCreationWorkflow:
    
    @pytest.mark.asyncio
    async def test_complete_post_creation_workflow(self, sample_user_data, sample_instagram_credentials):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = str(user.user_id)
        
        tokens = await token_service.register_tokens(
            email=user.email,
            username=user.username,
            user_id=user_id,
            permissions=user.permissions,
            refresh_token_version=user.refresh_token_version
        )
        access_token = tokens.access_token
        
        insta_data = CreateInstagramCredentials(**sample_instagram_credentials)
        await instagram_repository.create_instagram_credentials(insta_data, UUID(user_id))
        
        await post_context_repository.create_context(UUID(user_id), SAMPLE_CONTEXT_CONTENT)
        
        with TestClient(app) as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            with patch('source.services.openrouter.openrouter.create_post_for_user', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = {
                    "text": "Generated post caption",
                    "image_url": "http://minio:9000/images/generated_image.jpg"
                }
                
                with patch('source.services.instagram.Publisher.create_media_container', new_callable=AsyncMock) as mock_container:
                    mock_container.return_value = "media_container_id_12345"
                    
                    response = client.post(
                        "/v1/botservice/post/prepare",
                        headers=headers,
                        json={
                            "image_url": ["http://test.com/image.jpg"],
                            "caption": "Test caption"
                        }
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert "post_id" in data
                    assert "image_url" in data
                    assert "caption" in data
                    assert "creation_id" in data
                    
                    mock_create.assert_called_once()
                    mock_container.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_post_creation_without_context(self, sample_user_data, sample_instagram_credentials):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = str(user.user_id)
        
        tokens = await token_service.register_tokens(
            email=user.email,
            username=user.username,
            user_id=user_id,
            permissions=user.permissions,
            refresh_token_version=user.refresh_token_version
        )
        access_token = tokens.access_token
        
        insta_data = CreateInstagramCredentials(**sample_instagram_credentials)
        await instagram_repository.create_instagram_credentials(insta_data, UUID(user_id))
        
        with TestClient(app) as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            with patch('source.services.openrouter.openrouter.create_post_for_user', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = {
                    "text": "Generated post without context",
                    "image_url": "http://minio:9000/images/generated_image.jpg"
                }
                
                with patch('source.services.instagram.Publisher.create_media_container', new_callable=AsyncMock) as mock_container:
                    mock_container.return_value = "media_container_id_67890"
                    
                    response = client.post(
                        "/v1/botservice/post/prepare",
                        headers=headers,
                        json={
                            "image_url": ["http://test.com/image2.jpg"],
                            "caption": "Test caption 2"
                        }
                    )
                    
                    assert response.status_code == 200
                    mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_post_creation_workflow_stores_post_in_db(self, sample_user_data, sample_instagram_credentials):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = str(user.user_id)
        
        tokens = await token_service.register_tokens(
            email=user.email,
            username=user.username,
            user_id=user_id,
            permissions=user.permissions,
            refresh_token_version=user.refresh_token_version
        )
        access_token = tokens.access_token
        
        insta_data = CreateInstagramCredentials(**sample_instagram_credentials)
        await instagram_repository.create_instagram_credentials(insta_data, UUID(user_id))
        
        with TestClient(app) as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            with patch('source.services.openrouter.openrouter.create_post_for_user', new_callable=AsyncMock) as mock_create:
                mock_create.return_value = {
                    "text": "Stored post caption",
                    "image_url": "http://minio:9000/images/stored_image.jpg"
                }
                
                with patch('source.services.instagram.Publisher.create_media_container', new_callable=AsyncMock) as mock_container:
                    mock_container.return_value = "stored_container_id"
                    
                    response = client.post(
                        "/v1/botservice/post/prepare",
                        headers=headers,
                        json={
                            "image_url": ["http://test.com/store.jpg"],
                            "caption": "Store this"
                        }
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    creation_id = data["creation_id"]
                    
                    posts = await post_repository.list_posts(user_id=UUID(user_id))
                    assert len(posts) > 0
                    post = next((p for p in posts if p.instagram_creation_id == creation_id), None)
                    assert post is not None
                    assert post.caption == "Stored post caption"
    
    @pytest.mark.asyncio
    async def test_post_publish_workflow(self, sample_user_data, sample_instagram_credentials):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = str(user.user_id)
        
        tokens = await token_service.register_tokens(
            email=user.email,
            username=user.username,
            user_id=user_id,
            permissions=user.permissions,
            refresh_token_version=user.refresh_token_version
        )
        access_token = tokens.access_token
        
        insta_data = CreateInstagramCredentials(**sample_instagram_credentials)
        await instagram_repository.create_instagram_credentials(insta_data, UUID(user_id))
        
        post = await post_repository.create_post(
            user_id=UUID(user_id),
            instagram_creation_id="test_publish_creation_id",
            caption="Test publish post",
            image_url="http://test.com/publish.jpg"
        )
        
        with TestClient(app) as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            with patch('source.services.instagram.Publisher.publish_media', new_callable=AsyncMock) as mock_publish:
                mock_publish.return_value = None
                
                response = client.post(
                    "/v1/botservice/post/publish",
                    headers=headers,
                    json={"post_id": str(post.post_id)}
                )
                
                assert response.status_code == 204
                mock_publish.assert_called_once()

