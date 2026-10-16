import csv
import io
import logging
from urllib.parse import urljoin, urlsplit

import httpx

from app.scrapers.base import BaseScraper
from app.scrapers.config import SourceConfig, ScraperFieldConfig
from app.scrapers.models import ScrapedJob, ScrapeResult
from app.utils.normalization import normalize_text


logger = logging.getLogger(__name__)


class CSVScraper(BaseScraper):
    """Collect vacancies from configurable CSV data sources."""

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
                    name.strip().lstrip("\ufeff")
                    if name
                    else ""
                    for name in reader.fieldnames
                ]

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

    def _create_reader(
        self,
        content: str,
    ) -> csv.DictReader:
        """Create a CSV reader and detect the delimiter."""
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

        for field_name, field_config in self.source.fields.items():
            value = self._extract_field(
                row=normalized_row,
                field_config=field_config,
            )

            if field_config.required and not value:
                raise ValueError(
                    f"Required field '{field_name}' is missing."
                )

            # Support either 'url' or 'original_url' in the configuration.
            target_field = (
                "original_url"
                if field_name == "url"
                else field_name
            )

            data[target_field] = value

        if not data.get("title"):
            return None

        # Bulk datasets do not always provide a URL for each vacancy.
        # Use the dataset URL as a fallback, not as a fabricated job URL.
        original_url = data.get("original_url")

        if not original_url:
            original_url = source_url

        original_url = urljoin(source_url, original_url)
        scheme = urlsplit(original_url).scheme

        if scheme not in {"http", "https"}:
            raise ValueError(
                "Vacancy source URL must use HTTP or HTTPS."
            )

        data["original_url"] = original_url

        if not data.get("external_id"):
            data["external_id"] = None

        return ScrapedJob(**data)

    def _extract_field(
        self,
        row: dict[str, str | None],
        field_config: ScraperFieldConfig,
    ) -> str | None:
        """Extract a value from a CSV column or constant."""
        if field_config.value is not None:
            return normalize_text(field_config.value)

        if field_config.column is None:
            raise ValueError(
                "CSV fields must use 'column' or 'value' configuration."
            )

        column_name = field_config.column.strip().casefold()
        value = row.get(column_name)

        if value is None:
            available_columns = ", ".join(sorted(row.keys()))

            raise ValueError(
                f"CSV column '{field_config.column}' was not found. "
                f"Available columns: {available_columns}"
            )

        return normalize_text(value)