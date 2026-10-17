
# ==============================
# Library imports
# ==============================

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


# ==============================
# Application settings
# ==============================

class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # .env file configuration.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # PostgreSQL connection settings.
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str
    postgres_user: str
    postgres_password: SecretStr

    # Redis connection settings.
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: SecretStr | None = None

    # API key required to trigger a scraping operation.
    scrape_api_key: SecretStr

    # Delay between consecutive scraping cycles in seconds.
    scrape_interval_seconds: int = 3600


# ==============================
# Settings instance
# ==============================

settings = Settings()
