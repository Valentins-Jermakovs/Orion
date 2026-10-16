
from urllib.parse import urljoin, urlsplit

import httpx
from selectolax.lexbor import LexborHTMLParser

from app.scrapers.base import BaseScraper
from app.scrapers.config import SourceConfig, ScraperFieldConfig
from app.scrapers.models import ScrapedJob, ScrapeResult
from app.utils.normalization import normalize_text


class GenericHTMLScraper(BaseScraper):
    """Collect job vacancies using configurable HTML selectors."""

    def __init__(
        self,
        source: SourceConfig,
        client: httpx.AsyncClient,
    ) -> None:
        super().__init__(
            source_id=source.source_id,
            source_name=source.name,
            client=client,
        )

        self.source = source

    async def scrape(self) -> ScrapeResult:
        """Collect vacancies from all configured start URLs."""
        jobs: list[ScrapedJob] = []
        errors: list[str] = []
        visited_pages: set[str] = set()
        pages_processed = 0

        for start_url in self.source.start_urls:
            current_url = start_url

            for _ in range(self.source.pagination.max_pages):
                if current_url in visited_pages:
                    break

                visited_pages.add(current_url)

                try:
                    html = await self.fetch_page(current_url)
                    parser = LexborHTMLParser(html)

                    cards = parser.css(self.source.item_selector)
                    pages_processed += 1

                    if not cards:
                        errors.append(
                            f"No vacancy cards found on {current_url}"
                        )

                    for card in cards:
                        try:
                            job = self._parse_card(
                                card=card,
                                page_url=current_url,
                            )

                            if job is not None:
                                jobs.append(job)

                        except (ValueError, TypeError) as exc:
                            errors.append(
                                f"Failed to parse a vacancy on "
                                f"{current_url}: {exc}"
                            )

                    next_url = self._get_next_page(
                        parser=parser,
                        current_url=current_url,
                    )

                    if next_url is None:
                        break

                    current_url = next_url

                except (httpx.HTTPError, ValueError) as exc:
                    errors.append(
                        f"Failed to process {current_url}: "
                        f"{type(exc).__name__}: {exc}"
                    )
                    break

        return self.create_result(
            jobs=jobs,
            pages_processed=pages_processed,
            errors=errors,
        )

    def _parse_card(
        self,
        card,
        page_url: str,
    ) -> ScrapedJob | None:
        """Extract vacancy fields from one HTML card."""
        data: dict[str, str | None] = {}

        for field_name, field_config in self.source.fields.items():
            value = self._extract_field(
                card=card,
                field_config=field_config,
            )

            if field_config.required and not value:
                raise ValueError(
                    f"Required field '{field_name}' is missing."
                )

            if field_name == "url":
                field_name = "original_url"

                if value:
                    value = urljoin(page_url, value)

                    if urlsplit(value).scheme not in {"http", "https"}:
                        raise ValueError(
                            "Vacancy URL must use HTTP or HTTPS."
                        )

            data[field_name] = value

        if not data.get("title"):
            return None

        if not data.get("original_url"):
            return None

        if not data.get("external_id"):
            data["external_id"] = None

        return ScrapedJob(**data)

    
    def _extract_field(
        self,
        card,
        field_config: ScraperFieldConfig,
    ) -> str | None:
        """Extract a constant, text, or attribute from an HTML card."""
        if field_config.value is not None:
            return normalize_text(field_config.value)

        if field_config.selector is None:
            return None

        element = card.css_first(field_config.selector)

        if element is None:
            return None

        if field_config.attribute:
            value = element.attributes.get(field_config.attribute)

            if value is None:
                return None
        else:
            value = element.text(separator=" ", strip=True)

        return normalize_text(value)


    def _get_next_page(
        self,
        parser: LexborHTMLParser,
        current_url: str,
    ) -> str | None:
        """Find the URL of the next results page."""
        selector = self.source.pagination.next_selector

        if not selector:
            return None

        element = parser.css_first(selector)

        if element is None:
            return None

        href = element.attributes.get("href")

        if not href:
            return None

        next_url = urljoin(current_url, href)
        scheme = urlsplit(next_url).scheme

        if scheme not in {"http", "https"}:
            return None

        return next_url
