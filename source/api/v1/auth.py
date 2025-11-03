from fastapi import APIRouter, HTTPException
from loguru import logger

from source.auth.password import async_hash_password, async_verify_password
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
    logger.info("Registration attempt: email={email}, username={username}", 
               email=data.email, username=data.username)
    hashed = await async_hash_password(data.password)
    try:
        user = await user_repository.create_user(data, hashed)
        logger.info("User registered successfully: user_id={user_id}, email={email}", 
                   user_id=str(user.user_id), email=user.email)
    except UserAlreadyExistsError:
        logger.warning("Registration failed: email already exists: {email}", email=data.email)
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
    logger.info("Token refresh attempt")
    try:
        result = await token_service.refresh(refresh_token=refresh_token, increment_token_version=True)
        logger.info("Token refresh successful")
    except InvalidTokenVersionError:
        logger.warning("Token refresh failed: invalid token version")
        raise HTTPException(status_code=400, detail="Refresh token expired or invalid: wrong token version.")
    except TokenServiceError as e:
        logger.warning("Token refresh failed: {error}", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    return result

@router.post("/login", response_model=RegistrationSchemaResponse)
async def login(data: LoginSchema):
    logger.info("Login attempt: email={email}", email=data.email)
    try:
        user = await user_repository.get_user_by_email(data.email)
    except UserNotFoundError:
        logger.warning("Login failed: user not found: email={email}", email=data.email)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not await async_verify_password(data.password, user.hash_password):
        logger.warning("Login failed: invalid password: email={email}", email=data.email)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    logger.info("Login successful: user_id={user_id}, email={email}", 
               user_id=str(user.user_id), email=user.email)
    return await token_service.login_tokens(user=user)
