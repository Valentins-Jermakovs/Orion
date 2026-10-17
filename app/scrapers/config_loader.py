
# ==============================
# Library imports
# ==============================

import logging
from pathlib import Path

import yaml


# ==============================
# Application imports
# ==============================

from app.scrapers.config import SourceConfig, SourcesConfig


# ==============================
# Logger
# ==============================

logger = logging.getLogger(__name__)


# ==============================
# Configuration loading
# ==============================

def load_sources_config(
    config_path: Path = Path("sources.yaml"),
) -> SourcesConfig:
    """Load and validate the configured vacancy sources."""

    # Ensure the configuration file exists.
    if not config_path.is_file():
        raise FileNotFoundError(
            f"Source configuration file not found: {config_path}"
        )

    # Load the YAML configuration safely.
    try:
        with config_path.open("r", encoding="utf-8") as file:
            raw_config = yaml.safe_load(file)

    except yaml.YAMLError as error:
        raise ValueError(
            f"Could not parse source configuration: {error}"
        ) from error

    # The root YAML element must be a mapping.
    if not isinstance(raw_config, dict):
        raise ValueError(
            "The source configuration must contain a YAML mapping."
        )

    # Validate the configuration structure and field types.
    config = SourcesConfig.model_validate(raw_config)

    # Ensure that every source has a unique identifier.
    source_ids: set[str] = set()

    for source in config.sources:
        if source.source_id in source_ids:
            raise ValueError(
                f"Duplicate source ID: '{source.source_id}'."
            )

        source_ids.add(source.source_id)

        _validate_source_fields(source)

    logger.info(
        "Loaded %s scraper sources, %s enabled.",
        len(config.sources),
        len(get_enabled_sources(config)),
    )

    return config


# ==============================
# Source validation
# ==============================

def _validate_source_fields(source: SourceConfig) -> None:
    """Validate the fields required by CSV and JSON sources."""

    # Every source must identify a vacancy by its title and URL.
    for field_name in ("title", "url"):
        field_config = source.fields.get(field_name)

        if field_config is None:
            raise ValueError(
                f"Source '{source.source_id}' must define "
                f"the '{field_name}' field."
            )

        if not field_config.required:
            raise ValueError(
                f"Field '{field_name}' must be required "
                f"for source '{source.source_id}'."
            )

    # Ensure that every field uses an extraction method supported
    # by the configured source format.
    for field_name, field_config in source.fields.items():
        if source.scraper_type == "csv":
            if (
                field_config.column is None
                and field_config.value is None
            ):
                raise ValueError(
                    f"CSV field '{field_name}' in source "
                    f"'{source.source_id}' must define "
                    "'column' or 'value'."
                )

        elif source.scraper_type == "json":
            if (
                field_config.json_path is None
                and field_config.value is None
            ):
                raise ValueError(
                    f"JSON field '{field_name}' in source "
                    f"'{source.source_id}' must define "
                    "'json_path' or 'value'."
                )


# ==============================
# Enabled sources
# ==============================

def get_enabled_sources(
    config: SourcesConfig,
) -> list[SourceConfig]:
    """Return the sources enabled in the configuration."""
    return [
        source
        for source in config.sources
        if source.enabled
    ]
