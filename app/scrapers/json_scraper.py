
# ==============================
# Standard library imports
# ==============================

import json
import logging
import re
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
from app.utils import normalize_description, normalize_text


# ==============================
# Logger configuration
# ==============================

logger = logging.getLogger(__name__)


# ==============================
# JSON scraper
# ==============================

class JSONScraper(BaseScraper):
    """Collect vacancies from JSON APIs."""

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
        """Download JSON responses and convert records into vacancies."""
        jobs: list[ScrapedJob] = []
        errors: list[str] = []
        pages_processed = 0

        # Process each configured source URL independently.
        for source_url in self.source.start_urls:
            try:
                content = await self.fetch_page(source_url)
                payload = json.loads(content)
                pages_processed += 1

                records = self._get_records(payload)

                # Parse each vacancy record independently.
                for record_number, record in enumerate(records, start=1):
                    if not isinstance(record, dict):
                        continue

                    try:
                        job = self._parse_record(
                            record=record,
                            source_url=source_url,
                        )

                        if job is not None:
                            jobs.append(job)

                    except (ValueError, TypeError) as error:
                        message = (
                            f"Failed to parse JSON record "
                            f"{record_number} from {source_url}: {error}"
                        )

                        errors.append(message)
                        logger.warning("%s", message)

            except (
                httpx.HTTPError,
                json.JSONDecodeError,
                ValueError,
            ) as error:
                message = (
                    f"Failed to process JSON source {source_url}: "
                    f"{type(error).__name__}: {error}"
                )

                errors.append(message)

                logger.exception(
                    "Could not process JSON source '%s'.",
                    source_url,
                )

        return self.create_result(
            jobs=jobs,
            pages_processed=pages_processed,
            errors=errors,
        )

    # ==============================
    # Response parsing
    # ==============================

    def _get_records(self, payload: object) -> list[object]:
        """Find vacancy records in a JSON API response."""
        if isinstance(payload, list):
            return payload

        if isinstance(payload, dict):
            # Support common response structures used by job APIs.
            for key in ("jobs", "results", "vacancies", "data"):
                value = payload.get(key)

                if isinstance(value, list):
                    return value

        raise ValueError(
            "Expected a JSON array or an object containing a "
            "'jobs', 'results', 'vacancies', or 'data' array."
        )

    # ==============================
    # Record parsing
    # ==============================

    def _parse_record(
        self,
        record: dict,
        source_url: str,
    ) -> ScrapedJob | None:
        """Map one JSON object to a normalized vacancy."""
        title_config = self.source.fields.get("title")

        if title_config is None:
            raise ValueError(
                "JSON source must define a 'title' field."
            )

        # Extract the title first to identify actual vacancy records.
        title = self._extract_field(
            record=record,
            field_config=title_config,
        )

        # Ignore metadata objects that do not represent vacancies.
        if not title:
            return None

        data: dict[str, str | None] = {
            "title": title,
        }

        # Extract all remaining fields using the source configuration.
        for field_name, field_config in self.source.fields.items():
            if field_name == "title":
                continue

            value = self._extract_field(
                record=record,
                field_config=field_config,
            )

            if field_config.required and not value:
                raise ValueError(
                    f"Required field '{field_name}' is missing."
                )

            # Map configured URL fields to the model attribute.
            target_field = (
                "original_url"
                if field_name in {"url", "original_url"}
                else field_name
            )

            data[target_field] = value

        # Convert HTML descriptions into readable text.
        if data.get("description"):
            data["description"] = normalize_description(
                data["description"]
            )

        # Apply additional field extraction for Remote OK.
        if self.source.source_id == "remote_ok":
            self._fill_remote_ok_fields(data)

        # An individual vacancy URL is required for JSON records.
        original_url = data.get("original_url")

        if not original_url:
            raise ValueError(
                "The JSON record does not contain an original vacancy URL."
            )

        # Resolve relative URLs against the source endpoint.
        original_url = urljoin(source_url, original_url)
        parsed_url = urlsplit(original_url)

        if parsed_url.scheme not in {"http", "https"}:
            raise ValueError(
                "Vacancy URL must use HTTP or HTTPS."
            )

        # Do not save the generic listing page as an individual vacancy.
        if (
            self.source.source_id == "remote_ok"
            and parsed_url.netloc.casefold()
            in {"remoteok.com", "www.remoteok.com"}
            and parsed_url.path.rstrip("/") == "/remote-jobs"
        ):
            logger.warning(
                "Skipping Remote OK record without an individual "
                "vacancy URL: '%s'",
                title,
            )

            return None

        data["original_url"] = original_url

        # Preserve missing identifiers as None.
        if not data.get("external_id"):
            data["external_id"] = None

        return ScrapedJob(**data)

    # ==============================
    # Source-specific field handling
    # ==============================

    def _fill_remote_ok_fields(
        self,
        data: dict[str, str | None],
    ) -> None:
        """Extract missing fields from explicitly labelled description text."""
        description = data.get("description")

        if not description:
            return

        # Extract location only when it has an explicit label.
        if not data.get("location"):
            location_match = re.search(
                r"(?im)^\s*Location\s*:\s*(.+?)\s*$",
                description,
            )

            if location_match:
                location = normalize_text(location_match.group(1))

                if location:
                    data["location"] = location[:255]

        # Extract employment type only when it has an explicit label.
        if not data.get("employment_type"):
            employment_match = re.search(
                r"(?im)^\s*Employment\s*Type\s*:\s*(.+?)\s*$",
                description,
            )

            if employment_match:
                employment_type = normalize_text(
                    employment_match.group(1)
                )

                if employment_type:
                    # Keep the first value before a pipe separator.
                    employment_type = employment_type.split("|", 1)[0]
                    data["employment_type"] = (
                        employment_type[:100].strip()
                    )

    # ==============================
    # Field extraction
    # ==============================

    def _extract_field(
        self,
        record: dict,
        field_config: ScraperFieldConfig,
    ) -> str | None:
        """Extract a constant or a value using a dotted JSON path."""
        # Return a configured constant without traversing the record.
        if field_config.value is not None:
            return normalize_text(field_config.value)

        if field_config.json_path is None:
            raise ValueError(
                "JSON fields must use 'json_path' or 'value' configuration."
            )

        value: object = record

        # Traverse nested dictionaries and indexed lists.
        for part in field_config.json_path.split("."):
            if isinstance(value, dict):
                value = value.get(part)

            elif isinstance(value, list) and part.isdigit():
                index = int(part)

                if index >= len(value):
                    return None

                value = value[index]

            else:
                return None

            if value is None:
                return None

        # Convert lists into readable comma-separated text.
        # Example: ["Full-Time", "Contract"] -> "Full-Time, Contract".
        if isinstance(value, list):
            items: list[str] = []

            for item in value:
                if item is None:
                    continue

                if isinstance(item, (dict, list)):
                    item_text = json.dumps(
                        item,
                        ensure_ascii=False,
                    )
                else:
                    item_text = str(item)

                item_text = normalize_text(item_text)

                if item_text:
                    items.append(item_text)

            if not items:
                return None

            return normalize_text(", ".join(items))

        # Serialize dictionaries as JSON instead of Python representations.
        if isinstance(value, dict):
            value = json.dumps(value, ensure_ascii=False)

        return normalize_text(str(value))
