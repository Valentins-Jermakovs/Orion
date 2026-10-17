from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db import get_session
from app.facades.job_facade import JobFacade
from app.facades.scraper_facade import ScraperFacade


def get_job_facade(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> JobFacade:
    """Provide a job facade for API routes."""
    return JobFacade(session)


def get_scraper_facade(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ScraperFacade:
    """Provide a scraper facade for API routes."""
    return ScraperFacade(session)