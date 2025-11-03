from typing import TypeVar, Generic, Type, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from source.db.session import get_async_session

ModelType = TypeVar('ModelType')

class BaseCRUD(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get_by_id(self, id_value: UUID, session: Optional[AsyncSession] = None) -> Optional[ModelType]:
        logger.debug("Getting {model} by id: id={id_value}", model=self.model.__name__, id_value=str(id_value))
        if session:
            result = await session.execute(
                select(self.model).where(self.model.id == id_value)
            )
            return result.scalar_one_or_none()
        
        async with get_async_session() as session:
            result = await session.execute(
                select(self.model).where(self.model.id == id_value)
            )
            return result.scalar_one_or_none()

    async def exists(self, id_value: UUID) -> bool:
        logger.debug("Checking if {model} exists: id={id_value}", model=self.model.__name__, id_value=str(id_value))
        async with get_async_session() as session:
            result = await session.execute(
                select(self.model).where(self.model.id == id_value)
            )
            exists = result.scalar_one_or_none() is not None
            logger.debug("{model} exists={exists}: id={id_value}", model=self.model.__name__, exists=exists, id_value=str(id_value))
            return exists

    async def delete(self, id_value: UUID) -> None:
        logger.info("Deleting {model}: id={id_value}", model=self.model.__name__, id_value=str(id_value))
        async with get_async_session() as session:
            result = await session.execute(
                select(self.model).where(self.model.id == id_value)
            )
            obj = result.scalar_one_or_none()
            if obj:
                await session.delete(obj)
                await session.commit()
                logger.info("{model} deleted: id={id_value}", model=self.model.__name__, id_value=str(id_value))
            else:
                logger.warning("{model} not found for deletion: id={id_value}", model=self.model.__name__, id_value=str(id_value))

