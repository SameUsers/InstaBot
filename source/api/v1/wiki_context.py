from fastapi import APIRouter, Depends, status, HTTPException
from loguru import logger

from source.schemas.wiki_context import (
    CreateWikibaseContext,
    WikibaseContextResponse,
    WikibaseContextGetResponse,
)
from source.schemas.auth import CurrentUserSchema
from source.dependencies.current_user import current_user
from source.repositories.wiki_context import wiki_context_repository
from source.core.exceptions import WikibaseContextAlreadyExistsError, WikibaseContextNotFoundError

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=WikibaseContextResponse)
async def create_wikibase(
    data: CreateWikibaseContext,
    current_user: CurrentUserSchema = Depends(current_user)
):
    logger.info("Creating WikiBase context: user_id={user_id}", user_id=str(current_user.user_id))
    try:
        await wiki_context_repository.create_context(current_user.user_id, data.content)
        logger.info("WikiBase context created: user_id={user_id}", user_id=str(current_user.user_id))
        return WikibaseContextResponse(message="Wikibase context saved successfully")
    except WikibaseContextAlreadyExistsError:
        logger.warning("WikiBase context already exists: user_id={user_id}", user_id=str(current_user.user_id))
        raise HTTPException(status_code=400, detail="Wikibase context already exists for this user")

@router.get("/", status_code=status.HTTP_200_OK, response_model=WikibaseContextGetResponse)
async def get_wikibase(
    current_user: CurrentUserSchema = Depends(current_user)
):
    logger.info("Getting WikiBase context: user_id={user_id}", user_id=str(current_user.user_id))
    ctx = await wiki_context_repository.get_context(current_user.user_id)
    if not ctx:
        logger.warning("WikiBase context not found: user_id={user_id}", user_id=str(current_user.user_id))
        raise HTTPException(status_code=404, detail="Wikibase context not found")
    return {"content": ctx.content}

@router.put("/", status_code=status.HTTP_200_OK, response_model=WikibaseContextResponse)
async def update_wikibase(
    data: CreateWikibaseContext,
    current_user: CurrentUserSchema = Depends(current_user)
):
    logger.info("Updating WikiBase context: user_id={user_id}", user_id=str(current_user.user_id))
    try:
        await wiki_context_repository.update_context(current_user.user_id, data.content)
        logger.info("WikiBase context updated: user_id={user_id}", user_id=str(current_user.user_id))
        return WikibaseContextResponse(message="Wikibase context updated successfully")
    except WikibaseContextNotFoundError:
        logger.warning("WikiBase context not found for update: user_id={user_id}", user_id=str(current_user.user_id))
        raise HTTPException(status_code=404, detail="Wikibase context not found")

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wikibase(
    current_user: CurrentUserSchema = Depends(current_user)
):
    logger.info("Deleting WikiBase context: user_id={user_id}", user_id=str(current_user.user_id))
    try:
        await wiki_context_repository.delete_context(current_user.user_id)
        logger.info("WikiBase context deleted: user_id={user_id}", user_id=str(current_user.user_id))
    except WikibaseContextNotFoundError:
        logger.warning("WikiBase context not found for deletion: user_id={user_id}", user_id=str(current_user.user_id))
        raise HTTPException(status_code=404, detail="Wikibase context not found")
