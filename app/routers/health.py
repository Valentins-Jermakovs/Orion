
# ==============================
# Third-party imports
# ==============================

from fastapi import APIRouter, Depends, HTTPException

# ==============================
# Application imports
# ==============================

from app.db import check_database_connection, get_redis
from app.routers.dependencies import jwt_auth


# ==============================
# Health router
# ==============================

router = APIRouter(
    tags=["Health"],
)


# ==============================
# Public health check
# ==============================

@router.get("/health")
async def health_check(
    admin: dict = Depends(jwt_auth.require_roles(["admin"])),
) -> dict[str, str]:
    """Check whether the API is running."""
    return {"status": "ok"}


# ==============================
# Administrator readiness check
# ==============================

@router.get("/health/ready")
async def readiness_check(
    admin: dict = Depends(jwt_auth.require_roles(["admin"])),
) -> dict[str, str]:
    """Check whether application dependencies are available."""
    try:
        await check_database_connection()
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable.",
        ) from None

    try:
        await get_redis().ping()
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Redis is unavailable.",
        ) from None

    return {
        "status": "ready",
        "database": "ok",
        "redis": "ok",
    }
