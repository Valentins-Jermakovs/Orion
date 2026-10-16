
from sqlmodel.ext.asyncio.session import AsyncSession

from app.scrapers.models import ScrapeResult
from app.services.scraper_service import ScraperService


class ScraperFacade:
    """Provide a single entry point for scraping operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.scraper_service = ScraperService(session)

    async def scrape_all(self) -> list[ScrapeResult]:
        """Collect and save vacancies from enabled sources."""
        return await self.scraper_service.scrape_all()
