import jwt
from datetime import datetime, timedelta, timezone
from uuid import UUID
from typing import Any, Dict

from source.conf import settings
from source.schemas.auth import RegistrationSchemaResponse, RefreshResponseSchema
from source.core.constants import AccessTokenRows, RefreshTokenRows
from source.core.exceptions import TokenServiceError, InvalidTokenVersionError
from source.repositories.user import user_repository

class TokenService:
    @staticmethod
    def _generate_access_token(user_id: UUID, email: str, username: str, permissions: str) -> str:
        now = datetime.now(timezone.utc)
        payload: Dict[str, Any] = {
            AccessTokenRows.sub: str(user_id),
            AccessTokenRows.sub_email: email,
            AccessTokenRows.username: username,
            AccessTokenRows.permissions: permissions,
            AccessTokenRows.exp: int((now + timedelta(minutes=settings.access_token_exp)).timestamp())
        }
        return jwt.encode(payload, settings.access_token_secret, algorithm=settings.code_algorithm)

    @staticmethod
    def _generate_refresh_token(user_id: UUID, token_version: int) -> str:
        now = datetime.now(timezone.utc)
        payload: Dict[str, Any] = {
            RefreshTokenRows.sub: str(user_id),
            RefreshTokenRows.token_version: token_version,
            RefreshTokenRows.exp: int((now + timedelta(days=settings.refresh_token_exp)).timestamp())
        }
        return jwt.encode(payload, settings.refresh_token_secret, algorithm=settings.code_algorithm)

    @classmethod
    async def register_tokens(
        cls,
        *,
        email: str,
        username: str,
        user_id: UUID,
        permissions: str,
        refresh_token_version: int
    ) -> RegistrationSchemaResponse:
        access_token = cls._generate_access_token(user_id, email, username, permissions)
        refresh_token = cls._generate_refresh_token(user_id, refresh_token_version)
        return RegistrationSchemaResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )

    @classmethod
    async def login_tokens(cls, *, user) -> RegistrationSchemaResponse:
        return await cls.register_tokens(
            email=user.email,
            username=user.username,
            user_id=user.user_id,
            permissions=user.permissions,
            refresh_token_version=user.refresh_token_version
        )

    @staticmethod
    def _decode_refresh_token(refresh_token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(
                refresh_token, settings.refresh_token_secret, algorithms=[settings.code_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise TokenServiceError("Refresh token expired")
        except jwt.InvalidTokenError:
            raise TokenServiceError("Invalid refresh token")

    @staticmethod
    def _extract_token_data(payload: Dict[str, Any]) -> tuple[str, int]:
        user_id = payload.get(RefreshTokenRows.sub)
        token_version = payload.get(RefreshTokenRows.token_version)
        if not user_id or token_version is None:
            raise TokenServiceError("Payload missing fields")
        return user_id, token_version

    @staticmethod
    def _validate_token_version(token_version: int, db_token_version: int) -> None:
        if token_version != db_token_version:
            raise InvalidTokenVersionError("Refresh token is expired or invalid")

    @classmethod
    async def refresh(
        cls,
        refresh_token: str,
        increment_token_version: bool = True
    ) -> RefreshResponseSchema:
        payload = cls._decode_refresh_token(refresh_token)
        user_id_str, token_version = cls._extract_token_data(payload)
        user_id = UUID(user_id_str)
        
        db_token_version = await user_repository.get_refresh_version(user_id)
        cls._validate_token_version(token_version, db_token_version)
        
        user = await user_repository.get_user_by_id(user_id)
        access_token = cls._generate_access_token(
            user_id=user_id,
            email=user.email,
            username=user.username,
            permissions=user.permissions
        )
        
        new_token_version = db_token_version
        if increment_token_version:
            await user_repository.increment_token_version(user_id)
            new_token_version += 1
        
        updated_refresh_token = cls._generate_refresh_token(user_id, new_token_version)
        return RefreshResponseSchema(
            access_token=access_token,
            refresh_token=updated_refresh_token
        )

token_service = TokenService()