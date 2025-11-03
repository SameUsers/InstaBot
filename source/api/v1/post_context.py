from fastapi import APIRouter, Depends, status, HTTPException
from loguru import logger

from source.schemas.post_context import (
    CreatePostBaseContext,
    PostBaseContextResponse,
    PostBaseContextGetResponse,
)
from source.schemas.auth import CurrentUserSchema
from source.dependencies.current_user import current_user
from source.repositories.post_context import post_context_repository
from source.core.exceptions import PostBaseContextAlreadyExistsError, PostBaseContextNotFoundError

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PostBaseContextResponse)
async def create_postbase(
    data: CreatePostBaseContext,
    current_user: CurrentUserSchema = Depends(current_user)
):
    logger.info("Creating PostBase context: user_id={user_id}", user_id=str(current_user.user_id))
    try:
        await post_context_repository.create_context(current_user.user_id, data.content)
        logger.info("PostBase context created: user_id={user_id}", user_id=str(current_user.user_id))
        return PostBaseContextResponse(message="PostBase context saved successfully")
    except PostBaseContextAlreadyExistsError:
        logger.warning("PostBase context already exists: user_id={user_id}", user_id=str(current_user.user_id))
        raise HTTPException(status_code=400, detail="PostBase context already exists for this user")

@router.get("/", status_code=status.HTTP_200_OK, response_model=PostBaseContextGetResponse)
async def get_postbase(
    current_user: CurrentUserSchema = Depends(current_user)
):
    logger.info("Getting PostBase context: user_id={user_id}", user_id=str(current_user.user_id))
    ctx = await post_context_repository.get_context(current_user.user_id)
    if not ctx:
        logger.warning("PostBase context not found: user_id={user_id}", user_id=str(current_user.user_id))
        raise HTTPException(status_code=404, detail="PostBase context not found")
    return {"content": ctx.content}

@router.put("/", status_code=status.HTTP_200_OK, response_model=PostBaseContextResponse)
async def update_postbase(
    data: CreatePostBaseContext,
    current_user: CurrentUserSchema = Depends(current_user)
):
    logger.info("Updating PostBase context: user_id={user_id}", user_id=str(current_user.user_id))
    try:
        await post_context_repository.update_context(current_user.user_id, data.content)
        logger.info("PostBase context updated: user_id={user_id}", user_id=str(current_user.user_id))
        return PostBaseContextResponse(message="PostBase context updated successfully")
    except PostBaseContextNotFoundError:
        logger.warning("PostBase context not found for update: user_id={user_id}", user_id=str(current_user.user_id))
        raise HTTPException(status_code=404, detail="PostBase context not found")

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_postbase(
    current_user: CurrentUserSchema = Depends(current_user)
):
    logger.info("Deleting PostBase context: user_id={user_id}", user_id=str(current_user.user_id))
    try:
        await post_context_repository.delete_context(current_user.user_id)
        logger.info("PostBase context deleted: user_id={user_id}", user_id=str(current_user.user_id))
    except PostBaseContextNotFoundError:
        logger.warning("PostBase context not found for deletion: user_id={user_id}", user_id=str(current_user.user_id))
        raise HTTPException(status_code=404, detail="PostBase context not found")
