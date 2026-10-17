
# ==============================
# Library imports
# ==============================

from decimal import Decimal
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession


# ==============================
# Application imports
# ==============================

from app.models import Job
from app.schemas import JobCreate
from app.services.job_service import JobService


# ==============================
# Job facade
# ==============================

class JobFacade:
    """Provide a single entry point for job operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the facade with a database session."""
        self.job_service = JobService(session)

    # ==============================
    # Create or update vacancies
    # ==============================

    async def create_or_update(self, job_data: JobCreate) -> Job:
        """Create a vacancy or update an existing one."""
        return await self.job_service.create_or_update(job_data)

    # ==============================
    # Retrieve vacancies
    # ==============================

    async def get_job(self, job_id: UUID) -> Job:
        """Return a vacancy by its internal ID."""
        return await self.job_service.get_job(job_id)

    async def get_jobs(
        self,
        query: str | None = None,
        location: str | None = None,
        source_id: str | None = None,
        status: str = "active",
        min_salary: Decimal | None = None,
        max_salary: Decimal | None = None,
        salary_currency: str | None = None,
        employment_type: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Job]:
        """Return vacancies matching the requested filters."""
        return await self.job_service.get_jobs(
            query=query,
            location=location,
            source_id=source_id,
            status_filter=status,
            min_salary=min_salary,
            max_salary=max_salary,
            salary_currency=salary_currency,
            employment_type=employment_type,
            limit=limit,
            offset=offset,
        )
