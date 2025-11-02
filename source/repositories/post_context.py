from loguru import logger
from uuid import UUID

from source.models.post_context import PostBase
from source.repositories.base_context import BaseContextRepository
from source.core.exceptions import PostBaseContextNotFoundError, PostBaseContextAlreadyExistsError

class PostContextRepository(BaseContextRepository[PostBase]):
    def __init__(self):
        super().__init__(
            model=PostBase,
            not_found_error=PostBaseContextNotFoundError,
            already_exists_error=PostBaseContextAlreadyExistsError
        )

    async def get_context(self, user_id: UUID) -> PostBase | None:
        logger.info("Fetching PostBase context for user_id={user_id}", user_id=str(user_id))
        return await super().get_context(user_id)

    async def create_context(self, user_id: UUID, content: str) -> None:
        logger.info("Creating PostBase context for user_id={user_id}", user_id=str(user_id))
        await super().create_context(user_id, content)
        logger.info("PostBase context created for user_id={user_id}", user_id=str(user_id))

    async def update_context(self, user_id: UUID, content: str) -> None:
        logger.info("Updating PostBase context for user_id={user_id}", user_id=str(user_id))
        await super().update_context(user_id, content)
        logger.info("PostBase context updated for user_id={user_id}", user_id=str(user_id))

    async def delete_context(self, user_id: UUID) -> None:
        logger.info("Deleting PostBase context for user_id={user_id}", user_id=str(user_id))
        await super().delete_context(user_id)
        logger.info("PostBase context deleted for user_id={user_id}", user_id=str(user_id))

post_context_repository = PostContextRepository()
