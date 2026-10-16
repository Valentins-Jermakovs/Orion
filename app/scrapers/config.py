from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ScraperFieldConfig(BaseModel):
    """Configuration for extracting a field from CSV or JSON data."""

    model_config = ConfigDict(extra="forbid")

    column: str | None = Field(default=None, min_length=1)
    json_path: str | None = Field(default=None, min_length=1)
    value: str | None = None
    required: bool = False

    @model_validator(mode="after")
    def validate_extraction_method(self) -> "ScraperFieldConfig":
        """Require exactly one extraction method for each field."""
        methods = (
            self.column,
            self.json_path,
            self.value,
        )

        configured_methods = sum(
            method is not None
            for method in methods
        )

        if configured_methods != 1:
            raise ValueError(
                "Exactly one of 'column', 'json_path' or 'value' "
                "must be configured."
            )

        return self


class SourceConfig(BaseModel):
    """Configuration for a CSV or JSON vacancy source."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    source_id: str = Field(alias="id", min_length=1)
    name: str
    enabled: bool = True
    scraper_type: Literal["csv", "json"]
    complete_snapshot: bool = False
    start_urls: list[str] = Field(min_length=1)
    fields: dict[str, ScraperFieldConfig] = Field(
        default_factory=dict
    )


class SourcesConfig(BaseModel):
    """Configuration containing all vacancy sources."""

    model_config = ConfigDict(extra="forbid")

    sources: list[SourceConfig]