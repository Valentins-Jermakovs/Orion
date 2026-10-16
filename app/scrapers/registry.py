from collections.abc import Callable

import httpx

from app.scrapers.base import BaseScraper
from app.scrapers.config import SourceConfig


ScraperFactory = Callable[
    [SourceConfig, httpx.AsyncClient],
    BaseScraper,
]


class ScraperRegistry:
    """Register and create scrapers for job sources."""

    def __init__(self, default_factory: ScraperFactory) -> None:
        self.default_factory = default_factory
        self.scrapers: dict[str, ScraperFactory] = {}

    def register(
        self,
        source_id: str,
        factory: ScraperFactory,
    ) -> None:
        """Register a custom scraper for a specific source."""
        source_id = source_id.strip().lower()

        if not source_id:
            raise ValueError("Source ID cannot be empty.")

        if source_id in self.scrapers:
            raise ValueError(
                f"Scraper for source '{source_id}' is already registered."
            )

        self.scrapers[source_id] = factory

    def create(
        self,
        source: SourceConfig,
        client: httpx.AsyncClient,
    ) -> BaseScraper:
        """Create the appropriate scraper for a source."""
        source_id = source.source_id.strip().lower()

        factory = self.scrapers.get(
            source_id,
            self.default_factory,
        )

        return factory(source, client)