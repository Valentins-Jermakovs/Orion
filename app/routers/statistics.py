# ==============================
# Third-party imports
# ==============================

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

# ==============================
# Application imports
# ==============================

from app.db import get_session
from app.facades import StatisticsFacade
from app.schemas import (
    SourceStatisticsRead,
    StatisticsOverviewRead,
)


# ==============================
# Router configuration
# ==============================

router = APIRouter(
    prefix="/statistics",
    tags=["Statistics"],
)


# ==============================
# Overview statistics
# ==============================

@router.get(
    "/overview",
    response_model=StatisticsOverviewRead,
)
async def get_statistics_overview(
    session: AsyncSession = Depends(get_session),
) -> StatisticsOverviewRead:
    """Return overall vacancy statistics."""
    facade = StatisticsFacade(session)

    return await facade.get_overview()


# ==============================
# Statistics by source
# ==============================

@router.get(
    "/sources",
    response_model=list[SourceStatisticsRead],
)
async def get_statistics_by_source(
    session: AsyncSession = Depends(get_session),
) -> list[SourceStatisticsRead]:
    """Return vacancy statistics grouped by source."""
    facade = StatisticsFacade(session)

    return await facade.get_by_source()