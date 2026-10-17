# ==============================
# Third-party imports
# ==============================

from fastapi import APIRouter

# ==============================
# Application routers
# ==============================

from app.routers.health import router as health_router
from app.routers.jobs import router as jobs_router
from app.routers.sources import router as sources_router
from app.routers.statistics import router as statistics_router


# ==============================
# Main API router
# ==============================

router = APIRouter()

# Register application endpoints.
router.include_router(health_router)
router.include_router(jobs_router)
router.include_router(sources_router)
router.include_router(statistics_router)