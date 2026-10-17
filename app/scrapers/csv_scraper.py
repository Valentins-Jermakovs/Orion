# ==============================
# Standard library imports
# ==============================

import csv
import io
import logging
from urllib.parse import urljoin, urlsplit

# ==============================
# Third-party imports
# ==============================

import httpx

# ==============================
# Application imports
# ==============================

from app.scrapers.base import BaseScraper
from app.scrapers.config import ScraperFieldConfig, SourceConfig
from app.scrapers.models import ScrapedJob, ScrapeResult
from app.utils import normalize_text


# ==============================
# Logger configuration
# ==============================

logger = logging.getLogger(__name__)


# ==============================
# CSV scraper
# ==============================

class CSVScraper(BaseScraper):
    """Collect vacancies from configurable CSV data sources."""

    def __init__(
        self,
        source: SourceConfig,
        client: httpx.AsyncClient,
    ) -> None:
        """Initialize the scraper with source configuration and HTTP client."""
        super().__init__(
            source_id=source.source_id,
            source_name=source.name,
            client=client,
        )

        self.source = source

    # ==============================
    # Public methods
    # ==============================

    async def scrape(self) -> ScrapeResult:
        """Download CSV files and convert their rows into vacancies."""
        jobs: list[ScrapedJob] = []
        errors: list[str] = []
        pages_processed = 0

        for source_url in self.source.start_urls:
            try:
                content = await self.fetch_page(source_url)
                pages_processed += 1

                reader = self._create_reader(content)

                if not reader.fieldnames:
                    errors.append(
                        f"CSV source has no column headers: {source_url}"
                    )
                    continue

                # Normalize column headers, including a possible BOM.
                reader.fieldnames = [
                    name.strip().lstrip("\ufeff") if name else ""
                    for name in reader.fieldnames
                ]

                # Parse each data row independently.
                for row_number, row in enumerate(reader, start=2):
                    try:
                        job = self._parse_row(
                            row=row,
                            source_url=source_url,
                        )

                        if job is not None:
                            jobs.append(job)

                    except (ValueError, TypeError) as error:
                        errors.append(
                            f"Failed to parse CSV row {row_number} "
                            f"from {source_url}: {error}"
                        )

            except (
                httpx.HTTPError,
                csv.Error,
                UnicodeDecodeError,
                ValueError,
            ) as error:
                errors.append(
                    f"Failed to process CSV source {source_url}: "
                    f"{type(error).__name__}: {error}"
                )

                logger.exception(
                    "Could not process CSV source '%s'.",
                    source_url,
                )

        return self.create_result(
            jobs=jobs,
            pages_processed=pages_processed,
            errors=errors,
        )

    # ==============================
    # CSV reader
    # ==============================

    def _create_reader(self, content: str) -> csv.DictReader:
        """Create a CSV reader and automatically detect the delimiter."""
        content = content.lstrip("\ufeff")

        if not content.strip():
            raise ValueError("The CSV file is empty.")

        sample = content[:8192]

        try:
            dialect = csv.Sniffer().sniff(
                sample,
                delimiters=",;\t|",
            )
        except csv.Error:
            # Use the standard CSV format when detection is inconclusive.
            dialect = csv.excel

        return csv.DictReader(
            io.StringIO(content, newline=""),
            dialect=dialect,
        )

    # ==============================
    # Row parsing
    # ==============================

    def _parse_row(
        self,
        row: dict[str, str | None],
        source_url: str,
    ) -> ScrapedJob | None:
        """Map a single CSV row to a normalized vacancy."""
        data: dict[str, str | None] = {}

        # Build a case-insensitive view of the source columns.
        normalized_row = {
            key.strip().casefold(): value
            for key, value in row.items()
            if key
        }

        # Extract values according to the source configuration.
        for field_name, field_config in self.source.fields.items():
            value = self._extract_field(
                row=normalized_row,
                field_config=field_config,
            )

            if field_config.required and not value:
                raise ValueError(
                    f"Required field '{field_name}' is missing."
                )

            # Map the configured URL field to the model attribute.
            target_field = (
                "original_url"
                if field_name == "url"
                else field_name
            )

            data[target_field] = value

        # Skip rows without a vacancy title.
        if not data.get("title"):
            return None

        # Use the dataset URL if the vacancy has no individual URL.
        original_url = data.get("original_url") or source_url
        original_url = urljoin(source_url, original_url)

        # Accept only HTTP and HTTPS URLs.
        scheme = urlsplit(original_url).scheme

        if scheme not in {"http", "https"}:
            raise ValueError(
                "Vacancy source URL must use HTTP or HTTPS."
            )

        data["original_url"] = original_url

        # Allow the application to handle missing external identifiers.
        if not data.get("external_id"):
            data["external_id"] = None

        return ScrapedJob(**data)

    # ==============================
    # Field extraction
    # ==============================

    def _extract_field(
        self,
        row: dict[str, str | None],
        field_config: ScraperFieldConfig,
    ) -> str | None:
        """Extract a value from a CSV column or a configured constant."""
        # Return a constant value when one is configured.
        if field_config.value is not None:
            return normalize_text(field_config.value)

        if field_config.column is None:
            raise ValueError(
                "CSV fields must use 'column' or 'value' configuration."
            )

        # Match column names without regard to case or surrounding spaces.
        column_name = field_config.column.strip().casefold()
        value = row.get(column_name)

        if value is None:
            available_columns = ", ".join(sorted(row.keys()))

            raise ValueError(
                f"CSV column '{field_config.column}' was not found. "
                f"Available columns: {available_columns}"
            )

        return normalize_text(value)
