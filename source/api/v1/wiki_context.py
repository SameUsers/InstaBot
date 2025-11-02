from fastapi import APIRouter, Depends, status, HTTPException
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
    try:
        await wiki_context_repository.create_context(current_user.user_id, data)
        return WikibaseContextResponse(message="Wikibase context saved successfully")
    except WikibaseContextAlreadyExistsError:
        raise HTTPException(status_code=400, detail="Wikibase context already exists for this user")

@router.get("/", status_code=status.HTTP_200_OK, response_model=WikibaseContextGetResponse)
async def get_wikibase(
    current_user: CurrentUserSchema = Depends(current_user)
):
    ctx = await wiki_context_repository.get_context(current_user.user_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="Wikibase context not found")
    return {"content": ctx.content}

@router.put("/", status_code=status.HTTP_200_OK, response_model=WikibaseContextResponse)
async def update_wikibase(
    data: CreateWikibaseContext,
    current_user: CurrentUserSchema = Depends(current_user)
):
    try:
        await wiki_context_repository.update_context(current_user.user_id, data)
        return WikibaseContextResponse(message="Wikibase context updated successfully")
    except WikibaseContextNotFoundError:
        raise HTTPException(status_code=404, detail="Wikibase context not found")

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wikibase(
    current_user: CurrentUserSchema = Depends(current_user)
):
    try:
        await wiki_context_repository.delete_context(current_user.user_id)
    except WikibaseContextNotFoundError:
        raise HTTPException(status_code=404, detail="Wikibase context not found")
