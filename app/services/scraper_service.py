# ==============================
# Library imports
# ==============================

import logging
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

import httpx
from sqlmodel.ext.asyncio.session import AsyncSession


# ==============================
# Application imports
# ==============================

from app.schemas import JobCreate
from app.scrapers.config_loader import (
    get_enabled_sources,
    load_sources_config,
)
from app.scrapers.models import ScrapeResult
from app.scrapers.registry import ScraperRegistry
from app.services.job_service import JobService


# ==============================
# Logger
# ==============================

logger = logging.getLogger(__name__)


# ==============================
# Scraper service
# ==============================

class ScraperService:
    """Coordinate vacancy collection and database updates."""

    def __init__(
        self,
        session: AsyncSession,
        config_path: Path = Path("sources.yaml"),
    ) -> None:
        """Initialize the service and its dependencies."""
        self.job_service = JobService(session)
        self.config_path = config_path
        self.scraper_registry = ScraperRegistry()

    # ==============================
    # Scraping
    # ==============================

    async def scrape_all(self) -> list[ScrapeResult]:
        """Collect and save vacancies from all enabled sources."""
        config = load_sources_config(self.config_path)
        sources = get_enabled_sources(config)

        results: list[ScrapeResult] = []

        if not sources:
            logger.info("No enabled scraper sources configured.")
            return results

        async with httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=True,
            headers={
                "User-Agent": "OrionJobAggregator/0.1",
            },
        ) as client:
            for source in sources:
                logger.info(
                    "Starting scraper for source '%s'.",
                    source.source_id,
                )

                source_started_at = datetime.now(timezone.utc)

                try:
                    scraper = self.scraper_registry.create(
                        source=source,
                        client=client,
                    )

                    result = await scraper.scrape()

                    await self._save_jobs(
                        source_id=source.source_id,
                        source_name=source.name,
                        result=result,
                    )

                    await self._update_source_lifecycle(
                        source_id=source.source_id,
                        complete_snapshot=source.complete_snapshot,
                        source_started_at=source_started_at,
                        result=result,
                    )

                    logger.info(
                        "Finished source '%s': %s vacancies found, "
                        "%s pages processed, %s errors.",
                        source.source_id,
                        len(result.jobs),
                        result.pages_processed,
                        len(result.errors),
                    )

                except Exception as error:
                    logger.exception(
                        "Scraping failed for source '%s'.",
                        source.source_id,
                    )

                    result = ScrapeResult(
                        source_id=source.source_id,
                        source_name=source.name,
                        errors=[
                            f"{type(error).__name__}: {error}"
                        ],
                    )

                results.append(result)

        return results

    async def _update_source_lifecycle(
        self,
        source_id: str,
        complete_snapshot: bool,
        source_started_at: datetime,
        result: ScrapeResult,
    ) -> None:
        """Deactivate outdated vacancies after a complete successful scrape."""
        if not complete_snapshot:
            logger.debug(
                "Skipping stale-vacancy update for source '%s': "
                "the source does not provide a complete snapshot.",
                source_id,
            )
            return

        # Never deactivate vacancies after an incomplete or failed scrape.
        if (
            not result.jobs
            or result.pages_processed == 0
            or result.errors
        ):
            logger.warning(
                "Skipping stale-vacancy update for source '%s': "
                "jobs=%s, pages=%s, errors=%s.",
                source_id,
                len(result.jobs),
                result.pages_processed,
                len(result.errors),
            )
            return

        inactive_count = await self.job_service.mark_not_seen_inactive(
            source_id=source_id,
            cutoff=source_started_at,
        )

        if inactive_count:
            logger.info(
                "Marked %s vacancies inactive for source '%s'.",
                inactive_count,
                source_id,
            )

    # ==============================
    # Save vacancies
    # ==============================

    async def _save_jobs(
        self,
        source_id: str,
        source_name: str,
        result: ScrapeResult,
    ) -> None:
        """Validate and save the vacancies collected from one source."""
        for scraped_job in result.jobs:
            try:
                job_data = scraped_job.model_dump()

                # Normalize salary amounts and correct reversed ranges.
                job_data["salary_min"] = self._parse_salary(
                    job_data["salary_min"]
                )
                job_data["salary_max"] = self._parse_salary(
                    job_data["salary_max"]
                )

                salary_min = job_data["salary_min"]
                salary_max = job_data["salary_max"]

                if (
                    salary_min is not None
                    and salary_max is not None
                    and salary_min > salary_max
                ):
                    logger.warning(
                        "Reversed salary range for '%s' from '%s': "
                        "%s > %s. Swapping values.",
                        scraped_job.title,
                        source_id,
                        salary_min,
                        salary_max,
                    )

                    job_data["salary_min"], job_data["salary_max"] = (
                        salary_max,
                        salary_min,
                    )

                # Convert the salary period to a standard value.
                job_data["salary_period"] = self._parse_salary_period(
                    job_data["salary_period"]
                )

                # Convert the publication date to a timezone-aware value.
                job_data["published_at"] = self._parse_date(
                    job_data["published_at"]
                )

                job_create = JobCreate(
                    source_id=source_id,
                    source_name=source_name,
                    **job_data,
                )

                await self.job_service.create_or_update(job_create)

            except Exception as error:
                message = (
                    f"Failed to save vacancy '{scraped_job.title}': "
                    f"{type(error).__name__}: {error}"
                )

                result.errors.append(message)

                logger.exception(
                    "Could not save vacancy '%s' from '%s'.",
                    scraped_job.title,
                    source_id,
                )

    # ==============================
    # Salary normalization
    # ==============================

    @staticmethod
    def _parse_salary(value: str | None) -> Decimal | None:
        """Convert a salary string into a positive decimal amount."""
        if not value:
            return None

        normalized = re.sub(r"[^\d,.\-]", "", value)

        if not normalized:
            return None

        # Handle formats such as 1.200,50 and 1,200.50.
        if "," in normalized and "." in normalized:
            if normalized.rfind(",") > normalized.rfind("."):
                normalized = normalized.replace(".", "")
                normalized = normalized.replace(",", ".")
            else:
                normalized = normalized.replace(",", "")

        elif "," in normalized:
            integer_part, decimal_part = normalized.rsplit(",", 1)

            if len(decimal_part) == 3:
                normalized = integer_part + decimal_part
            else:
                normalized = integer_part + "." + decimal_part

        try:
            amount = Decimal(normalized)
        except InvalidOperation:
            return None

        # Ignore zero, negative, and non-finite salary values.
        if not amount.is_finite() or amount <= 0:
            return None

        return amount

    @staticmethod
    def _parse_salary_period(value: str | None) -> str | None:
        """Convert a salary period to a standard value."""
        if not value:
            return None

        normalized = re.sub(r"\s+", "", value.casefold())

        if any(
            marker in normalized
            for marker in (
                "€/h",
                "/h",
                "/st",
                "stund",
                "hourly",
                "perhour",
            )
        ):
            return "hour"

        if any(
            marker in normalized
            for marker in (
                "/dien",
                "dienā",
                "daily",
                "perday",
            )
        ):
            return "day"

        if any(
            marker in normalized
            for marker in (
                "/gad",
                "gadā",
                "yearly",
                "annually",
                "peryear",
            )
        ):
            return "year"

        if any(
            marker in normalized
            for marker in (
                "/mēn",
                "mēnesī",
                "mēnes",
                "monthly",
                "permonth",
            )
        ):
            return "month"

        return None

    # ==============================
    # Date normalization
    # ==============================

    @staticmethod
    def _parse_date(value: str | None) -> datetime | None:
        """Parse ISO dates, formatted dates, and Latvian relative times."""
        if not value:
            return None

        normalized = value.strip().casefold()

        # Parse ISO-formatted dates first.
        try:
            parsed_date = datetime.fromisoformat(
                normalized.replace("z", "+00:00")
            )
        except ValueError:
            parsed_date = None

        if parsed_date is not None:
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(
                    tzinfo=timezone.utc
                )

            return parsed_date.astimezone(timezone.utc)

        # Parse dates such as 2026.10.16 and 16.10.2026.
        for date_format in ("%Y.%m.%d", "%d.%m.%Y"):
            try:
                parsed_date = datetime.strptime(
                    normalized,
                    date_format,
                )

                return parsed_date.replace(tzinfo=timezone.utc)

            except ValueError:
                continue

        # Parse Latvian relative dates, such as "pirms 3 stundām".
        match = re.search(
            r"pirms\s+(\d+)\s+([a-zāčēģīķļņōŗšūž]+)",
            normalized,
        )

        if match is None:
            return None

        amount = int(match.group(1))
        unit = match.group(2)

        if unit.startswith("sekund"):
            delta = timedelta(seconds=amount)
        elif unit.startswith(("minūt", "minut")):
            delta = timedelta(minutes=amount)
        elif unit.startswith("stund"):
            delta = timedelta(hours=amount)
        elif unit.startswith("dien"):
            delta = timedelta(days=amount)
        elif unit.startswith("nedēļ"):
            delta = timedelta(weeks=amount)
        elif unit.startswith(("mēnes", "mēneš")):
            delta = timedelta(days=30 * amount)
        elif unit.startswith("gad"):
            delta = timedelta(days=365 * amount)
        else:
            return None

        return datetime.now(timezone.utc) - delta