
from uuid import UUID

from sqlalchemy import func, or_
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.job import Job


class JobRepository:
    """Provide database operations for job vacancies."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, job_id: UUID) -> Job | None:
        """Find a vacancy by its internal ID."""
        statement = select(Job).where(Job.id == job_id)

        result = await self.session.exec(statement)

        return result.first()

    async def get_by_deduplication_key(
        self,
        deduplication_key: str,
    ) -> Job | None:
        """Find a vacancy using its unique deduplication key."""
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
        limit: int = 20,
        offset: int = 0,
    ) -> list[Job]:
        """Return vacancies matching the supplied filters."""
        statement = select(Job).where(Job.status == status)

        if query:
            search_term = f"%{query.strip()}%"

            statement = statement.where(
                or_(
                    Job.title.ilike(search_term),
                    Job.company.ilike(search_term),
                    Job.description.ilike(search_term),
                )
            )

        if location:
            statement = statement.where(
                Job.location.ilike(f"%{location.strip()}%")
            )

        if source_id:
            statement = statement.where(
                Job.source_id == source_id
            )

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

    async def upsert(self, job: Job) -> Job:
        """Insert a vacancy or update it if its key already exists."""
        job_data = job.model_dump()

        statement = postgresql_insert(Job).values(job_data)

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
