
# ==============================
# Library imports
# ==============================

from collections.abc import Callable

# ==============================
# Application imports
# ==============================

import httpx

from app.scrapers.base import BaseScraper
from app.scrapers.config import SourceConfig
from app.scrapers.csv_scraper import CSVScraper
from app.scrapers.json_scraper import JSONScraper


# ==============================
# Type definitions
# ==============================

ScraperFactory = Callable[
    [SourceConfig, httpx.AsyncClient],
    BaseScraper,
]


# ==============================
# Scraper registry
# ==============================

class ScraperRegistry:
    """Create scrapers based on source configuration."""

    def __init__(self) -> None:
        """Register the supported scraper types."""
        self._type_factories: dict[str, ScraperFactory] = {
            "csv": CSVScraper,
            "json": JSONScraper,
        }

        # Source-specific factories override the default scraper type.
        self._source_factories: dict[str, ScraperFactory] = {}

    def register(
        self,
        source_id: str,
        factory: ScraperFactory,
    ) -> None:
        """Register a custom scraper for a specific source."""
        self._source_factories[source_id] = factory

    def register_type(
        self,
        scraper_type: str,
        factory: ScraperFactory,
    ) -> None:
        """Register a scraper for a data format."""
        self._type_factories[scraper_type] = factory

    def create(
        self,
        source: SourceConfig,
        client: httpx.AsyncClient,
    ) -> BaseScraper:
        """Create a scraper for the specified source."""
        factory = self._source_factories.get(source.source_id)

        if factory is None:
            factory = self._type_factories.get(source.scraper_type)

        if factory is None:
            raise ValueError(
                f"No scraper registered for source '{source.source_id}' "
                f"with type '{source.scraper_type}'."
            )

        return factory(source, client)
