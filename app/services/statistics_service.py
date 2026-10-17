# ==============================
# Application imports
# ==============================

from app.repositories import StatisticsRepository
from app.schemas import (
    SourceStatisticsRead,
    StatisticsOverviewRead,
)


# ==============================
# Statistics service
# ==============================

class StatisticsService:
    """Provide vacancy statistics for the application."""

    def __init__(self, repository: StatisticsRepository) -> None:
        """Initialize the service with a statistics repository."""
        self.repository = repository

    # ==============================
    # Overview statistics
    # ==============================

    async def get_overview(self) -> StatisticsOverviewRead:
        """Return overall vacancy statistics."""
        data = await self.repository.get_overview()

        return StatisticsOverviewRead(**data)

    # ==============================
    # Statistics by source
    # ==============================

    async def get_by_source(self) -> list[SourceStatisticsRead]:
        """Return vacancy statistics grouped by source."""
        data = await self.repository.get_by_source()

        return [
            SourceStatisticsRead(**source)
            for source in data
        ]