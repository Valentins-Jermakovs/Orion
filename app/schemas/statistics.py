
# ==============================
# Third-party imports
# ==============================

from pydantic import BaseModel, Field


# ==============================
# Overview statistics
# ==============================

class StatisticsOverviewRead(BaseModel):
    """Represent overall vacancy statistics."""

    # Total number of vacancies stored in the database.
    total_jobs: int = Field(ge=0)

    # Number of currently active vacancies.
    active_jobs: int = Field(ge=0)

    # Number of inactive vacancies.
    inactive_jobs: int = Field(ge=0)

    # Number of distinct sources represented in the database.
    sources_count: int = Field(ge=0)


# ==============================
# Source statistics
# ==============================

class SourceStatisticsRead(BaseModel):
    """Represent vacancy statistics for a single source."""

    # Source identification.
    source_id: str
    source_name: str

    # Vacancy counts for this source.
    total_jobs: int = Field(ge=0)
    active_jobs: int = Field(ge=0)
    inactive_jobs: int = Field(ge=0)
