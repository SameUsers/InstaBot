from sqlalchemy import select
from loguru import logger
from uuid import UUID

from source.db.session import get_async_session
from source.models.instagram import InstagramCredentials
from source.schemas.instagram import CreateInstagramCredentials
from source.core.exceptions import InstagramCredsAlreadyExistsError, InstagramCredsNotFoundError

class InstagramRepository:
    @classmethod
    async def _get_credentials_by_user_id(cls, user_id: UUID) -> InstagramCredentials | None:
        async with get_async_session() as session:
            result = await session.execute(
                select(InstagramCredentials).where(
                    InstagramCredentials.user_id == user_id
                )
            )
            return result.scalar_one_or_none()

    @classmethod
    async def _credentials_exist(cls, user_id: UUID) -> bool:
        return await cls._get_credentials_by_user_id(user_id) is not None

    @classmethod
    async def create_instagram_credentials(cls, data: CreateInstagramCredentials, user_id: UUID) -> None:
        logger.info("Creating Instagram credentials for user_id={user_id}", user_id=str(user_id))
        if await cls._credentials_exist(user_id):
            raise InstagramCredsAlreadyExistsError("Instagram credentials already exist for this user")
        
        async with get_async_session() as session:
            credentials = InstagramCredentials(
                user_id=user_id,
                instagram_id=data.instagram_id,
                instagram_token=data.instagram_token
            )
            session.add(credentials)
            await session.commit()
            await session.refresh(credentials)
        logger.info("Instagram credentials created for user_id={user_id}", user_id=str(user_id))

    @classmethod
    async def get_instagram_credentials(cls, user_id: UUID) -> InstagramCredentials | None:
        logger.info("Fetching Instagram credentials for user_id={user_id}", user_id=str(user_id))
        return await cls._get_credentials_by_user_id(user_id)

    @classmethod
    async def update_instagram_credentials(cls, user_id: UUID, data: CreateInstagramCredentials) -> None:
        logger.info("Updating Instagram credentials for user_id={user_id}", user_id=str(user_id))
        async with get_async_session() as session:
            result = await session.execute(
                select(InstagramCredentials).where(
                    InstagramCredentials.user_id == user_id
                )
            )
            credentials = result.scalar_one_or_none()
            if not credentials:
                raise InstagramCredsNotFoundError("Instagram credentials not found for this user")
            credentials.instagram_id = data.instagram_id
            credentials.instagram_token = data.instagram_token
            await session.commit()
            await session.refresh(credentials)
        logger.info("Instagram credentials updated for user_id={user_id}", user_id=str(user_id))

    @classmethod
    async def delete_instagram_credentials(cls, user_id: UUID) -> None:
        logger.info("Deleting Instagram credentials for user_id={user_id}", user_id=str(user_id))
        async with get_async_session() as session:
            result = await session.execute(
                select(InstagramCredentials).where(
                    InstagramCredentials.user_id == user_id
                )
            )
            credentials = result.scalar_one_or_none()
            if not credentials:
                raise InstagramCredsNotFoundError("Instagram credentials not found for this user")
            await session.delete(credentials)
            await session.commit()
        logger.info("Instagram credentials deleted for user_id={user_id}", user_id=str(user_id))

    @classmethod
    async def get_user_id_by_instagram_id(cls, instagram_id: int) -> UUID | None:
        logger.info("Resolving user_id by instagram_id={instagram_id}", instagram_id=instagram_id)
        async with get_async_session() as session:
            result = await session.execute(
                select(InstagramCredentials).where(
                    InstagramCredentials.instagram_id == instagram_id
                )
            )
            row = result.scalar_one_or_none()
            return row.user_id if row else None

instagram_repository = InstagramRepository()