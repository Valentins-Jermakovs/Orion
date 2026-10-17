# ==============================
# Standard library imports
# ==============================

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

# ==============================
# Third-party imports
# ==============================

from fastapi import FastAPI

# ==============================
# Application imports
# ==============================

from app.db import (
    close_database_connection,
    close_redis,
    init_db,
    init_redis,
)
from app.routers import router as api_router


# ==============================
# Application lifespan
# ==============================

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize and release application resources."""
    try:
        # Initialize application resources.
        await init_db()
        await init_redis()

        yield

    finally:
        # Close Redis and always dispose of the database engine.
        try:
            await close_redis()
        finally:
            await close_database_connection()


# ==============================
# FastAPI application
# ==============================

app = FastAPI(
    title="Orion",
    lifespan=lifespan,
)

# Register application routes.
app.include_router(api_router)
