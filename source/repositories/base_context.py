from uuid import UUID
from sqlalchemy import select
from typing import Optional, TypeVar, Type, Generic

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
        async with get_async_session() as session:
            existing = await session.execute(
                select(self.model).where(self.model.user_id == user_id)
            )
            if existing.scalar_one_or_none():
                raise self.already_exists_error("Context already exists for this user")
            
            obj = self.model(user_id=user_id, content=content)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)

    async def update_context(self, user_id: UUID, content: str) -> None:
        async with get_async_session() as session:
            result = await session.execute(
                select(self.model).where(self.model.user_id == user_id)
            )
            obj = result.scalar_one_or_none()
            if not obj:
                raise self.not_found_error("Context not found for this user")
            obj.content = content
            await session.commit()
            await session.refresh(obj)

    async def delete_context(self, user_id: UUID) -> None:
        async with get_async_session() as session:
            result = await session.execute(
                select(self.model).where(self.model.user_id == user_id)
            )
            obj = result.scalar_one_or_none()
            if not obj:
                raise self.not_found_error("Context not found for this user")
            await session.delete(obj)
            await session.commit()

