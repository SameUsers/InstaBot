from fastapi import APIRouter, Depends
from source.schemas.auth import CurrentUserSchema
from source.dependencies.current_user import current_user

router = APIRouter()

@router.get("/me", response_model=CurrentUserSchema)
async def get_current_user_info(
    user: CurrentUserSchema = Depends(current_user)
) -> CurrentUserSchema:
    return user