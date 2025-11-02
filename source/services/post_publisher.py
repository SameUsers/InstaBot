from loguru import logger

from source.models.post import Post
from source.repositories.post import post_repository
from source.repositories.instagram import instagram_repository
from source.services.instagram import Publisher

class PostPublishService:
    @classmethod
    async def _publish_single_post(cls, post: Post) -> None:
        logger.info(
            "Publishing post post_id={post_id}, user_id={user_id}, creation_id={creation_id}",
            post_id=str(post.post_id),
            user_id=str(post.user_id),
            creation_id=post.instagram_creation_id
        )
        
        credentials = await instagram_repository.get_instagram_credentials(post.user_id)
        if not credentials:
            logger.warning(
                "Instagram credentials not found for user_id={user_id}, skipping post post_id={post_id}",
                user_id=str(post.user_id),
                post_id=str(post.post_id)
            )
            return
        
        await Publisher.publish_media(
            inst_id=credentials.instagram_id,
            inst_token=credentials.instagram_token,
            creation_id=post.instagram_creation_id,
        )
        
        await post_repository.mark_published(
            user_id=post.user_id,
            instagram_creation_id=post.instagram_creation_id
        )
        
        logger.info("Successfully published post post_id={post_id}", post_id=str(post.post_id))

    @classmethod
    async def publish_pending_posts(cls) -> None:
        logger.info("Starting to publish pending posts")
        try:
            posts = await post_repository.get_posts_ready_to_publish()
            
            if not posts:
                logger.info("No posts ready to publish")
                return
            
            logger.info("Found {count} posts to publish", count=len(posts))
            
            for post in posts:
                try:
                    await cls._publish_single_post(post)
                except Exception as exc:
                    logger.exception(
                        "Failed to publish post post_id={post_id}, user_id={user_id}: {error}",
                        post_id=str(post.post_id),
                        user_id=str(post.user_id),
                        error=str(exc)
                    )
        except Exception as exc:
            logger.exception("Error in publish_pending_posts: {error}", error=str(exc))

post_publish_service = PostPublishService()
