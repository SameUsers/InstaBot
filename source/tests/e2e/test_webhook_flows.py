import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from main import app
from source.repositories.user import user_repository
from source.repositories.instagram import instagram_repository
from source.repositories.wiki_context import wiki_context_repository
from source.schemas.auth import RegistrationSchema
from source.schemas.instagram import CreateInstagramCredentials
from source.auth.password import hash_password

WEBHOOK_MESSAGING_PAYLOAD = {
    "object": "instagram",
    "entry": [
        {
            "id": "0",
            "time": 1762076519,
            "messaging": [
                {
                    "sender": {"id": "123456789"},
                    "recipient": {"id": "987654321"},
                    "timestamp": 1762076518,
                    "message": {
                        "mid": "mid.1234567890",
                        "text": "Hello, this is a test message!"
                    }
                }
            ]
        }
    ]
}

WEBHOOK_CHANGES_PAYLOAD = {
    "object": "instagram",
    "entry": [
        {
            "id": "0",
            "time": 1762076519,
            "changes": [
                {
                    "field": "comments",
                    "value": {
                        "from": {
                            "id": "232323232",
                            "username": "test_user"
                        },
                        "media": {
                            "id": "17912345678901234"
                        },
                        "comment_id": "17812345678901234",
                        "text": "This is an example comment."
                    }
                }
            ]
        }
    ]
}

WEBHOOK_VERIFICATION_REQUEST = {
    "hub.mode": "subscribe",
    "hub.challenge": "460578810",
    "hub.verify_token": "change_me_instagram_webhook_verification_token"
}


@pytest.mark.e2e
class TestWebhookFlows:
    
    def test_webhook_verification_success(self):
        with TestClient(app) as client:
            params = WEBHOOK_VERIFICATION_REQUEST
            
            response = client.get("/v1/botservice/webhook", params=params)
            
            assert response.status_code == 200
            assert response.text == params["hub.challenge"]
    
    def test_webhook_verification_invalid_token(self):
        with TestClient(app) as client:
            params = {
                "hub.mode": "subscribe",
                "hub.challenge": "12345",
                "hub.verify_token": "wrong_token"
            }
            
            response = client.get("/v1/botservice/webhook", params=params)
            
            assert response.status_code == 403
    
    def test_webhook_verification_invalid_mode(self):
        with TestClient(app) as client:
            params = {
                "hub.mode": "unsubscribe",
                "hub.challenge": "12345",
                "hub.verify_token": WEBHOOK_VERIFICATION_REQUEST["hub.verify_token"]
            }
            
            response = client.get("/v1/botservice/webhook", params=params)
            
            assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_webhook_messaging_event_processed(self, sample_user_data, sample_instagram_credentials):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = str(user.user_id)
        
        insta_data = CreateInstagramCredentials(**sample_instagram_credentials)
        await instagram_repository.create_instagram_credentials(insta_data, user_id)
        
        wiki_context = "Test context for AI responses"
        await wiki_context_repository.create_context(user_id, wiki_context)
        
        payload = WEBHOOK_MESSAGING_PAYLOAD.copy()
        payload["entry"][0]["messaging"][0]["recipient"]["id"] = str(insta_data.instagram_id)
        
        with TestClient(app) as client:
            with patch('source.api.v1.instagram.openrouter.generate_response', new_callable=AsyncMock) as mock_ai:
                mock_ai.return_value = "AI generated response"
                
                with patch('source.api.v1.instagram.Messages.send_message', new_callable=AsyncMock) as mock_send:
                    mock_send.return_value = None
                    
                    response = client.post("/v1/botservice/webhook", json=payload)
                    
                    assert response.status_code == 200
                    mock_ai.assert_called_once()
                    mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_webhook_changes_event_logged_only(self, sample_user_data, sample_instagram_credentials):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = str(user.user_id)
        
        insta_data = CreateInstagramCredentials(**sample_instagram_credentials)
        await instagram_repository.create_instagram_credentials(insta_data, user_id)
        
        payload = WEBHOOK_CHANGES_PAYLOAD.copy()
        
        with TestClient(app) as client:
            with patch('source.api.v1.instagram.openrouter.generate_response', new_callable=AsyncMock) as mock_ai:
                with patch('source.api.v1.instagram.Messages.send_message', new_callable=AsyncMock) as mock_send:
                    response = client.post("/v1/botservice/webhook", json=payload)
                    
                    assert response.status_code == 200
                    mock_ai.assert_not_called()
                    mock_send.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_webhook_messaging_no_user_found(self, sample_instagram_credentials):
        payload = WEBHOOK_MESSAGING_PAYLOAD.copy()
        payload["entry"][0]["messaging"][0]["recipient"]["id"] = "9999999999"
        
        with TestClient(app) as client:
            with patch('source.api.v1.instagram.openrouter.generate_response', new_callable=AsyncMock) as mock_ai:
                with patch('source.api.v1.instagram.Messages.send_message', new_callable=AsyncMock) as mock_send:
                    response = client.post("/v1/botservice/webhook", json=payload)
                    
                    assert response.status_code == 200
                    mock_ai.assert_not_called()
                    mock_send.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_webhook_messaging_no_credentials(self, sample_user_data, sample_instagram_credentials):
        user_data = RegistrationSchema(**sample_user_data)
        hashed = hash_password(user_data.password)
        user = await user_repository.create_user(user_data, hashed)
        user_id = str(user.user_id)
        
        insta_data = CreateInstagramCredentials(**sample_instagram_credentials)
        await instagram_repository.create_instagram_credentials(insta_data, user_id)
        
        payload = WEBHOOK_MESSAGING_PAYLOAD.copy()
        payload["entry"][0]["messaging"][0]["recipient"]["id"] = str(insta_data.instagram_id)
        
        with TestClient(app) as client:
            with patch('source.api.v1.instagram.openrouter.generate_response', new_callable=AsyncMock) as mock_ai:
                mock_ai.return_value = "AI response"
                
                with patch('source.services.instagram.Messages.send_message', new_callable=AsyncMock) as mock_send:
                    response = client.post("/v1/botservice/webhook", json=payload)
                    
                    assert response.status_code == 200
                    mock_ai.assert_called_once()
                    mock_send.assert_called_once()
    
    def test_webhook_invalid_json_returns_200(self):
        with TestClient(app) as client:
            response = client.post(
                "/v1/botservice/webhook",
                json={"invalid": "payload"},
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 200
    
    def test_webhook_malformed_json_returns_200(self):
        with TestClient(app) as client:
            response = client.post(
                "/v1/botservice/webhook",
                data="not valid json",
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 200

