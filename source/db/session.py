import contextlib
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from loguru import logger

from source.conf import settings

@contextlib.asynccontextmanager
async def get_async_session():
    logger.debug("Creating database session")
    async_engine = create_async_engine(settings.db_url, poolclass=NullPool)
    AsyncSessionLocal = async_sessionmaker(
        bind=async_engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False
    )
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
            logger.debug("Database session committed successfully")
        except Exception as exc:
            logger.exception("Database session error, rolling back: {error}", error=str(exc))
            await session.rollback()
            raise
        finally:
            await session.close()
            await async_engine.dispose()
            logger.debug("Database session closed")