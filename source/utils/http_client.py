import httpx
from typing import Dict, Any, Optional
from loguru import logger

class HttpClient:
    def __init__(self, base_url: Optional[str] = None, default_headers: Optional[Dict[str, str]] = None):
        self.base_url = base_url or ""
        self.default_headers = default_headers or {}

    def _build_url(self, endpoint: str) -> str:
        if self.base_url:
            return f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        return endpoint

    def _merge_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        merged = self.default_headers.copy()
        if headers:
            merged.update(headers)
        return merged

    async def post(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None, 
             data: Optional[str] = None, headers: Optional[Dict[str, str]] = None,
             timeout: int = 30) -> httpx.Response:
        url = self._build_url(endpoint)
        merged_headers = self._merge_headers(headers)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=json_data,
                    content=data if data else None,
                    headers=merged_headers,
                    timeout=timeout
                )
                if response.status_code >= 400:
                    request_body = json_data or data
                    logger.error(
                        "HTTP POST request failed: url={url}, status={status}, request_body={req_body}, response_body={body}",
                        url=url,
                        status=response.status_code,
                        req_body=str(request_body)[:500] if request_body else None,
                        body=response.text[:500]
                    )
                response.raise_for_status()
                return response
        except httpx.HTTPError as exc:
            request_body = json_data or data
            logger.exception("HTTP POST request failed: url={url}, error={error}, request_body={req_body}", 
                           url=url, error=str(exc), req_body=str(request_body)[:500] if request_body else None)
            raise

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None, timeout: int = 30) -> httpx.Response:
        url = self._build_url(endpoint)
        merged_headers = self._merge_headers(headers)
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=merged_headers,
                    timeout=timeout
                )
                if response.status_code >= 400:
                    logger.error(
                        "HTTP GET request failed: url={url}, status={status}, response_body={body}",
                        url=url,
                        status=response.status_code,
                        body=response.text[:500]
                    )
                response.raise_for_status()
                return response
        except httpx.HTTPError as exc:
            logger.exception("HTTP GET request failed: url={url}, error={error}",
                           url=url, error=str(exc))
            raise

