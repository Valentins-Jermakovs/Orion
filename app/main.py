
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI


from app.db.redis import close_redis, init_redis
from app.db.session import close_database_connection, init_db

from app.routers import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown."""
    try:
        # Initialize database.
        await init_db()

        # Initialize the Redis connection.
        await init_redis()

        yield

    finally:
        # Close application resources during shutdown.
        try:
            await close_redis()
        finally:
            await close_database_connection()


app = FastAPI(
    title="Orion",
    lifespan=lifespan,
)

# Register all application routes.
app.include_router(api_router)
