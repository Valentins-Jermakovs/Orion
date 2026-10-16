
from redis.asyncio import Redis

from app.config.settings import settings


redis_client: Redis | None = None


async def init_redis() -> Redis:
    """Initialize Redis and verify the connection."""
    global redis_client

    client = Redis.from_url(
        settings.redis_url.get_secret_value(),
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )

    try:
        await client.ping()
    except Exception:
        await client.aclose()
        raise

    redis_client = client
    return client


def get_redis() -> Redis:
    """Return the initialized Redis client."""
    if redis_client is None:
        raise RuntimeError("Redis has not been initialized.")

    return redis_client


async def close_redis_connection() -> None:
    """Close the Redis connection."""
    global redis_client

    if redis_client is not None:
        await redis_client.aclose()
        redis_client = None
