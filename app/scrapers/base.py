from abc import ABC, abstractmethod

import httpx

from app.scrapers.models import ScrapedJob, ScrapeResult


class BaseScraper(ABC):
    """Define the common interface for all job scrapers."""

    def __init__(
        self,
        source_id: str,
        source_name: str,
        client: httpx.AsyncClient,
    ) -> None:
        self.source_id = source_id
        self.source_name = source_name
        self.client = client

    @abstractmethod
    async def scrape(self) -> ScrapeResult:
        """Collect vacancies from the configured source."""
        raise NotImplementedError

    async def fetch_page(self, url: str) -> str:
        """Download a web page and return its HTML."""
        response = await self.client.get(url)
        response.raise_for_status()

        return response.text

    def create_result(
        self,
        jobs: list[ScrapedJob] | None = None,
        pages_processed: int = 0,
        errors: list[str] | None = None,
    ) -> ScrapeResult:
        """Create a standardized result for this source."""
        return ScrapeResult(
            source_id=self.source_id,
            source_name=self.source_name,
            jobs=jobs or [],
            pages_processed=pages_processed,
            errors=errors or [],
        )