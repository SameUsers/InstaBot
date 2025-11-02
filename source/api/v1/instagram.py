import asyncio
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from loguru import logger
from starlette.responses import JSONResponse, PlainTextResponse, Response

from source.conf import settings
from source.repositories.instagram import instagram_repository
from source.repositories.wiki_context import wiki_context_repository
from source.repositories.post import post_repository
from source.core.exceptions import (
    InstagramCredsAlreadyExistsError,
    InstagramCredsNotFoundError,
    PostNotFoundError
)
from source.dependencies.current_user import current_user
from source.schemas.auth import CurrentUserSchema
from source.schemas.instagram import (
    BaseMessageResponse,
    CreateInstagramCredentials,
    CreatePostRequest,
    InstagramCredentialsResponse,
    PreparePostResponse,
    PublishPostRequest,
    InstagramWebhookPayload,
    MessagingItem,
)
from source.services.instagram import Messages, Publisher
from source.services.openrouter import openrouter

router = APIRouter()

@router.get("/webhook")
async def verify_webhook(
    hub_mode: str | None = Query(None, alias="hub.mode"),
    hub_challenge: str | None = Query(None, alias="hub.challenge"),
    hub_verify_token: str | None = Query(None, alias="hub.verify_token"),
) -> Response:
    logger.info("Webhook verification request: mode={mode}, has_challenge={has_challenge}", 
               mode=hub_mode, has_challenge=bool(hub_challenge))
    if hub_mode == "subscribe" and hub_verify_token == settings.verify_token:
        logger.info("Webhook verification succeeded")
        return PlainTextResponse(content=hub_challenge)
    logger.warning("Webhook verification failed: provided_token does not match")
    return JSONResponse({"error": "Verification failed"}, status_code=403)

async def _parse_page_id(recipient_id: str) -> int | None:
    try:
        return int(recipient_id)
    except ValueError:
        return None

async def _resolve_user_id(page_id: int | None) -> UUID | None:
    if page_id is None:
        return None
    return await instagram_repository.get_user_id_by_instagram_id(page_id)

async def _get_wikibase_context(user_id: UUID | None) -> str:
    if not user_id:
        return ""
    ctx = await wiki_context_repository.get_context(user_id)
    return ctx.content if ctx else ""

async def _get_credentials_for_sending(user_id: UUID | None) -> tuple[int | None, str | None]:
    if not user_id:
        return None, None
    credentials = await instagram_repository.get_instagram_credentials(user_id)
    if credentials:
        return credentials.instagram_id, credentials.instagram_token
    return None, None

async def _process_messaging_item(messaging: MessagingItem, page_id: int | None) -> None:
    if not messaging.message:
        return
    
    user_id = await _resolve_user_id(page_id)
    logger.info("Resolved user_id by instagram_id: {user_id}", user_id=str(user_id) if user_id else None)
    
    context_text = await _get_wikibase_context(user_id)
    logger.info("Context length: {length}", length=len(context_text) if context_text else 0)
    
    ai_response = await openrouter.generate_response(
        user_query=messaging.message.text or "",
        context=context_text,
    )
    logger.info("AI response generated: {preview}", 
               preview=(ai_response[:120] + "...") if ai_response and len(ai_response) > 120 else ai_response)
    
    page_for_send, page_access_token = await _get_credentials_for_sending(user_id)
    logger.info("Prepared send params: page_for_send={page_for_send}, has_token={has_token}", 
               page_for_send=page_for_send, has_token=bool(page_access_token))
    
    if page_access_token and page_for_send:
        try:
            await Messages.send_message(
                recipient_id=messaging.sender.id,
                message=ai_response,
                inst_id=page_for_send,
                inst_token=page_access_token,
            )
            logger.info("Message sent to recipient {recipient}", recipient=messaging.sender.id)
        except Exception as exc:
            logger.exception("Failed to send message: {error}", error=str(exc))

@router.post("/webhook")
async def get_event(request: Request) -> None:
    try:
        data = await request.json()
    except Exception as exc:
        logger.exception("Failed to parse incoming webhook JSON: {error}", error=str(exc))
        return

    logger.info("Incoming webhook payload: keys={}", data)
    try:
        payload = InstagramWebhookPayload(**data)
    except Exception as exc:
        logger.exception("Webhook payload validation failed: {error}", error=str(exc))
        return
    
    for entry in payload.entry:
        for messaging in entry.messaging:
            if messaging.message:
                page_id = await _parse_page_id(messaging.recipient.id)
                logger.info("Parsed page_id: {page_id}", page_id=page_id)
                await _process_messaging_item(messaging, page_id)

