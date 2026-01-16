"""History API Schemas."""

from datetime import datetime
from pydantic import Field

from src.presentation.schemas.common import BaseSchema, PaginatedResponse


class TestRecordResponse(BaseSchema):
    """Test record response."""

    id: str
    user_id: str
    test_type: str
    provider: str
    input_text: str | None = None
    output_text: str | None = None
    latency_ms: int | None = None
    created_at: datetime
    metadata: dict = Field(default_factory=dict)


class TestRecordListResponse(PaginatedResponse):
    """Paginated list of test records."""

    records: list[TestRecordResponse]


class StatisticsResponse(BaseSchema):
    """Statistics response."""

    total_tests: int
    by_type: dict[str, int] = Field(
        default_factory=dict, description="Test count by type"
    )
    by_provider: dict[str, int] = Field(
        default_factory=dict, description="Test count by provider"
    )
    avg_latency_ms: float | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
