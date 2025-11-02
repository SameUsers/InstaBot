from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from source.dependencies.current_user import current_user
from source.schemas.auth import CurrentUserSchema
from source.repositories.post import post_repository
from source.core.exceptions import PostNotFoundError
from source.schemas.post import (
    CreatePostRecordRequest, 
    PostResponse, 
    PostsListResponse, 
    PublishByCreationIdRequest,
    SetTimeToPublishRequest
)

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PostResponse)
async def create_post_record(
    data: CreatePostRecordRequest,
    current_user: CurrentUserSchema = Depends(current_user)
):
    post = await post_repository.create_post(
        user_id=current_user.user_id,
        instagram_creation_id=data.instagram_creation_id,
        caption=data.caption,
        image_url=data.image_url,
    )
    return post

@router.get("/", status_code=status.HTTP_200_OK, response_model=PostsListResponse)
async def list_posts(
    current_user: CurrentUserSchema = Depends(current_user)
):
    items = await post_repository.list_posts(user_id=current_user.user_id)
    return {"items": items}

@router.get("/{post_id}", status_code=status.HTTP_200_OK, response_model=PostResponse)
async def get_post(
    post_id: UUID,
    current_user: CurrentUserSchema = Depends(current_user)
):
    try:
        post = await post_repository.get_post(user_id=current_user.user_id, post_id=post_id)
        return post
    except PostNotFoundError:
        raise HTTPException(status_code=404, detail="Post not found")

@router.put("/publish", status_code=status.HTTP_204_NO_CONTENT)
async def mark_published(
    data: PublishByCreationIdRequest,
    current_user: CurrentUserSchema = Depends(current_user)
):
    try:
        await post_repository.mark_published(user_id=current_user.user_id, instagram_creation_id=data.creation_id)
    except PostNotFoundError:
        raise HTTPException(status_code=404, detail="Post not found")

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: UUID,
    current_user: CurrentUserSchema = Depends(current_user)
):
    try:
        await post_repository.delete_post(user_id=current_user.user_id, post_id=post_id)
    except PostNotFoundError:
        raise HTTPException(status_code=404, detail="Post not found")

@router.put("/set-publish-time", status_code=status.HTTP_200_OK, response_model=PostResponse)
async def set_time_to_publish(
    data: SetTimeToPublishRequest,
    current_user: CurrentUserSchema = Depends(current_user)
):
    try:
        post = await post_repository.update_time_to_publish(
            user_id=current_user.user_id,
            post_id=data.post_id,
            time_to_publish=data.time_to_publish
        )
        return post
    except PostNotFoundError:
        raise HTTPException(status_code=404, detail="Post not found")
