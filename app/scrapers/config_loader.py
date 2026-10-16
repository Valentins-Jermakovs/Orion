import logging
from pathlib import Path

import yaml

from app.scrapers.config import SourceConfig, SourcesConfig


logger = logging.getLogger(__name__)


def load_sources_config(
    config_path: Path = Path("sources.yaml"),
) -> SourcesConfig:
    """Load and validate scraper source configurations."""
    if not config_path.is_file():
        raise FileNotFoundError(
            f"Source configuration file not found: {config_path}"
        )

    try:
        with config_path.open("r", encoding="utf-8") as file:
            raw_config = yaml.safe_load(file)

    except yaml.YAMLError as error:
        raise ValueError(
            f"Could not parse source configuration: {error}"
        ) from error

    if not isinstance(raw_config, dict):
        raise ValueError(
            "The source configuration must contain a YAML mapping."
        )

    config = SourcesConfig.model_validate(raw_config)

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


def _validate_source_fields(source: SourceConfig) -> None:
    """Check that a source has the field mappings it requires."""
    if source.scraper_type == "html":
        required_fields = ("title", "url")

        for field_name in required_fields:
            field_config = source.fields.get(field_name)

            if field_config is None:
                raise ValueError(
                    f"HTML source '{source.source_id}' must define "
                    f"the '{field_name}' field."
                )

            if not field_config.required:
                raise ValueError(
                    f"Field '{field_name}' must be marked as required "
                    f"for HTML source '{source.source_id}'."
                )

    else:
        if "title" not in source.fields:
            raise ValueError(
                f"Source '{source.source_id}' must define a title "
                f"field mapping."
            )


def get_enabled_sources(
    config: SourcesConfig,
) -> list[SourceConfig]:
    """Return only the sources enabled in the configuration."""
    return [
        source
        for source in config.sources
        if source.enabled
    ]