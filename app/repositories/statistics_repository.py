
# ==============================
# Third-party imports
# ==============================

from sqlalchemy import case, func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

# ==============================
# Application imports
# ==============================

from app.models import Job


# ==============================
# Statistics repository
# ==============================

class StatisticsRepository:
    """Retrieve vacancy statistics from the database."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session."""
        self.session = session

    # ==============================
    # Overview statistics
    # ==============================

    async def get_overview(self) -> dict[str, int]:
        """Return aggregated statistics for all vacancies."""
        statement = select(
            func.count(Job.id).label("total_jobs"),
            func.coalesce(
                func.sum(
                    case(
                        (Job.status == "active", 1),
                        else_=0,
                    )
                ),
                0,
            ).label("active_jobs"),
            func.coalesce(
                func.sum(
                    case(
                        (Job.status == "inactive", 1),
                        else_=0,
                    )
                ),
                0,
            ).label("inactive_jobs"),
            func.count(
                func.distinct(Job.source_id)
            ).label("sources_count"),
        )

        result = await self.session.exec(statement)
        row = result.one()

        return {
            "total_jobs": int(row.total_jobs),
            "active_jobs": int(row.active_jobs),
            "inactive_jobs": int(row.inactive_jobs),
            "sources_count": int(row.sources_count),
        }

    # ==============================
    # Statistics by source
    # ==============================

    async def get_by_source(self) -> list[dict[str, str | int]]:
        """Return vacancy counts grouped by source."""
        statement = (
            select(
                Job.source_id.label("source_id"),
                Job.source_name.label("source_name"),
                func.count(Job.id).label("total_jobs"),
                func.coalesce(
                    func.sum(
                        case(
                            (Job.status == "active", 1),
                            else_=0,
                        )
                    ),
                    0,
                ).label("active_jobs"),
                func.coalesce(
                    func.sum(
                        case(
                            (Job.status == "inactive", 1),
                            else_=0,
                        )
                    ),
                    0,
                ).label("inactive_jobs"),
            )
            .group_by(Job.source_id, Job.source_name)
            .order_by(
                func.count(Job.id).desc(),
                Job.source_name.asc(),
            )
        )

        result = await self.session.exec(statement)
        rows = result.all()

        return [
            {
                "source_id": row.source_id,
                "source_name": row.source_name,
                "total_jobs": int(row.total_jobs),
                "active_jobs": int(row.active_jobs),
                "inactive_jobs": int(row.inactive_jobs),
            }
            for row in rows
        ]
