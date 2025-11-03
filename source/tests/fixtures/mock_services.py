import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock
import json


def mock_openrouter_response():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "This is a test AI-generated response."
                }
            }
        ]
    }
    return mock_response


def mock_openrouter_image_response():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Generated image caption: Beautiful sunset"
                }
            }
        ]
    }
    return mock_response


def mock_instagram_message_response():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"recipient_id": "123456789"}
    return mock_response


def mock_instagram_media_container_response():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "media_container_id_12345"}
    return mock_response


def mock_instagram_publish_response():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "published_post_id_67890"}
    return mock_response


@pytest.fixture
def mock_httpx_client(monkeypatch):
    async def async_mock_post(*args, **kwargs):
        url = args[0]
        mock_response = MagicMock()
        
        if "openrouter.ai" in url:
            if kwargs.get("content") and "image" in kwargs.get("content", "").lower():
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "choices": [
                        {
                            "message": {
                                "content": "data:image/png;base64,iVBORw0KGgoAAAANS..."
                            }
                        }
                    ]
                }
            else:
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "choices": [
                        {
                            "message": {
                                "content": "Test AI response"
                            }
                        }
                    ]
                }
        elif "graph.instagram.com" in url:
            if "/messages" in url:
                mock_response.status_code = 200
                mock_response.json.return_value = {"recipient_id": "123456789"}
            elif "/media" in url and not "media?" in url:
                mock_response.status_code = 200
                mock_response.json.return_value = {"id": "media_id_123"}
            elif "/media_publish" in url:
                mock_response.status_code = 200
                mock_response.json.return_value = {"id": "published_post_id"}
            else:
                mock_response.status_code = 200
                mock_response.json.return_value = {}
        else:
            mock_response.status_code = 200
            mock_response.json.return_value = {}
        
        return mock_response
    
    mock_client = MagicMock()
    mock_client.post = AsyncMock(side_effect=async_mock_post)
    
    return mock_client

