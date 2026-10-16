import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlmodel import SQLModel

from app.config.logging_config import configure_logging
from app.config.settings import settings
from app.db.redis import close_redis_connection, init_redis
from app.db.session import close_database_connection, engine
from app.models.job import Job  # noqa: F401
from app.routers.health import router as health_router
from app.routers.jobs import router as jobs_router
from app.routers.sources import router as sources_router


configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown."""
    try:
        logger.info("Initializing database")

        async with engine.begin() as connection:
            await connection.run_sync(SQLModel.metadata.create_all)

        logger.info("Database initialized successfully")

        await init_redis()

        logger.info("Redis initialized successfully")
        logger.info("Application started successfully")

        yield

    except Exception:
        logger.exception("Application lifecycle error")
        raise

    finally:
        logger.info("Shutting down application")

        try:
            await close_redis_connection()
        finally:
            await close_database_connection()

        logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Job aggregation service.",
    lifespan=lifespan,
)

# Health endpoints: /health and /health/ready
app.include_router(health_router)

# Job endpoints: /api/v1/jobs and /api/v1/jobs/{job_id}
app.include_router(
    jobs_router,
    prefix=settings.api_v1_prefix,
)

# Source endpoints: /api/v1/sources/scrape
app.include_router(
    sources_router,
    prefix=settings.api_v1_prefix,
)