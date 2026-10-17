
# ==============================
# Third-party imports
# ==============================

from pydantic import BaseModel, Field


# ==============================
# System metrics
# ==============================

class SystemMetricsRead(BaseModel):
    """Represent resource usage metrics for the API process."""

    # CPU utilization percentage.
    cpu_percent: float = Field(ge=0)

    # Percentage of system memory used by the process.
    memory_percent: float = Field(ge=0)

    # Resident memory usage in megabytes.
    memory_used_mb: int = Field(ge=0)
