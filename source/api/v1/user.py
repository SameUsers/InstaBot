from fastapi import APIRouter, Depends
from loguru import logger

from source.schemas.auth import CurrentUserSchema
from source.dependencies.current_user import current_user

router = APIRouter()

@router.get("/me", response_model=CurrentUserSchema)
async def get_current_user_info(
    user: CurrentUserSchema = Depends(current_user)
) -> CurrentUserSchema:
    logger.info("Getting current user info: user_id={user_id}", user_id=str(user.user_id))
    return user