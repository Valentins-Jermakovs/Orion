
# ==============================
# Third-party imports
# ==============================

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


# ==============================
# Application settings
# ==============================

class Settings(BaseSettings):
    """Load and validate application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==============================
    # PostgreSQL settings
    # ==============================

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str
    postgres_user: str
    postgres_password: SecretStr

    # ==============================
    # Redis settings
    # ==============================

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: SecretStr | None = None

    # ==============================
    # Scraper settings
    # ==============================

    scrape_api_key: SecretStr
    scrape_interval_seconds: int = 3600

    # ==============================
    # JWT settings
    # ==============================

    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"


# ==============================
# Settings instance
# ==============================

settings = Settings()
