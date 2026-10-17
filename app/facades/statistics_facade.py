# ==============================
# Third-party imports
# ==============================

from sqlmodel.ext.asyncio.session import AsyncSession

# ==============================
# Application imports
# ==============================

from app.repositories import StatisticsRepository
from app.schemas import (
    SourceStatisticsRead,
    StatisticsOverviewRead,
)
from app.services import StatisticsService


# ==============================
# Statistics facade
# ==============================

class StatisticsFacade:
    """Provide a unified interface for vacancy statistics."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the statistics service and repository."""
        self.repository = StatisticsRepository(session)
        self.service = StatisticsService(self.repository)

    # ==============================
    # Overview statistics
    # ==============================

    async def get_overview(self) -> StatisticsOverviewRead:
        """Return overall vacancy statistics."""
        return await self.service.get_overview()

    # ==============================
    # Statistics by source
    # ==============================

    async def get_by_source(self) -> list[SourceStatisticsRead]:
        """Return vacancy statistics grouped by source."""
        return await self.service.get_by_source()