from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.facades.job_facade import JobFacade
from app.routers.dependencies import get_job_facade
from app.schemas.job import JobRead


router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)


@router.get("", response_model=list[JobRead])
async def get_jobs(
    facade: Annotated[JobFacade, Depends(get_job_facade)],
    q: str | None = Query(default=None, min_length=1, max_length=200),
    location: str | None = Query(
        default=None,
        min_length=1,
        max_length=255,
    ),
    source_id: str | None = Query(default=None, max_length=100),
    status: str = Query(
        default="active",
        pattern="^(active|inactive|closed)$",
    ),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[JobRead]:
    """Return vacancies matching the requested filters."""
    jobs = await facade.get_jobs(
        query=q,
        location=location,
        source_id=source_id,
        status=status,
        limit=limit,
        offset=offset,
    )

    return [JobRead.model_validate(job) for job in jobs]


@router.get("/{job_id}", response_model=JobRead)
async def get_job(
    job_id: UUID,
    facade: Annotated[JobFacade, Depends(get_job_facade)],
) -> JobRead:
    """Return a vacancy by its internal ID."""
    job = await facade.get_job(job_id)

    return JobRead.model_validate(job)