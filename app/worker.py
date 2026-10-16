import asyncio
import logging

from app.config.logging_config import configure_logging
from app.config.settings import settings
from app.db.session import (
    async_session_factory,
    close_database_connection,
)
from app.services.scraper_service import ScraperService


logger = logging.getLogger(__name__)


async def run_worker() -> None:
    """Periodically collect vacancies from configured sources."""
    if settings.scrape_interval_seconds < 1:
        raise ValueError(
            "SCRAPE_INTERVAL_SECONDS must be greater than zero."
        )

    logger.info("Orion scraper worker started.")

    try:
        while True:
            try:
                async with async_session_factory() as session:
                    scraper_service = ScraperService(session)
                    results = await scraper_service.scrape_all()

                jobs_found = sum(
                    len(result.jobs)
                    for result in results
                )

                errors_count = sum(
                    len(result.errors)
                    for result in results
                )

                logger.info(
                    "Scraping cycle completed. "
                    "Sources: %s, vacancies: %s, errors: %s.",
                    len(results),
                    jobs_found,
                    errors_count,
                )

            except Exception:
                logger.exception("Scraping cycle failed.")

            logger.info(
                "Next scraping cycle in %s seconds.",
                settings.scrape_interval_seconds,
            )

            await asyncio.sleep(
                settings.scrape_interval_seconds
            )

    finally:
        await close_database_connection()
        logger.info("Orion scraper worker stopped.")


if __name__ == "__main__":
    configure_logging()

    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user.")