
# ==============================
# Library imports
# ==============================

from sqlmodel.ext.asyncio.session import AsyncSession


# ==============================
# Application imports
# ==============================

from app.scrapers import ScrapeResult
from app.services.scraper_service import ScraperService


# ==============================
# Scraper facade
# ==============================

class ScraperFacade:
    """Provide a single entry point for scraping operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the facade with a database session."""
        self.scraper_service = ScraperService(session)

    async def scrape_all(self) -> list[ScrapeResult]:
        """Collect and save vacancies from all enabled sources."""
        return await self.scraper_service.scrape_all()
