from sqlalchemy import select
from uuid import UUID
from loguru import logger

from source.db.session import get_async_session
from source.models.user import User
from source.schemas.auth import RegistrationSchema
from source.schemas.user import UserSchema, UserOutputSchema
from source.core.exceptions import UserAlreadyExistsError, UserNotFoundError

class UserRepository:
    @staticmethod
    def _to_user_schema(user: User) -> UserSchema:
        return UserSchema(
            user_id=str(user.user_id),
            email=user.email,
            username=user.username,
            permissions=user.permissions,
            hash_password=user.hash_password,
            refresh_token_version=user.refresh_token_version,
            created_at=user.created_at
        )

    @staticmethod
    def _to_user_output_schema(user: User) -> UserOutputSchema:
        return UserOutputSchema(
            user_id=str(user.user_id),
            email=user.email,
            username=user.username,
            permissions=user.permissions,
            created_at=user.created_at
        )

    @classmethod
    async def _check_email_exists(cls, email: str) -> bool:
        async with get_async_session() as session:
            result = await session.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none() is not None

    @classmethod
    async def _get_user_by_email_from_db(cls, email: str) -> User | None:
        async with get_async_session() as session:
            result = await session.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()

    @classmethod
    async def create_user(cls, data: RegistrationSchema, hash_password: str) -> UserSchema:
        logger.info("Creating user with email={email}", email=data.email)
        if await cls._check_email_exists(data.email):
            raise UserAlreadyExistsError("User with this email already exists")

        async with get_async_session() as session:
            user = User(
                email=data.email,
                username=data.username,
                hash_password=hash_password,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return cls._to_user_schema(user)

    @classmethod
    async def check_user_exists(cls, user_email: str) -> bool:
        logger.info("Checking if user exists by email={email}", email=user_email)
        return await cls._check_email_exists(user_email)

    @classmethod
    async def get_user_by_email(cls, user_email: str) -> UserSchema:
        logger.info("Fetching user by email={email}", email=user_email)
        user = await cls._get_user_by_email_from_db(user_email)
        if not user:
            raise UserNotFoundError("User not found")
        return cls._to_user_schema(user)

    @classmethod
    async def _get_user_by_id_from_db(cls, user_id: UUID) -> User | None:
        async with get_async_session() as session:
            result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            return result.scalar_one_or_none()

    @classmethod
    async def get_user_by_id(cls, user_id: UUID) -> UserSchema:
        logger.info("Fetching user by id={user_id}", user_id=str(user_id))
        user = await cls._get_user_by_id_from_db(user_id)
        if not user:
            raise UserNotFoundError("User not found")
        return cls._to_user_schema(user)

    @classmethod
    async def get_refresh_version(cls, user_id: UUID) -> int:
        logger.info("Getting refresh_token_version for user_id={user_id}", user_id=str(user_id))
        async with get_async_session() as session:
            result = await session.execute(
                select(User.refresh_token_version).where(
                    User.user_id == user_id
                )
            )
            version = result.scalar_one_or_none()
            if version is None:
                raise UserNotFoundError("User not found")
            return version

    @classmethod
    async def increment_token_version(cls, user_id: UUID) -> None:
        logger.info("Incrementing refresh_token_version for user_id={user_id}", user_id=str(user_id))
        async with get_async_session() as session:
            result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                raise UserNotFoundError(f"User with id {user_id} not found")
            user.refresh_token_version += 1
            await session.commit()
            await session.refresh(user)

user_repository = UserRepository()