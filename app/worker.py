# ==============================
# Standard library imports
# ==============================

import asyncio
import logging

# ==============================
# Application imports
# ==============================

from app.config import settings
from app.db import async_session_factory, close_database_connection
from app.services import ScraperService


# ==============================
# Logger configuration
# ==============================

logger = logging.getLogger(__name__)


# ==============================
# Worker
# ==============================

async def run_worker() -> None:
    """Periodically collect vacancies from configured sources."""
    interval = settings.scrape_interval_seconds

    if interval < 1:
        raise ValueError(
            "SCRAPE_INTERVAL_SECONDS must be greater than zero."
        )

    logger.info("Orion scraper worker started.")

    try:
        while True:
            try:
                # Run one scraping cycle using a dedicated database session.
                async with async_session_factory() as session:
                    scraper_service = ScraperService(session)
                    results = await scraper_service.scrape_all()

                # Aggregate scraping statistics.
                jobs_found = sum(
                    len(result.jobs)
                    for result in results
                )
                errors_count = sum(
                    len(result.errors)
                    for result in results
                )

                logger.info(
                    "Scraping cycle completed: "
                    "sources=%s, vacancies=%s, errors=%s.",
                    len(results),
                    jobs_found,
                    errors_count,
                )

            except Exception:
                # Retry automatically after an unsuccessful cycle.
                logger.exception(
                    "Scraping cycle failed. Retrying in %s seconds.",
                    interval,
                )

            logger.info(
                "Next scraping cycle in %s seconds.",
                interval,
            )

            await asyncio.sleep(interval)

    finally:
        # Release database resources when the worker stops.
        try:
            await close_database_connection()
        finally:
            logger.info("Orion scraper worker stopped.")


# ==============================
# Worker entry point
# ==============================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker stopped by keyboard interrupt.")
