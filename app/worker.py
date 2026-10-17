
import asyncio
import logging

from app.config.settings import settings
from app.db.session import (
    async_session_factory,
    close_database_connection,
)
from app.services.scraper_service import ScraperService


logger = logging.getLogger(__name__)


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
                # Create a database session for the current scraping cycle.
                async with async_session_factory() as session:
                    scraper_service = ScraperService(session)
                    results = await scraper_service.scrape_all()

                # Calculate the number of collected vacancies and errors.
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
                # Keep the worker running if a scraping cycle fails.
                logger.exception(
                    "Scraping cycle failed. The worker will retry "
                    "after %s seconds.",
                    interval,
                )

            logger.info(
                "Next scraping cycle in %s seconds.",
                interval,
            )

            await asyncio.sleep(interval)

    finally:
        # Close database resources when the worker stops.
        await close_database_connection()
        logger.info("Orion scraper worker stopped.")


if __name__ == "__main__":
    # Configure basic console logging without a separate module.
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info(
            "Worker stopped by keyboard interrupt."
        )
