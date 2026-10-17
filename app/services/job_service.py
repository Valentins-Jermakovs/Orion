from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Job
from app.repositories.job_repository import JobRepository
from app.schemas import JobCreate
from app.utils.normalization import (
    create_deduplication_key,
    normalize_description,
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
        data["source_id"] = data["source_id"].strip().lower()

        # Normalize fields containing short text values.
        for field in (
            "source_name",
            "title",
            "company",
            "location",
            "employment_type",
            "external_id",
        ):
            data[field] = normalize_text(data[field])

        # Preserve readable paragraphs and line breaks in descriptions.
        data["description"] = normalize_description(
            data["description"]
        )

        if not data["source_id"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Source ID cannot be empty.",
            )

        if not data["source_name"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Source name cannot be empty.",
            )

        if not data["title"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
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
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
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
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Invalid vacancy URL or source identifier.",
            ) from None

        # New vacancies are active. If an inactive vacancy appears
        # again, the upsert will reactivate it.
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

    async def mark_not_seen_inactive(
        self,
        source_id: str,
        cutoff: datetime,
    ) -> int:
        """Deactivate vacancies missing from a complete source snapshot."""
        try:
            count = await self.repository.mark_not_seen_inactive(
                source_id=source_id.strip().lower(),
                cutoff=cutoff,
            )

            await self.session.commit()

            return count

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
        min_salary: Decimal | None = None,
        max_salary: Decimal | None = None,
        salary_currency: str | None = None,
        employment_type: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Job]:
        """Return vacancies matching the requested filters."""
        if not 1 <= limit <= 100:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Limit must be between 1 and 100.",
            )

        if offset < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Offset cannot be negative.",
            )

        if (
            min_salary is not None
            and max_salary is not None
            and min_salary > max_salary
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="min_salary cannot exceed max_salary.",
            )

        # Salary values in different currencies must not be compared.
        if (
            min_salary is not None or max_salary is not None
        ) and not salary_currency:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=(
                    "salary_currency is required when filtering by salary."
                ),
            )

        if salary_currency:
            salary_currency = salary_currency.strip().upper()

        return await self.repository.list_jobs(
            query=query,
            location=location,
            source_id=source_id,
            status=status_filter,
            min_salary=min_salary,
            max_salary=max_salary,
            salary_currency=salary_currency,
            employment_type=employment_type,
            limit=limit,
            offset=offset,
        )