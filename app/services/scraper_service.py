
import logging
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

import httpx
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.job import Job
from app.schemas.job import JobCreate
from app.scrapers.config_loader import (
    get_enabled_sources,
    load_sources_config,
)
from app.scrapers.generic_html import GenericHTMLScraper
from app.scrapers.models import ScrapeResult
from app.scrapers.registry import ScraperRegistry
from app.services.job_service import JobService


logger = logging.getLogger(__name__)


class ScraperService:
    """Coordinate scraping and saving vacancies from job websites."""

    def __init__(
        self,
        session: AsyncSession,
        config_path: Path = Path("sources.yaml"),
    ) -> None:
        self.job_service = JobService(session)
        self.config_path = config_path

        self.scraper_registry = ScraperRegistry(
            default_factory=GenericHTMLScraper,
        )

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

                job_data["salary_min"] = self._parse_salary(
                    job_data["salary_min"]
                )
                job_data["salary_max"] = self._parse_salary(
                    job_data["salary_max"]
                )
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
                    f"Failed to save vacancy "
                    f"'{scraped_job.title}': "
                    f"{type(error).__name__}: {error}"
                )

                result.errors.append(message)

                logger.exception(
                    "Could not save vacancy '%s' from '%s'.",
                    scraped_job.title,
                    source_id,
                )

    @staticmethod
    def _parse_salary(value: str | None) -> Decimal | None:
        """Convert a simple salary string into a decimal amount."""
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

        if not amount.is_finite() or amount < 0:
            return None

        return amount

    @staticmethod
    def _parse_date(value: str | None) -> datetime | None:
        """Parse an ISO-formatted publication date."""
        if not value:
            return None

        try:
            parsed_date = datetime.fromisoformat(
                value.strip().replace("Z", "+00:00")
            )
        except ValueError:
            return None

        if parsed_date.tzinfo is None:
            parsed_date = parsed_date.replace(tzinfo=timezone.utc)

        return parsed_date.astimezone(timezone.utc)
