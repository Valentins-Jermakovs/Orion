
from pydantic import BaseModel, ConfigDict, Field


class ScrapedJob(BaseModel):
    """Raw vacancy data extracted from a website."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="ignore",
    )

    external_id: str | None = Field(
        default=None,
        max_length=255,
    )

    title: str = Field(
        min_length=1,
        max_length=500,
    )

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

    # Salary values remain strings until they are normalized.
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

    original_url: str = Field(
        min_length=1,
        max_length=2048,
    )

    # The original date representation may differ between websites.
    published_at: str | None = None


class ScrapeResult(BaseModel):
    """Result of collecting vacancies from one source."""

    source_id: str
    source_name: str

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
