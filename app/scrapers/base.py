
# ==============================
# Library imports
# ==============================

from abc import ABC, abstractmethod

import httpx


# ==============================
# Application imports
# ==============================

from app.scrapers.models import ScrapedJob, ScrapeResult


# ==============================
# Base scraper
# ==============================

class BaseScraper(ABC):
    """Define the common interface for all vacancy scrapers."""

    def __init__(
        self,
        source_id: str,
        source_name: str,
        client: httpx.AsyncClient,
    ) -> None:
        """Initialize the scraper with source information and HTTP client."""
        self.source_id = source_id
        self.source_name = source_name
        self.client = client

    # ==============================
    # Scraping interface
    # ==============================

    @abstractmethod
    async def scrape(self) -> ScrapeResult:
        """Collect vacancies from the configured source."""
        raise NotImplementedError

    # ==============================
    # HTTP requests
    # ==============================

    async def fetch_page(self, url: str) -> str:
        """Fetch source content and return the response text."""
        response = await self.client.get(url)
        response.raise_for_status()

        return response.text

    # ==============================
    # Scraping results
    # ==============================

    def create_result(
        self,
        jobs: list[ScrapedJob] | None = None,
        pages_processed: int = 0,
        errors: list[str] | None = None,
    ) -> ScrapeResult:
        """Create a standardized result for the current source."""
        return ScrapeResult(
            source_id=self.source_id,
            source_name=self.source_name,
            jobs=jobs if jobs is not None else [],
            pages_processed=pages_processed,
            errors=errors if errors is not None else [],
        )
