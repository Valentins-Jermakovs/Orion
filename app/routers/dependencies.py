from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import get_session
from app.facades.job_facade import JobFacade


def get_job_facade(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> JobFacade:
    """Provide a job facade for API routes."""
    return JobFacade(session)