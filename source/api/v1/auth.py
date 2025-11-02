from fastapi import APIRouter, HTTPException

from source.auth.password import hash_password, verify_password
from source.auth.jwt import token_service
from source.core.exceptions import TokenServiceError, InvalidTokenVersionError, UserAlreadyExistsError, UserNotFoundError
from source.repositories.user import user_repository
from source.schemas.auth import (
    RegistrationSchema,
    RegistrationSchemaResponse,
    RefreshResponseSchema,
    LoginSchema
)

router = APIRouter()

@router.post("/registration", response_model=RegistrationSchemaResponse)
async def registration(data: RegistrationSchema):
    hashed = hash_password(data.password)
    try:
        user = await user_repository.create_user(data, hashed)
    except UserAlreadyExistsError:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    return await token_service.register_tokens(
        email=user.email,
        username=user.username,
        user_id=user.user_id,
        permissions=user.permissions,
        refresh_token_version=user.refresh_token_version
    )

@router.post("/refresh", response_model=RefreshResponseSchema)
async def refresh(refresh_token: str):
    try:
        result = await token_service.refresh(refresh_token=refresh_token, increment_token_version=True)
    except InvalidTokenVersionError:
        raise HTTPException(status_code=400, detail="Refresh token expired or invalid: wrong token version.")
    except TokenServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result

@router.post("/login", response_model=RegistrationSchemaResponse)
async def login(data: LoginSchema):
    try:
        user = await user_repository.get_user_by_email(data.email)
    except UserNotFoundError:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not verify_password(data.password, user.hash_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return await token_service.login_tokens(user=user)
