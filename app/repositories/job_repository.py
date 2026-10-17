# ==============================
# Library imports
# ==============================

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, or_, update
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession


# ==============================
# Application imports
# ==============================

from app.models import Job


# ==============================
# Job repository
# ==============================

class JobRepository:
    """Provide database operations for job vacancies."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session."""
        self.session = session

    # ==============================
    # Retrieve vacancies
    # ==============================

    async def get_by_id(self, job_id: UUID) -> Job | None:
        """Find a vacancy by its internal ID."""
        statement = select(Job).where(Job.id == job_id)
        result = await self.session.exec(statement)

        return result.first()

    async def get_by_deduplication_key(
        self,
        deduplication_key: str,
    ) -> Job | None:
        """Find a vacancy by its unique deduplication key."""
        statement = select(Job).where(
            Job.deduplication_key == deduplication_key
        )
        result = await self.session.exec(statement)

        return result.first()

    async def list_jobs(
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
        statement = select(Job).where(Job.status == status)

        # Search vacancy titles, company names, and descriptions.
        if query:
            search_term = f"%{query.strip()}%"
            statement = statement.where(
                or_(
                    Job.title.ilike(search_term),
                    Job.company.ilike(search_term),
                    Job.description.ilike(search_term),
                )
            )

        # Filter by location, source, and employment type.
        if location:
            statement = statement.where(
                Job.location.ilike(f"%{location.strip()}%")
            )

        if source_id:
            statement = statement.where(
                Job.source_id == source_id.strip().lower()
            )

        if employment_type:
            statement = statement.where(
                Job.employment_type.ilike(
                    f"%{employment_type.strip()}%"
                )
            )

        # Match the requested salary currency.
        if salary_currency:
            statement = statement.where(
                Job.salary_currency == salary_currency.strip().upper()
            )

        # The vacancy range must reach the requested minimum salary.
        if min_salary is not None:
            statement = statement.where(
                or_(
                    Job.salary_max >= min_salary,
                    and_(
                        Job.salary_max.is_(None),
                        Job.salary_min >= min_salary,
                    ),
                )
            )

        # The vacancy range must start at or below the requested maximum.
        if max_salary is not None:
            statement = statement.where(
                or_(
                    Job.salary_min <= max_salary,
                    and_(
                        Job.salary_min.is_(None),
                        Job.salary_max <= max_salary,
                    ),
                )
            )

        # Show the newest published vacancies first.
        statement = (
            statement
            .order_by(
                Job.published_at.desc().nullslast(),
                Job.first_seen_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.exec(statement)

        return list(result.all())

    # ==============================
    # Insert or update vacancies
    # ==============================

    async def upsert(self, job: Job) -> Job:
        """Insert a vacancy or update an existing matching record."""
        job_data = job.model_dump()
        statement = postgresql_insert(Job).values(job_data)

        # Preserve the original ID, deduplication key, and creation dates.
        immutable_fields = {
            "id",
            "deduplication_key",
            "first_seen_at",
            "created_at",
        }

        update_values = {
            field: getattr(statement.excluded, field)
            for field in job_data
            if field not in immutable_fields
        }

        update_values["updated_at"] = func.now()

        statement = (
            statement
            .on_conflict_do_update(
                index_elements=[Job.deduplication_key],
                set_=update_values,
            )
            .returning(Job)
            .execution_options(populate_existing=True)
        )

        result = await self.session.exec(statement)

        return result.scalar_one()

    # ==============================
    # Vacancy lifecycle
    # ==============================

    async def mark_not_seen_inactive(
        self,
        source_id: str,
        cutoff: datetime,
    ) -> int:
        """Deactivate active vacancies not seen in a completed scrape."""
        statement = (
            update(Job)
            .where(
                Job.source_id == source_id,
                Job.status == "active",
                Job.last_seen_at < cutoff,
            )
            .values(
                status="inactive",
                updated_at=func.now(),
            )
        )

        result = await self.session.exec(statement)

        return result.rowcount or 0
