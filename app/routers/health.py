from fastapi import APIRouter, HTTPException, status

from app.db.redis import get_redis
from app.db.session import check_database_connection


router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Check whether the API is running."""
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness_check() -> dict[str, str]:
    """Check whether the application dependencies are available."""

    try:
        await check_database_connection()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from None

    try:
        await get_redis().ping()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis is unavailable.",
        ) from None

    return {
        "status": "ready",
        "database": "ok",
        "redis": "ok",
    }