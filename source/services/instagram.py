import json
import asyncio
from loguru import logger

from source.utils.http_client import HttpClient

BASE_IG_URL = "https://graph.instagram.com/v24.0"

class Messages:
    @classmethod
    def _build_headers(cls, inst_token: str) -> dict:
        return {
            "Authorization": f"Bearer {inst_token}",
            "Content-Type": "application/json",
        }

    @classmethod
    def _build_message_body(cls, recipient_id: str, message: str) -> dict:
        return {
            "recipient": {"id": recipient_id},
            "message": {"text": message},
        }

    @classmethod
    async def send_message(cls, recipient_id: str, message: str, *, inst_id: int | str, inst_token: str) -> None:
        headers = cls._build_headers(inst_token)
        body = cls._build_message_body(recipient_id, message)
        url = f"{BASE_IG_URL}/{inst_id}/messages"
        
        logger.info(
            "Sending IG message: recipient={recipient} inst_id={inst_id} body_preview={preview}",
            recipient=recipient_id,
            inst_id=inst_id,
            preview=(message[:120] + "...") if message and len(message) > 120 else message,
        )
        
        client = HttpClient()
        response = await client.post(url, json_data=body, headers=headers, timeout=15)
        logger.info("IG API response: status={status}", status=response.status_code)

class Publisher:
    @classmethod
    def _build_auth_headers(cls, inst_token: str) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {inst_token}",
        }

    @classmethod
    def _build_container_body(cls, image_url: str, caption: str) -> dict:
        return {
            "image_url": image_url,
            "caption": caption,
        }

    @classmethod
    def _extract_media_id(cls, response_data: dict) -> str:
        media_id = response_data.get("id")
        if not media_id:
            raise ValueError("No media id returned")
        return media_id

    @classmethod
    async def create_media_container(cls, *, inst_id: int | str, inst_token: str, image_url: str, caption: str) -> str:
        headers = cls._build_auth_headers(inst_token)
        container_body = cls._build_container_body(image_url, caption)
        url = f"{BASE_IG_URL}/{inst_id}/media"

        logger.info("Creating IG media container: inst_id={inst_id} image_url={image_url}", inst_id=inst_id, image_url=image_url)
        
        client = HttpClient()
        response = await client.post(url, data=json.dumps(container_body), headers=headers, timeout=60)
        
        container_data = response.json()
        media_id = cls._extract_media_id(container_data)
        logger.info("Container created: media_id={media_id}", media_id=media_id)
        return media_id

    @classmethod
    async def publish_media(cls, *, inst_id: int | str, inst_token: str, creation_id: str) -> None:
        headers = cls._build_auth_headers(inst_token)
        publish_body = {"creation_id": creation_id}
        url = f"{BASE_IG_URL}/{inst_id}/media_publish"
        
        await asyncio.sleep(15)
        
        logger.info("Publishing IG media: creation_id={creation_id}", creation_id=creation_id)
        client = HttpClient()
        response = await client.post(url, data=json.dumps(publish_body), headers=headers, timeout=30)
        logger.info("Publish response: status={status}", status=response.status_code)