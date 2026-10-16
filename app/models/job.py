
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Text
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    """Return the current UTC date and time."""
    return datetime.now(timezone.utc)


class Job(SQLModel, table=True):
    """Database model representing a collected job vacancy."""

    __tablename__ = "jobs"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )

    # Source identification and duplicate prevention.
    source_id: str = Field(
        index=True,
        max_length=100,
    )
    source_name: str = Field(
        max_length=200,
    )
    external_id: str | None = Field(
        default=None,
        max_length=255,
    )
    deduplication_key: str = Field(
        unique=True,
        index=True,
        max_length=128,
    )

    # Basic vacancy information.
    title: str = Field(
        index=True,
        max_length=500,
    )
    company: str | None = Field(
        default=None,
        index=True,
        max_length=255,
    )
    location: str | None = Field(
        default=None,
        index=True,
        max_length=255,
    )
    employment_type: str | None = Field(
        default=None,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        sa_type=Text,
    )

    # Salary information.
    salary_min: Decimal | None = Field(
        default=None,
        max_digits=12,
        decimal_places=2,
    )
    salary_max: Decimal | None = Field(
        default=None,
        max_digits=12,
        decimal_places=2,
    )
    salary_currency: str | None = Field(
        default=None,
        max_length=3,
    )
    salary_period: str | None = Field(
        default=None,
        max_length=30,
    )

    # Original vacancy URL and publication date.
    original_url: str = Field(
        max_length=2048,
    )
    published_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        index=True,
    )

    # Collection and lifecycle tracking.
    status: str = Field(
        default="active",
        index=True,
        max_length=20,
    )
    first_seen_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
    )
    last_seen_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
        index=True,
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_type=DateTime(timezone=True),
    )
