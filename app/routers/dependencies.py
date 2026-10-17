
# ==============================
# Standard library imports
# ==============================

from typing import Annotated

# ==============================
# Third-party imports
# ==============================

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

# ==============================
# Application configuration
# ==============================

from app.config import settings
from app.db import get_session

# ==============================
# Application facades
# ==============================

from app.facades import (
    JobFacade,
    ScraperFacade,
)

# ==============================
# Authentication utilities
# ==============================

from app.utils import JWTAuth, JWTManager


# ==============================
# JWT authentication
# ==============================

# Create a shared JWT manager using application settings.
jwt_manager = JWTManager(
    secret_key=settings.jwt_secret_key.get_secret_value(),
    algorithm=settings.jwt_algorithm,
)

# Create shared authentication dependencies for API routes.
jwt_auth = JWTAuth(
    jwt_manager=jwt_manager,
)


# ==============================
# Job dependencies
# ==============================

def get_job_facade(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> JobFacade:
    """Provide a job facade for API routes."""
    return JobFacade(session)


# ==============================
# Scraper dependencies
# ==============================

def get_scraper_facade(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ScraperFacade:
    """Provide a scraper facade for API routes."""
    return ScraperFacade(session)
