
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.job import Job
from app.repositories.job_repository import JobRepository
from app.schemas.job import JobCreate
from app.utils.normalization import (
    create_deduplication_key,
    normalize_text,
)


class JobService:
    """Handle business logic for job vacancies."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = JobRepository(session)

    async def create_or_update(self, job_data: JobCreate) -> Job:
        """Create a vacancy or update an existing one."""
        data = job_data.model_dump()

        # Normalize text fields before saving.
        data["source_id"] = data["source_id"].strip().lower()

        for field in (
            "source_name",
            "title",
            "company",
            "location",
            "employment_type",
            "description",
            "external_id",
        ):
            data[field] = normalize_text(data[field])

        if not data["source_id"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Source ID cannot be empty.",
            )

        if not data["source_name"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Source name cannot be empty.",
            )

        if not data["title"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Job title cannot be empty.",
            )

        # Validate the salary range.
        salary_min = data["salary_min"]
        salary_max = data["salary_max"]

        if (
            salary_min is not None
            and salary_max is not None
            and salary_min > salary_max
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Minimum salary cannot exceed maximum salary.",
            )

        # Normalize the currency code.
        if data["salary_currency"]:
            data["salary_currency"] = (
                data["salary_currency"].strip().upper()
            )

        # Generate a stable key to prevent duplicate vacancies.
        try:
            deduplication_key = create_deduplication_key(
                source_id=data["source_id"],
                original_url=data["original_url"],
                external_id=data["external_id"],
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid vacancy URL or source identifier.",
            ) from None

        job = Job(
            **data,
            deduplication_key=deduplication_key,
        )

        try:
            saved_job = await self.repository.upsert(job)
            await self.session.commit()

            return saved_job

        except Exception:
            await self.session.rollback()
            raise

    async def get_job(self, job_id: UUID) -> Job:
        """Return a vacancy by its internal ID."""
        job = await self.repository.get_by_id(job_id)

        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job vacancy not found.",
            )

        return job

    async def get_jobs(
        self,
        query: str | None = None,
        location: str | None = None,
        source_id: str | None = None,
        status_filter: str = "active",
        limit: int = 20,
        offset: int = 0,
    ) -> list[Job]:
        """Return vacancies matching the requested filters."""
        if not 1 <= limit <= 100:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Limit must be between 1 and 100.",
            )

        if offset < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Offset cannot be negative.",
            )

        return await self.repository.list_jobs(
            query=query,
            location=location,
            source_id=source_id,
            status=status_filter,
            limit=limit,
            offset=offset,
        )
