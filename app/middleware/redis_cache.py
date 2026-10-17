
# ==============================
# Standard library imports
# ==============================

import hashlib
import logging

# ==============================
# Third-party imports
# ==============================

from redis.exceptions import RedisError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

# ==============================
# Application imports
# ==============================

from app.db import get_redis


# ==============================
# Cache configuration
# ==============================

logger = logging.getLogger(__name__)

CACHE_PREFIX = "orion:api-cache:"
CACHE_TTL_SECONDS = 60

CACHEABLE_PATHS = {
    "/jobs",
    "/statistics/overview",
    "/statistics/sources",
}


# ==============================
# Redis cache middleware
# ==============================

class RedisCacheMiddleware(BaseHTTPMiddleware):
    """Cache selected GET responses in Redis."""

    def __init__(
        self,
        app: ASGIApp,
        ttl_seconds: int = CACHE_TTL_SECONDS,
    ) -> None:
        """Initialize the middleware with a cache lifetime."""
        super().__init__(app)
        self.ttl_seconds = ttl_seconds

    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:
        """Serve cached responses and invalidate the cache after writes."""
        # Invalidate cached responses after requests that may modify data.
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            response = await call_next(request)
            await self._invalidate_cache()
            return response

        # Do not cache health checks, documentation, or unrelated routes.
        if (
            request.method != "GET"
            or not self._is_cacheable_path(request.url.path)
        ):
            return await call_next(request)

        cache_key = self._create_cache_key(request)

        # Return a cached response when Redis contains one.
        try:
            redis_client = get_redis()
            cached_body = await redis_client.get(cache_key)
        except (RedisError, RuntimeError):
            logger.warning(
                "Could not read the Redis cache.",
                exc_info=True,
            )
            cached_body = None

        if cached_body is not None:
            return Response(
                content=cached_body,
                status_code=200,
                media_type="application/json",
                headers={"X-Cache": "HIT"},
            )

        # Execute the request normally on a cache miss.
        response = await call_next(request)

        content_type = response.headers.get("content-type", "")

        # Cache only successful JSON responses.
        if (
            response.status_code != 200
            or not content_type.startswith("application/json")
        ):
            response.headers["X-Cache"] = "BYPASS"
            return response

        # Read the response body so it can be stored in Redis.
        body = b"".join(
            [chunk async for chunk in response.body_iterator]
        )

        try:
            await get_redis().set(
                cache_key,
                body.decode("utf-8"),
                ex=self.ttl_seconds,
            )
        except (RedisError, RuntimeError):
            # Redis failures must not prevent the API response.
            logger.warning(
                "Could not write the Redis cache.",
                exc_info=True,
            )

        # Preserve the original response headers and background task.
        headers = dict(response.headers)
        headers.pop("content-length", None)
        headers.pop("transfer-encoding", None)
        headers["X-Cache"] = "MISS"

        return Response(
            content=body,
            status_code=response.status_code,
            headers=headers,
            background=response.background,
        )

    # ==============================
    # Cache helpers
    # ==============================

    @staticmethod
    def _is_cacheable_path(path: str) -> bool:
        """Check whether the requested endpoint supports caching."""
        if path in CACHEABLE_PATHS:
            return True

        # Cache individual vacancy endpoints such as /jobs/{job_id}.
        if path.startswith("/jobs/"):
            job_id = path.removeprefix("/jobs/")
            return bool(job_id) and "/" not in job_id

        return False

    @staticmethod
    def _create_cache_key(request: Request) -> str:
        """Create a unique cache key for the path and query parameters."""
        request_data = f"{request.url.path}?{request.url.query}"
        digest = hashlib.sha256(
            request_data.encode("utf-8")
        ).hexdigest()

        return f"{CACHE_PREFIX}{digest}"

    async def _invalidate_cache(self) -> None:
        """Delete cached API responses after a write request."""
        try:
            redis_client = get_redis()
            keys: list[str] = []

            async for key in redis_client.scan_iter(
                match=f"{CACHE_PREFIX}*"
            ):
                keys.append(key)

                # Delete keys in batches to limit command size.
                if len(keys) >= 100:
                    await redis_client.delete(*keys)
                    keys.clear()

            if keys:
                await redis_client.delete(*keys)

            logger.debug("Redis API cache invalidated.")

        except (RedisError, RuntimeError):
            logger.warning(
                "Could not invalidate the Redis API cache.",
                exc_info=True,
            )
