from pathlib import Path

import yaml
from pydantic import ValidationError

from app.scrapers.config import SourcesConfig


def load_sources_config(
    config_path: Path = Path("sources.yaml"),
) -> SourcesConfig:
    """Load and validate scraper source configurations."""
    if not config_path.is_file():
        raise FileNotFoundError(
            f"Scraper configuration not found: {config_path}"
        )

    with config_path.open("r", encoding="utf-8") as config_file:
        data = yaml.safe_load(config_file) or {}

    try:
        config = SourcesConfig.model_validate(data)
    except ValidationError as error:
        raise ValueError(
            f"Invalid scraper configuration: {error}"
        ) from error

    source_ids: set[str] = set()

    for source in config.sources:
        source_id = source.source_id.strip().lower()

        if source_id in source_ids:
            raise ValueError(
                f"Duplicate scraper source ID: {source.source_id}"
            )

        source_ids.add(source_id)

        if "title" not in source.fields:
            raise ValueError(
                f"Source '{source.source_id}' must define a title field."
            )

        if "url" not in source.fields:
            raise ValueError(
                f"Source '{source.source_id}' must define a url field."
            )

    return config


def get_enabled_sources(
    config: SourcesConfig,
) -> list:
    """Return only enabled scraper sources."""
    return [
        source
        for source in config.sources
        if source.enabled
    ]