async def _generate_post_content(user_id: str, caption: str, images: list[str]) -> dict:
    result = await openrouter.create_post_for_user(user_id, caption, images)
    if "error" in result:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации контента: {result['error']}")
    return result

async def _create_media_container(credentials, image_url: str, post_text: str) -> str:
    await asyncio.sleep(10)
    return await Publisher.create_media_container(
        inst_id=credentials.instagram_id,
        inst_token=credentials.instagram_token,
        image_url=image_url,
        caption=post_text,
    )

async def _save_post_record(user_id: UUID, creation_id: str, post_text: str, image_url: str):
    return await post_repository.create_post(
        user_id=user_id,
        instagram_creation_id=creation_id,
        caption=post_text,
        image_url=image_url,
    )

@router.post("/post/prepare", status_code=status.HTTP_200_OK, response_model=PreparePostResponse)
async def prepare_post(
    data: CreatePostRequest,
    current_user: CurrentUserSchema = Depends(current_user),
) -> dict:
    credentials = await instagram_repository.get_instagram_credentials(current_user.user_id)
    if not credentials:
        raise HTTPException(status_code=404, detail="Instagram credentials not found")

    result = await _generate_post_content(str(current_user.user_id), data.caption, data.image_url)
    image_url = result.get("image_url")
    post_text = result.get("text")
    
    creation_id = await _create_media_container(credentials, image_url, post_text)
    post = await _save_post_record(current_user.user_id, creation_id, post_text, image_url)
    
    return {
        "post_id": str(post.post_id), 
        "image_url": image_url, 
        "caption": post_text, 
        "creation_id": creation_id
    }

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=BaseMessageResponse)
async def register_instagram_credentials(
    data: CreateInstagramCredentials,
    current_user: CurrentUserSchema = Depends(current_user),
) -> BaseMessageResponse:
    try:
        await instagram_repository.create_instagram_credentials(
            data,
            user_id=current_user.user_id
        )
        return BaseMessageResponse(message="Instagram credentials saved successfully")
    except InstagramCredsAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Instagram credentials already exist for this user"
        )
    except Exception as e:
        logger.exception("Failed to save Instagram credentials: {error}", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to save credentials: {str(e)}"
        )

@router.get("/creds", status_code=status.HTTP_200_OK, response_model=InstagramCredentialsResponse)
async def get_instagram_credentials(
    current_user: CurrentUserSchema = Depends(current_user),
) -> dict:
    credentials = await instagram_repository.get_instagram_credentials(current_user.user_id)
    if not credentials:
        raise HTTPException(status_code=404, detail="Instagram credentials not found")
    return {
        "instagram_id": credentials.instagram_id,
        "instagram_token": credentials.instagram_token,
    }

@router.put("/creds", status_code=status.HTTP_200_OK, response_model=BaseMessageResponse)
async def update_instagram_credentials(
    data: CreateInstagramCredentials,
    current_user: CurrentUserSchema = Depends(current_user),
) -> BaseMessageResponse:
    try:
        await instagram_repository.update_instagram_credentials(current_user.user_id, data)
        return BaseMessageResponse(message="Instagram credentials updated successfully")
    except InstagramCredsNotFoundError:
        raise HTTPException(status_code=404, detail="Instagram credentials not found")

@router.post("/post/publish", status_code=status.HTTP_204_NO_CONTENT)
async def publish_post(
    data: PublishPostRequest,
    current_user: CurrentUserSchema = Depends(current_user),
) -> None:
    credentials = await instagram_repository.get_instagram_credentials(current_user.user_id)
    if not credentials:
        raise HTTPException(status_code=404, detail="Instagram credentials not found")
    try:
        post = await post_repository.get_post(user_id=current_user.user_id, post_id=data.post_id)
    except PostNotFoundError:
        raise HTTPException(status_code=404, detail="Post not found")
    await Publisher.publish_media(
        inst_id=credentials.instagram_id,
        inst_token=credentials.instagram_token,
        creation_id=post.instagram_creation_id,
    )
    await post_repository.mark_published(
        user_id=current_user.user_id, 
        instagram_creation_id=post.instagram_creation_id
    )

@router.delete("/creds", status_code=status.HTTP_204_NO_CONTENT)
async def delete_instagram_credentials(
    current_user: CurrentUserSchema = Depends(current_user),
) -> None:
    try:
        await instagram_repository.delete_instagram_credentials(current_user.user_id)
    except InstagramCredsNotFoundError:
        raise HTTPException(status_code=404, detail="Instagram credentials not found")