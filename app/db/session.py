
# ==============================
# Library imports
# ==============================

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession


# ==============================
# Application imports
# ==============================

from app.config import settings
from app.models import Job  # noqa: F401


# ==============================
# Database configuration
# ==============================

# Build the PostgreSQL connection URL from application settings.
# URL.create safely handles special characters in the password.
DATABASE_URL = URL.create(
    drivername="postgresql+asyncpg",
    username=settings.postgres_user,
    password=settings.postgres_password.get_secret_value(),
    host=settings.postgres_host,
    port=settings.postgres_port,
    database=settings.postgres_db,
)


# ==============================
# Database engine
# ==============================

# Create the asynchronous database engine.
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)


# ==============================
# Database session
# ==============================

# Create a factory for asynchronous SQLModel sessions.
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ==============================
# Database dependencies
# ==============================

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an asynchronous database session."""
    async with async_session_factory() as session:
        yield session


# ==============================
# Database initialization
# ==============================

async def init_db() -> None:
    """Create all database tables registered in SQLModel metadata."""
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)


# ==============================
# Database health check
# ==============================

async def check_database_connection() -> bool:
    """Check whether PostgreSQL is reachable."""
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))

    return True


# ==============================
# Database shutdown
# ==============================

async def close_database_connection() -> None:
    """Dispose of the database connection pool."""
    await engine.dispose()
