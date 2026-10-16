from collections.abc import Callable

import httpx

from app.scrapers.base import BaseScraper
from app.scrapers.config import SourceConfig
from app.scrapers.csv_scraper import CSVScraper
from app.scrapers.json_scraper import JSONScraper


ScraperFactory = Callable[..., BaseScraper]


class ScraperRegistry:
    """Create the appropriate scraper for each configured source."""

    def __init__(self) -> None:
        self._type_factories: dict[str, ScraperFactory] = {
            "csv": CSVScraper,
            "json": JSONScraper,
        }

        # Allows a particular source to use a custom scraper.
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
        """Register a scraper for a source format."""
        self._type_factories[scraper_type] = factory

    def create(
        self,
        source: SourceConfig,
        client: httpx.AsyncClient,
    ) -> BaseScraper:
        """Create the appropriate scraper for a configured source."""
        factory = self._source_factories.get(source.source_id)

        if factory is None:
            factory = self._type_factories.get(source.scraper_type)

        if factory is None:
            raise ValueError(
                f"No scraper registered for source "
                f"'{source.source_id}' with type "
                f"'{source.scraper_type}'."
            )

        return factory(
            source=source,
            client=client,
        )