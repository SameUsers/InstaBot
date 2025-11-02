from fastapi import APIRouter, Depends, status, HTTPException
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
    try:
        await post_context_repository.create_context(current_user.user_id, data.content)
        return PostBaseContextResponse(message="PostBase context saved successfully")
    except PostBaseContextAlreadyExistsError:
        raise HTTPException(status_code=400, detail="PostBase context already exists for this user")

@router.get("/", status_code=status.HTTP_200_OK, response_model=PostBaseContextGetResponse)
async def get_postbase(
    current_user: CurrentUserSchema = Depends(current_user)
):
    ctx = await post_context_repository.get_context(current_user.user_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="PostBase context not found")
    return {"content": ctx.content}

@router.put("/", status_code=status.HTTP_200_OK, response_model=PostBaseContextResponse)
async def update_postbase(
    data: CreatePostBaseContext,
    current_user: CurrentUserSchema = Depends(current_user)
):
    try:
        await post_context_repository.update_context(current_user.user_id, data.content)
        return PostBaseContextResponse(message="PostBase context updated successfully")
    except PostBaseContextNotFoundError:
        raise HTTPException(status_code=404, detail="PostBase context not found")

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_postbase(
    current_user: CurrentUserSchema = Depends(current_user)
):
    try:
        await post_context_repository.delete_context(current_user.user_id)
    except PostBaseContextNotFoundError:
        raise HTTPException(status_code=404, detail="PostBase context not found")
