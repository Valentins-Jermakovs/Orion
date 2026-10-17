# ==============================
# Library imports
# ==============================

from redis.asyncio import Redis


# ==============================
# Application imports
# ==============================

from app.config.settings import settings


# ==============================
# Redis client
# ==============================

# Redis client is initialized during application startup.
redis: Redis | None = None


# ==============================
# Redis lifecycle
# ==============================

async def init_redis() -> None:
    """Initialize the Redis client using application settings."""
    global redis

    password = (
        settings.redis_password.get_secret_value()
        if settings.redis_password is not None
        else None
    )

    redis = Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        password=password,
        decode_responses=True,
    )


def get_redis() -> Redis:
    """Return the initialized Redis client."""
    if redis is None:
        raise RuntimeError("Redis has not been initialized.")

    return redis


async def close_redis() -> None:
    """Close the Redis connection and release the client."""
    global redis

    if redis is not None:
        await redis.aclose()
        redis = None
