import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from source.utils.http_client import HttpClient


class TestHttpClient:
    """Тесты для HTTP клиента"""

    @pytest.fixture
    def client(self):
        """Создание клиента для тестов"""
        return HttpClient()

    def test_init_with_defaults(self, client):
        """Инициализация с дефолтными значениями"""
        assert client.base_url == ""
        assert client.default_headers == {}

    def test_init_with_base_url(self):
        """Инициализация с base_url"""
        client = HttpClient(base_url="https://api.example.com")
        assert client.base_url == "https://api.example.com"

    def test_init_with_default_headers(self):
        """Инициализация с default_headers"""
        headers = {"Authorization": "Bearer token"}
        client = HttpClient(default_headers=headers)
        assert client.default_headers == headers

    def test_build_url_without_base_url(self, client):
        """Построение URL без base_url"""
        url = client._build_url("/endpoint")
        assert url == "/endpoint"

    def test_build_url_with_base_url(self):
        """Построение URL с base_url"""
        client = HttpClient(base_url="https://api.example.com")
        url = client._build_url("/endpoint")
        assert url == "https://api.example.com/endpoint"

    def test_build_url_trailing_slashes(self):
        """Построение URL с trailing slashes"""
        client = HttpClient(base_url="https://api.example.com/")
        url = client._build_url("/endpoint/")
        assert url == "https://api.example.com/endpoint/"

    def test_merge_headers_without_headers(self, client):
        """Слияние заголовков без дополнительных"""
        merged = client._merge_headers()
        assert merged == {}

    def test_merge_headers_with_additional(self, client):
        """Слияние заголовков с дополнительными"""
        client.default_headers = {"Authorization": "Bearer token1"}
        merged = client._merge_headers({"Content-Type": "application/json"})
        
        assert merged == {
            "Authorization": "Bearer token1",
            "Content-Type": "application/json"
        }

    def test_merge_headers_override_default(self, client):
        """Замещение дефолтных заголовков"""
        client.default_headers = {"Authorization": "Bearer token1"}
        merged = client._merge_headers({"Authorization": "Bearer token2"})
        
        assert merged == {"Authorization": "Bearer token2"}

    @pytest.mark.asyncio
    async def test_post_success(self):
        """Успешный POST запрос"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value={"status": "ok"})
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_ctx = MagicMock()
            mock_ctx.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_ctx
            
            client = HttpClient()
            response = await client.post("/test", json_data={"key": "value"})
            
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_post_with_json_data(self):
        """POST запрос с JSON данными"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_ctx = MagicMock()
            mock_ctx.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_ctx
            
            client = HttpClient()
            json_data = {"key": "value"}
            
            await client.post("/test", json_data=json_data)
            
            mock_ctx.post.assert_called_once()
            call_args = mock_ctx.post.call_args
            assert call_args[1]["json"] == json_data

    @pytest.mark.asyncio
    async def test_post_with_string_data(self):
        """POST запрос со строковыми данными"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_ctx = MagicMock()
            mock_ctx.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_ctx
            
            client = HttpClient()
            string_data = '{"key": "value"}'
            
            await client.post("/test", data=string_data)
            
            mock_ctx.post.assert_called_once()
            call_args = mock_ctx.post.call_args
            assert call_args[1]["content"] == string_data

    @pytest.mark.asyncio
    async def test_post_with_custom_headers(self):
        """POST запрос с кастомными заголовками"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_ctx = MagicMock()
            mock_ctx.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_ctx
            
            client = HttpClient(default_headers={"X-API-Key": "secret"})
            await client.post("/test", headers={"Content-Type": "application/json"})
            
            call_args = mock_ctx.post.call_args
            assert call_args[1]["headers"]["X-API-Key"] == "secret"
            assert call_args[1]["headers"]["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_post_with_timeout(self):
        """POST запрос с таймаутом"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_ctx = MagicMock()
            mock_ctx.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_ctx
            
            client = HttpClient()
            await client.post("/test", timeout=60)
            
            call_args = mock_ctx.post.call_args
            assert call_args[1]["timeout"] == 60

    @pytest.mark.asyncio
    async def test_post_raises_on_error(self):
        """POST запрос выбрасывает исключение при ошибке"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_ctx = MagicMock()
            mock_ctx.post = AsyncMock(side_effect=httpx.HTTPError("Connection error"))
            mock_client.return_value.__aenter__.return_value = mock_ctx
            
            client = HttpClient()
            
            with pytest.raises(httpx.HTTPError):
                await client.post("/test")

    @pytest.mark.asyncio
    async def test_get_success(self):
        """Успешный GET запрос"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value={"data": "test"})
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_ctx = MagicMock()
            mock_ctx.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_ctx
            
            client = HttpClient()
            response = await client.get("/test")
            
            assert response.status_code == 200
            assert response.json() == {"data": "test"}

    @pytest.mark.asyncio
    async def test_get_with_params(self):
        """GET запрос с параметрами"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_ctx = MagicMock()
            mock_ctx.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_ctx
            
            client = HttpClient()
            params = {"page": 1, "limit": 10}
            
            await client.get("/test", params=params)
            
            call_args = mock_ctx.get.call_args
            assert call_args[1]["params"] == params

    @pytest.mark.asyncio
    async def test_get_raises_on_error(self):
        """GET запрос выбрасывает исключение при ошибке"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_ctx = MagicMock()
            mock_ctx.get = AsyncMock(side_effect=httpx.HTTPError("Connection error"))
            mock_client.return_value.__aenter__.return_value = mock_ctx
            
            client = HttpClient()
            
            with pytest.raises(httpx.HTTPError):
                await client.get("/test")

