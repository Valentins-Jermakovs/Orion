
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ScraperFieldConfig(BaseModel):
    """Configuration for extracting one field from HTML."""

    model_config = ConfigDict(extra="forbid")

    selector: str | None = Field(default=None, min_length=1)
    attribute: str | None = None
    value: str | None = None
    required: bool = False

    @model_validator(mode="after")
    def validate_configuration(self) -> "ScraperFieldConfig":
        """Require either a selector or a constant value."""
        if (self.selector is None) == (self.value is None):
            raise ValueError(
                "Specify exactly one of 'selector' or 'value'."
            )

        if self.attribute and not self.selector:
            raise ValueError(
                "An attribute requires a CSS selector."
            )

        return self


class PaginationConfig(BaseModel):
    """Configuration for navigating between result pages."""

    model_config = ConfigDict(extra="forbid")

    next_selector: str | None = None
    max_pages: int = Field(default=1, ge=1, le=100)


class DetailPageConfig(BaseModel):
    """Configuration for extracting fields from a vacancy page."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = False
    max_details: int = Field(default=3, ge=0, le=100)

    row_selector: str = Field(
        default=r"div.flex.gap-2\.5",
        min_length=1,
    )

    label_selector: str = Field(
        default="div:nth-child(2) > div:first-child",
        min_length=1,
    )

    value_selector: str = Field(
        default="div:nth-child(2) > div.font-semibold",
        min_length=1,
    )

    # Maps an application field to its label on the source website.
    fields: dict[str, str] = Field(default_factory=dict)


class SourceConfig(BaseModel):
    """Configuration for one job website."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )

    source_id: str = Field(
        alias="id",
        min_length=1,
        max_length=100,
    )

    name: str = Field(min_length=1, max_length=200)
    enabled: bool = True

    start_urls: list[str] = Field(min_length=1)
    item_selector: str = Field(min_length=1)

    fields: dict[str, ScraperFieldConfig]

    pagination: PaginationConfig = Field(
        default_factory=PaginationConfig,
    )

    detail_page: DetailPageConfig = Field(
        default_factory=DetailPageConfig,
    )


class SourcesConfig(BaseModel):
    """Configuration containing all scraper sources."""

    model_config = ConfigDict(extra="forbid")

    sources: list[SourceConfig] = Field(default_factory=list)
