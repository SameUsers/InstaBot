import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from source.api import router
from source.schemas.healthcheck import HealthCheckSchema
from source.services.post_publisher import post_publish_service


async def background_post_publisher():
    try:
        await post_publish_service.publish_pending_posts()
    except Exception as exc:
        logger.exception("Error in background_post_publisher: {error}", error=str(exc))
    
    while True:
        await asyncio.sleep(600)
        try:
            await post_publish_service.publish_pending_posts()
        except Exception as exc:
            logger.exception("Error in background_post_publisher: {error}", error=str(exc))


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting background post publisher task")
    task = asyncio.create_task(background_post_publisher())
    yield
    logger.info("Stopping background post publisher task")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Asmanta Multibot API",
    docs_url="/docs",
    lifespan=lifespan,
    swagger_ui_parameters={
        "displayRequestDuration": True,
        "filter": True,
        "deepLinking": True,
        "displayOperationId": True,
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@router.get("/", response_model=HealthCheckSchema, tags=["health"])
def health() -> HealthCheckSchema:
    return HealthCheckSchema()


app.include_router(router)
