"""Корневой модуль API приложения.

Подключает маршрутизатор версии v1 по префиксу `/v1`.
"""

from fastapi import APIRouter

from source.api.v1 import router as v1_router

router = APIRouter()
router.include_router(v1_router, prefix="/v1")
