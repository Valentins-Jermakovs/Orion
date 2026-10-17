
# ==============================
# Library imports
# ==============================

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ==============================
# Scraper field configuration
# ==============================

class ScraperFieldConfig(BaseModel):
    """Configure how a field is extracted from CSV or JSON data."""

    model_config = ConfigDict(extra="forbid")

    # CSV column name.
    column: str | None = Field(default=None, min_length=1)

    # Dot-separated path to a value in a JSON object.
    json_path: str | None = Field(default=None, min_length=1)

    # Constant value assigned to the field.
    value: str | None = None

    # Indicate whether the field must be present in the source data.
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


# ==============================
# Source configuration
# ==============================

class SourceConfig(BaseModel):
    """Configure a vacancy source and its extraction rules."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    # Unique source identifier, provided as 'id' in YAML.
    source_id: str = Field(alias="id", min_length=1)

    # Human-readable source name.
    name: str

    # Enable or disable collection from this source.
    enabled: bool = True

    # Data format supported by the scraper registry.
    scraper_type: Literal["csv", "json"]

    # Whether the source provides a complete vacancy snapshot.
    complete_snapshot: bool = False

    # URLs from which source data is downloaded.
    start_urls: list[str] = Field(min_length=1)

    # Mapping between application fields and source fields.
    fields: dict[str, ScraperFieldConfig] = Field(
        default_factory=dict
    )


# ==============================
# Sources configuration
# ==============================

class SourcesConfig(BaseModel):
    """Store the configuration of all vacancy sources."""

    model_config = ConfigDict(extra="forbid")

    # Configured vacancy sources.
    sources: list[SourceConfig]
