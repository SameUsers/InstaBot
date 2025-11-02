"""Маршруты API версии v1.

Содержит набор роутеров: авторизация, пользователи, сервис Instagram и Wikibase.
"""

from fastapi import APIRouter

from source.api.v1.auth import router as auth_router
from source.api.v1.user import router as user_router
from source.api.v1.instagram import router as instagram_router
from source.api.v1.wiki_context import router as wiki_context_router
from source.api.v1.post_context import router as post_context_router
from source.api.v1.post import router as post_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(user_router, prefix="/user", tags=["user"])
router.include_router(instagram_router, prefix="/botservice", tags=["instagram"])
router.include_router(wiki_context_router, prefix="/wikibase", tags=["wikibase"])
router.include_router(post_context_router, prefix="/postbase", tags=["postbase"])
router.include_router(post_router, prefix="/posts", tags=["posts"])