
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config.settings import settings


engine = create_async_engine(
    settings.database_url.get_secret_value(),
    echo=settings.environment == "development",
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an asynchronous SQLModel session."""
    async with async_session_factory() as session:
        yield session


async def check_database_connection() -> bool:
    """Check whether PostgreSQL is reachable."""
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))

    return True


async def close_database_connection() -> None:
    """Dispose of the database connection pool."""
    await engine.dispose()
