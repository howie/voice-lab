"""Common schema definitions."""

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class ErrorResponse(BaseSchema):
    """Standard error response."""

    error: str
    detail: str | None = None
    code: str | None = None


class PaginatedResponse(BaseSchema):
    """Base for paginated responses."""

    total: int
    limit: int
    offset: int
    has_more: bool
