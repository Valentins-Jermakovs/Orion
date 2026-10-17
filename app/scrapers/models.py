
# ==============================
# Third-party imports
# ==============================

from pydantic import BaseModel, ConfigDict, Field


# ==============================
# Scraped vacancy model
# ==============================

class ScrapedJob(BaseModel):
    """Represent raw vacancy data extracted by a scraper."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="ignore",
    )

    # ==============================
    # Vacancy identification
    # ==============================

    external_id: str | None = Field(
        default=None,
        max_length=255,
    )

    title: str = Field(
        min_length=1,
        max_length=500,
    )

    # ==============================
    # Vacancy details
    # ==============================

    company: str | None = Field(
        default=None,
        max_length=255,
    )

    location: str | None = Field(
        default=None,
        max_length=255,
    )

    employment_type: str | None = Field(
        default=None,
        max_length=100,
    )

    description: str | None = None

    # ==============================
    # Salary information
    # ==============================

    # Keep salary values as strings until the service normalizes them.
    salary_min: str | None = None
    salary_max: str | None = None

    salary_currency: str | None = Field(
        default=None,
        max_length=3,
    )

    salary_period: str | None = Field(
        default=None,
        max_length=30,
    )

    # ==============================
    # Vacancy metadata
    # ==============================

    original_url: str = Field(
        min_length=1,
        max_length=2048,
    )

    # Preserve the original date representation for later normalization.
    published_at: str | None = None


# ==============================
# Scraping result model
# ==============================

class ScrapeResult(BaseModel):
    """Represent the result of collecting vacancies from one source."""

    # ==============================
    # Source information
    # ==============================

    source_id: str
    source_name: str

    # ==============================
    # Scraping output
    # ==============================

    jobs: list[ScrapedJob] = Field(
        default_factory=list,
    )

    pages_processed: int = Field(
        default=0,
        ge=0,
    )

    errors: list[str] = Field(
        default_factory=list,
    )
