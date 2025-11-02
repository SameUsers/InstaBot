import contextlib
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from source.conf import settings

@contextlib.asynccontextmanager
async def get_async_session():
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
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
            await async_engine.dispose()