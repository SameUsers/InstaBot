from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
import jwt

from source.conf import settings
from source.core.constants import AccessTokenRows
from source.schemas.auth import CurrentUserSchema

security = HTTPBearer(auto_error=False)

class AuthProvider:
    @classmethod
    def _validate_credentials(cls, credentials: HTTPAuthorizationCredentials) -> None:
        if not credentials:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"}
            )
        if credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid auth scheme",
                headers={"WWW-Authenticate": "Bearer"}
            )

    @classmethod
    def _decode_token(cls, token: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                settings.access_token_secret,
                algorithms=[settings.code_algorithm]
            )
            logger.info("Access token decoded successfully")
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Access token expired")
            raise HTTPException(
                status_code=401,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.InvalidTokenError:
            logger.warning("Access token invalid")
            raise HTTPException(
                status_code=401,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )

    @classmethod
    def _extract_user_data(cls, payload: dict) -> CurrentUserSchema:
        user_id = payload.get(AccessTokenRows.sub)
        email = payload.get(AccessTokenRows.sub_email)
        username = payload.get(AccessTokenRows.username)
        permissions = payload.get(AccessTokenRows.permissions)

        if not user_id or not email:
            logger.warning("Token payload missing required claims: sub/email")
            raise HTTPException(status_code=401, detail="Invalid token payload")

        return CurrentUserSchema(
            user_id=user_id,
            email=email,
            username=username or "",
            permissions=permissions or ""
        )

    @classmethod
    async def get_current_user(
        cls,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> CurrentUserSchema:
        cls._validate_credentials(credentials)
        token = credentials.credentials
        payload = cls._decode_token(token)
        return cls._extract_user_data(payload)

current_user = AuthProvider.get_current_user