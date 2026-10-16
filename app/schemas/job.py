
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class JobCreate(BaseModel):
    """Validated vacancy data prepared for database storage."""

    model_config = ConfigDict(str_strip_whitespace=True)

    source_id: str = Field(min_length=1, max_length=100)
    source_name: str = Field(min_length=1, max_length=200)

    external_id: str | None = Field(default=None, max_length=255)

    title: str = Field(min_length=1, max_length=500)
    company: str | None = Field(default=None, max_length=255)
    location: str | None = Field(default=None, max_length=255)

    employment_type: str | None = Field(default=None, max_length=100)
    description: str | None = None

    salary_min: Decimal | None = Field(default=None, ge=0)
    salary_max: Decimal | None = Field(default=None, ge=0)

    salary_currency: str | None = Field(
        default=None,
        min_length=3,
        max_length=3,
    )
    salary_period: str | None = Field(default=None, max_length=30)

    original_url: str = Field(min_length=1, max_length=2048)
    published_at: datetime | None = None


class JobRead(BaseModel):
    """Vacancy data returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID

    source_id: str
    source_name: str
    external_id: str | None

    title: str
    company: str | None
    location: str | None
    employment_type: str | None
    description: str | None

    salary_min: Decimal | None
    salary_max: Decimal | None
    salary_currency: str | None
    salary_period: str | None

    original_url: str
    published_at: datetime | None

    status: str
    first_seen_at: datetime
    last_seen_at: datetime
    created_at: datetime
    updated_at: datetime


class JobListRead(BaseModel):
    """Short representation of a vacancy in search results."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_name: str
    title: str
    company: str | None = None
    location: str | None = None
    employment_type: str | None = None
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    salary_currency: str | None = None
    salary_period: str | None = None
    published_at: datetime | None = None
    original_url: str | None = None
    status: str