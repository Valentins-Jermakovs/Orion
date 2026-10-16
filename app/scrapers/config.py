from pydantic import BaseModel, ConfigDict, Field


class ScraperFieldConfig(BaseModel):
    """Configuration for extracting one field from HTML."""

    model_config = ConfigDict(extra="forbid")

    selector: str = Field(min_length=1)
    attribute: str | None = None
    required: bool = False


class PaginationConfig(BaseModel):
    """Configuration for navigating between result pages."""

    model_config = ConfigDict(extra="forbid")

    next_selector: str | None = None
    max_pages: int = Field(default=1, ge=1, le=100)


class SourceConfig(BaseModel):
    """Configuration for one job website."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    source_id: str = Field(alias="id", min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)

    enabled: bool = True

    start_urls: list[str] = Field(min_length=1)
    item_selector: str = Field(min_length=1)

    fields: dict[str, ScraperFieldConfig]

    pagination: PaginationConfig = Field(
        default_factory=PaginationConfig,
    )


class SourcesConfig(BaseModel):
    """Configuration containing all scraper sources."""

    model_config = ConfigDict(extra="forbid")

    sources: list[SourceConfig] = Field(default_factory=list)
