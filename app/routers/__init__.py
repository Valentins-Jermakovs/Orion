
from fastapi import APIRouter

from app.routers.health import router as health_router
from app.routers.jobs import router as jobs_router
from app.routers.sources import router as sources_router


# Create the main API router.
router = APIRouter()

# Register application routes.
router.include_router(health_router)
router.include_router(jobs_router)
router.include_router(sources_router)
