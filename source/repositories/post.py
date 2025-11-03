from datetime import datetime
from uuid import UUID
from sqlalchemy import select, and_
from loguru import logger

from source.db.session import get_async_session
from source.models.post import Post
from source.core.exceptions import PostNotFoundError
from source.utils.datetime_utils import to_naive_utc, utcnow

class PostRepository:
    @classmethod
    async def _get_post_by_ids_in_session(cls, session, user_id: UUID, post_id: UUID) -> Post | None:
        result = await session.execute(
            select(Post).where(Post.user_id == user_id, Post.post_id == post_id)
        )
        return result.scalar_one_or_none()

    @classmethod
    async def _get_post_by_ids(cls, user_id: UUID, post_id: UUID) -> Post | None:
        async with get_async_session() as session:
            return await cls._get_post_by_ids_in_session(session, user_id, post_id)

    @classmethod
    async def _get_post_by_creation_id_in_session(cls, session, user_id: UUID, creation_id: str) -> Post | None:
        result = await session.execute(
            select(Post).where(
                Post.user_id == user_id,
                Post.instagram_creation_id == creation_id,
            )
        )
        return result.scalar_one_or_none()

    @classmethod
    async def _get_post_by_creation_id(cls, user_id: UUID, creation_id: str) -> Post | None:
        async with get_async_session() as session:
            return await cls._get_post_by_creation_id_in_session(session, user_id, creation_id)

    @classmethod
    async def create_post(
        cls,
        *,
        user_id: UUID,
        instagram_creation_id: str,
        caption: str,
        image_url: str,
    ) -> Post:
        logger.info("Creating post record for user_id={user_id}", user_id=str(user_id))
        async with get_async_session() as session:
            post = Post(
                user_id=user_id,
                instagram_creation_id=instagram_creation_id,
                caption=caption,
                image_url=image_url,
            )
            session.add(post)
            await session.commit()
            await session.refresh(post)
            return post

    @classmethod
    async def mark_published(cls, *, user_id: UUID, instagram_creation_id: str) -> None:
        logger.info("Marking post as published user_id={user_id} creation_id={creation_id}", 
                   user_id=str(user_id), creation_id=instagram_creation_id)
        async with get_async_session() as session:
            post = await cls._get_post_by_creation_id_in_session(session, user_id, instagram_creation_id)
            if not post:
                raise PostNotFoundError("Post not found")
            post.published_at = utcnow()
            await session.commit()
            await session.refresh(post)

    @classmethod
    async def get_post(cls, *, user_id: UUID, post_id: UUID) -> Post:
        post = await cls._get_post_by_ids(user_id, post_id)
        if not post:
            raise PostNotFoundError("Post not found")
        return post

    @classmethod
    async def list_posts(cls, *, user_id: UUID) -> list[Post]:
        async with get_async_session() as session:
            result = await session.execute(select(Post).where(Post.user_id == user_id))
            return list(result.scalars().all())

    @classmethod
    async def delete_post(cls, *, user_id: UUID, post_id: UUID) -> None:
        async with get_async_session() as session:
            post = await cls._get_post_by_ids_in_session(session, user_id, post_id)
            if not post:
                raise PostNotFoundError("Post not found")
            await session.delete(post)
            await session.commit()

    @classmethod
    async def get_posts_ready_to_publish(cls) -> list[Post]:
        logger.info("Fetching posts ready to publish")
        async with get_async_session() as session:
            now = utcnow()
            result = await session.execute(
                select(Post).where(
                    and_(
                        Post.time_to_publish <= now,
                        Post.published_at.is_(None)
                    )
                )
            )
            posts = list(result.scalars().all())
            logger.info("Found {count} posts ready to publish", count=len(posts))
            return posts

    @classmethod
    async def update_time_to_publish(cls, *, user_id: UUID, post_id: UUID, time_to_publish: datetime) -> Post:
        logger.info("Updating time_to_publish for post_id={post_id}, user_id={user_id}", 
                   post_id=str(post_id), user_id=str(user_id))
        async with get_async_session() as session:
            post = await cls._get_post_by_ids_in_session(session, user_id, post_id)
            if not post:
                raise PostNotFoundError("Post not found")
            post.time_to_publish = to_naive_utc(time_to_publish)
            await session.commit()
            await session.refresh(post)
            logger.info("Updated time_to_publish for post_id={post_id}", post_id=str(post_id))
            return post

post_repository = PostRepository()
