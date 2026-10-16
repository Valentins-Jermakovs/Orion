import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.config.settings import settings
from app.facades.scraper_facade import ScraperFacade
from app.routers.dependencies import get_scraper_facade
from app.scrapers.models import ScrapeResult


router = APIRouter(
    prefix="/sources",
    tags=["Sources"],
)


@router.post("/scrape", response_model=list[ScrapeResult])
async def scrape_sources(
    facade: Annotated[ScraperFacade, Depends(get_scraper_facade)],
    api_key: Annotated[
        str | None,
        Header(alias="X-Scrape-Api-Key"),
    ] = None,
) -> list[ScrapeResult]:
    """Start scraping all enabled sources."""
    expected_api_key = settings.scrape_api_key.get_secret_value()

    if not api_key or not secrets.compare_digest(
        api_key,
        expected_api_key,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing scraper API key.",
        )

    return await facade.scrape_all()