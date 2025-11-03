import httpx
import json
from typing import List, Dict, Optional
from uuid import UUID

from source.conf import settings
from source.services.storage import minio_client
from source.core.constants import MessageRole, ContentType, ResponseKeys, ApiResponseKeys, PromptSuffixes
from loguru import logger

class Openrouter:
    def __init__(self, api_key: str | None = None,
                 model: str | None = None,
                 base_url: str | None = None):
        self.api_key = settings.openrouter_key
        self.model = settings.openrouter_model_key
        self.base_url = settings.openrouter_base_url

    def _build_messages(self, user_content: str, system_content: str = "") -> list:
        messages = []
        if system_content:
            messages.append({"role": MessageRole.system, "content": system_content})
        messages.append({"role": MessageRole.user, "content": user_content})
        return messages

    def _extract_content(self, response_data: dict) -> str:
        content = response_data[ApiResponseKeys.choices][0][ApiResponseKeys.message][ApiResponseKeys.content]
        return (content or "").strip()

    async def generate_response(self, user_query: str, context: str = "") -> str:
        user_content = (user_query or "").strip() + PromptSuffixes.max_900_chars
        system_content = (context or "").strip()
        logger.info(
            "Openrouter request: model={model}, has_system={has_system}, query_len={q_len}",
            model=self.model,
            has_system=bool(system_content),
            q_len=len(user_content),
        )

        messages = self._build_messages(user_content, system_content)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                content=json.dumps({
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": settings.openrouter_max_tokens,
                    "temperature": settings.openrouter_temperature
                }),
                timeout=settings.openrouter_timeout
            )
            response.raise_for_status()
            result = response.json()
            content = self._extract_content(result)
            logger.info("Openrouter response: status={status}, preview={preview}", 
                       status=response.status_code, 
                       preview=(content[:120] + "...") if content and len(content) > 120 else content)
            return content

    async def _get_user_context(self, user_id: str, fallback: str = "") -> str:
        try:
            from source.repositories.post_context import post_context_repository
            ctx = await post_context_repository.get_context(UUID(user_id))
            context_to_use = ctx.content if ctx else fallback
            logger.debug("Retrieved user context: user_id={user_id}, has_context={has_ctx}", 
                        user_id=user_id, has_ctx=bool(ctx))
            return context_to_use
        except Exception as exc:
            logger.warning("Failed to get user context, using fallback: user_id={user_id}, error={error}", 
                          user_id=user_id, error=str(exc))
            return fallback

    async def generate_response_for_user(self, user_id: str, user_query: str, *, fallback_context: str = "") -> str:
        system_ctx = await self._get_user_context(user_id, fallback_context)
        return await self.generate_response(user_query=user_query, context=system_ctx)

    @staticmethod
    def _build_post_content(prompt: str, images: List[str]) -> list:
        content = [
            {
                "type": ContentType.text,
                "text": f"{(prompt or '').strip()}{PromptSuffixes.max_2000_chars}"
            }
        ]
        for image_url in images:
            content.append({
                "type": ContentType.image_url,
                ContentType.image_url: {
                    ApiResponseKeys.url: image_url
                }
            })
        return content

    @staticmethod
    def _build_post_messages(content: list, system_ctx: Optional[str] = None) -> list:
        messages = []
        if system_ctx and system_ctx.strip():
            messages.append({"role": MessageRole.system, "content": system_ctx.strip() + PromptSuffixes.max_2000_chars})
        messages.append({"role": MessageRole.user, "content": content})
        return messages

    @staticmethod
    def _extract_image_url(data: dict) -> str:
        return data[ApiResponseKeys.choices][0][ApiResponseKeys.message][ApiResponseKeys.images][0][ApiResponseKeys.image_url][ApiResponseKeys.url]

    @staticmethod
    def _extract_base64_from_data_url(data_url: str) -> str:
        return data_url.split(',')[1]

    @classmethod
    async def create_post(cls, prompt: str, images: List[str], system_ctx: Optional[str] = None) -> Dict[str, str]:
        content = cls._build_post_content(prompt, images)
        messages = cls._build_post_messages(content, system_ctx)

        logger.info(
            "Creating post with OpenRouter: model={model}, images_count={img_count}, has_system_ctx={has_ctx}",
            model=settings.openrouter_image_model_key,
            img_count=len(images),
            has_ctx=bool(system_ctx)
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=settings.openrouter_base_url,
                headers={
                    "Authorization": f"Bearer {settings.openrouter_key}",
                    "Content-Type": "application/json",
                },
                content=json.dumps({
                    "model": settings.openrouter_image_model_key,
                    "messages": messages,
                }),
                timeout=settings.openrouter_timeout
            )
            
            if response.status_code != 200:
                logger.error(
                    "OpenRouter API error: status={status}, response={response}",
                    status=response.status_code,
                    response=response.text[:200]
                )
                return {
                    ResponseKeys.error: f"API error: {response.status_code}",
                    ResponseKeys.details: response.text
                }
            
            data = response.json()
            text_content = data[ApiResponseKeys.choices][0][ApiResponseKeys.message][ApiResponseKeys.content]
            text_content = (text_content or "").strip()
            
            try:
                data_url = cls._extract_image_url(data)
            except Exception as exc:
                logger.exception("Failed to extract image from OpenRouter response: {error}", error=str(exc))
                return {ResponseKeys.error: "Model did not return image data"}
            
            try:
                base64_string = cls._extract_base64_from_data_url(data_url)
            except Exception as exc:
                logger.exception("Failed to decode base64 from data URL: {error}", error=str(exc))
                return {ResponseKeys.error: "Invalid image data URL returned by model"}
            
            image_url = await minio_client.upload_from_base64(base64_string)
            logger.info(
                "Post created successfully: text_len={len}, image_url={url}",
                len=len(text_content),
                url=image_url
            )
            return {
                ResponseKeys.text: text_content,
                ResponseKeys.image_url: image_url
            }

    @classmethod
    async def create_post_for_user(cls, user_id: str, prompt: str, images: List[str]) -> Dict[str, str]:
        try:
            from source.repositories.post_context import post_context_repository
            ctx = await post_context_repository.get_context(UUID(user_id))
            system_ctx = ctx.content if (ctx and ctx.content) else None
        except Exception as exc:
            logger.warning("Failed to get post context for user, proceeding without context: user_id={user_id}, error={error}", 
                          user_id=user_id, error=str(exc))
            system_ctx = None
        return await cls.create_post(prompt, images, system_ctx=system_ctx)

openrouter = Openrouter()