
# ==============================
# Standard library imports
# ==============================

from typing import Annotated

# ==============================
# Third-party imports
# ==============================

from fastapi import APIRouter, Depends

# ==============================
# Application imports
# ==============================

from app.facades import ScraperFacade
from app.routers.dependencies import get_scraper_facade, jwt_auth
from app.scrapers import ScrapeResult


# ==============================
# Sources router
# ==============================

router = APIRouter(
    prefix="/sources",
    tags=["Sources"],
)


# ==============================
# Scrape sources
# ==============================

@router.post("/scrape", response_model=list[ScrapeResult])
async def scrape_sources(
    admin: Annotated[
        dict,
        Depends(jwt_auth.require_roles(["admin"])),
    ],
    facade: Annotated[
        ScraperFacade,
        Depends(get_scraper_facade),
    ],
) -> list[ScrapeResult]:
    """Start scraping all enabled sources."""
    return await facade.scrape_all()
