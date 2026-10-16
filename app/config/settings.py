from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Orion Job Aggregator"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    database_url: SecretStr
    redis_url: SecretStr
    scrape_api_key: SecretStr

    scrape_interval_seconds: int = 3600
    request_timeout_seconds: int = 20
    max_pages_per_source: int = 5
    job_expiry_days: int = 30


@lru_cache
def get_settings() -> Settings:
    """Return a cached application configuration."""
    return Settings()


settings = get_settings()