from loguru import logger
from uuid import UUID

from source.models.wiki_context import Wikibase
from source.schemas.wiki_context import CreateWikibaseContext
from source.repositories.base_context import BaseContextRepository
from source.core.exceptions import WikibaseContextNotFoundError, WikibaseContextAlreadyExistsError

class WikiContextRepository(BaseContextRepository[Wikibase]):
    def __init__(self):
        super().__init__(
            model=Wikibase,
            not_found_error=WikibaseContextNotFoundError,
            already_exists_error=WikibaseContextAlreadyExistsError
        )

    async def get_context(self, user_id: UUID) -> Wikibase | None:
        logger.info("Fetching Wikibase context for user_id={user_id}", user_id=str(user_id))
        return await super().get_context(user_id)

    async def create_context(self, user_id: UUID, data: CreateWikibaseContext) -> None:
        logger.info("Creating Wikibase context for user_id={user_id}", user_id=str(user_id))
        await super().create_context(user_id, data.content)
        logger.info("Wikibase context created for user_id={user_id}", user_id=str(user_id))

    async def update_context(self, user_id: UUID, data: CreateWikibaseContext) -> None:
        logger.info("Updating Wikibase context for user_id={user_id}", user_id=str(user_id))
        await super().update_context(user_id, data.content)
        logger.info("Wikibase context updated for user_id={user_id}", user_id=str(user_id))

    async def delete_context(self, user_id: UUID) -> None:
        logger.info("Deleting Wikibase context for user_id={user_id}", user_id=str(user_id))
        await super().delete_context(user_id)
        logger.info("Wikibase context deleted for user_id={user_id}", user_id=str(user_id))

wiki_context_repository = WikiContextRepository()
