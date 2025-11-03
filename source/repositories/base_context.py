from uuid import UUID
from sqlalchemy import select
from typing import Optional, TypeVar, Type, Generic
from loguru import logger

from source.db.session import get_async_session

ModelType = TypeVar('ModelType')

class BaseContextRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], not_found_error: type[Exception], already_exists_error: type[Exception]):
        self.model = model
        self.not_found_error = not_found_error
        self.already_exists_error = already_exists_error

    async def get_context(self, user_id: UUID) -> Optional[ModelType]:
        async with get_async_session() as session:
            result = await session.execute(
                select(self.model).where(self.model.user_id == user_id)
            )
            return result.scalar_one_or_none()

    async def create_context(self, user_id: UUID, content: str) -> None:
        logger.debug("Creating {model} context for user_id={user_id}", model=self.model.__name__, user_id=str(user_id))
        async with get_async_session() as session:
            existing = await session.execute(
                select(self.model).where(self.model.user_id == user_id)
            )
            if existing.scalar_one_or_none():
                logger.warning("{model} context already exists for user_id={user_id}", model=self.model.__name__, user_id=str(user_id))
                raise self.already_exists_error("Context already exists for this user")
            
            obj = self.model(user_id=user_id, content=content)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            logger.debug("{model} context created for user_id={user_id}", model=self.model.__name__, user_id=str(user_id))

    async def update_context(self, user_id: UUID, content: str) -> None:
        logger.debug("Updating {model} context for user_id={user_id}", model=self.model.__name__, user_id=str(user_id))
        async with get_async_session() as session:
            result = await session.execute(
                select(self.model).where(self.model.user_id == user_id)
            )
            obj = result.scalar_one_or_none()
            if not obj:
                logger.warning("{model} context not found for user_id={user_id}", model=self.model.__name__, user_id=str(user_id))
                raise self.not_found_error("Context not found for this user")
            obj.content = content
            await session.commit()
            await session.refresh(obj)
            logger.debug("{model} context updated for user_id={user_id}", model=self.model.__name__, user_id=str(user_id))

    async def delete_context(self, user_id: UUID) -> None:
        logger.debug("Deleting {model} context for user_id={user_id}", model=self.model.__name__, user_id=str(user_id))
        async with get_async_session() as session:
            result = await session.execute(
                select(self.model).where(self.model.user_id == user_id)
            )
            obj = result.scalar_one_or_none()
            if not obj:
                logger.warning("{model} context not found for user_id={user_id}", model=self.model.__name__, user_id=str(user_id))
                raise self.not_found_error("Context not found for this user")
            await session.delete(obj)
            await session.commit()
            logger.debug("{model} context deleted for user_id={user_id}", model=self.model.__name__, user_id=str(user_id))

