from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.facades.job_facade import JobFacade
from app.routers.dependencies import get_job_facade
from app.schemas import JobListRead, JobRead


router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)


@router.get("", response_model=list[JobListRead])
async def get_jobs(
    facade: Annotated[JobFacade, Depends(get_job_facade)],
    q: str | None = Query(
        default=None,
        min_length=1,
        max_length=200,
    ),
    location: str | None = Query(
        default=None,
        min_length=1,
        max_length=255,
    ),
    source_id: str | None = Query(
        default=None,
        max_length=100,
    ),
    status: str = Query(
        default="active",
        pattern="^(active|inactive|closed)$",
    ),
    min_salary: Decimal | None = Query(
        default=None,
        ge=0,
    ),
    max_salary: Decimal | None = Query(
        default=None,
        ge=0,
    ),
    salary_currency: str | None = Query(
        default=None,
        pattern="^[A-Za-z]{3}$",
    ),
    employment_type: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
) -> list[JobListRead]:
    """Return a concise list of vacancies matching the requested filters."""
    jobs = await facade.get_jobs(
        query=q,
        location=location,
        source_id=source_id,
        status=status,
        min_salary=min_salary,
        max_salary=max_salary,
        salary_currency=salary_currency,
        employment_type=employment_type,
        limit=limit,
        offset=offset,
    )

    return [
        JobListRead.model_validate(job)
        for job in jobs
    ]


@router.get("/{job_id}", response_model=JobRead)
async def get_job(
    job_id: UUID,
    facade: Annotated[JobFacade, Depends(get_job_facade)],
) -> JobRead:
    """Return a vacancy with full details by its internal ID."""
    job = await facade.get_job(job_id)

    return JobRead.model_validate(job)