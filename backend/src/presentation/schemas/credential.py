"""Credential API Schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AddCredentialRequest(BaseModel):
    """Request schema for adding a new provider credential."""

    provider: str = Field(
        ...,
        description="Provider identifier (elevenlabs, azure, gemini)",
        examples=["elevenlabs"],
    )
    api_key: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="Provider API key",
    )
    selected_model_id: str | None = Field(
        default=None,
        description="Optional model to select",
    )

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate provider is one of supported providers."""
        supported = ["elevenlabs", "azure", "gemini"]
        if v.lower() not in supported:
            raise ValueError(f"Provider must be one of: {', '.join(supported)}")
        return v.lower()


class UpdateCredentialRequest(BaseModel):
    """Request schema for updating a credential."""

    api_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="New API key (optional, triggers revalidation)",
    )
    selected_model_id: str | None = Field(
        default=None,
        description="Model to select",
    )


class CredentialSummary(BaseModel):
    """Summary view of a credential (for list endpoints)."""

    id: UUID
    provider: str
    provider_display_name: str
    masked_key: str = Field(examples=["****abc1"])
    is_valid: bool
    selected_model_id: str | None = None
    last_validated_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CredentialResponse(CredentialSummary):
    """Full credential response (includes updated_at)."""

    updated_at: datetime

    model_config = {"from_attributes": True}


class QuotaInfo(BaseModel):
    """Quota information from provider."""

    character_count: int | None = Field(
        default=None, description="Characters used in current period"
    )
    character_limit: int | None = Field(
        default=None, description="Character limit for current tier"
    )
    remaining_characters: int | None = Field(default=None, description="Remaining characters")
    tier: str | None = Field(default=None, description="Subscription tier name")


class ValidationResult(BaseModel):
    """Result of credential validation."""

    is_valid: bool
    validated_at: datetime | None = None
    error_message: str | None = None
    quota_info: QuotaInfo | None = None


class ValidationError(BaseModel):
    """Error response for validation failures."""

    error: str = "validation_failed"
    message: str = "API key validation failed"
    details: dict | None = None


class CredentialListResponse(BaseModel):
    """Response schema for listing credentials."""

    credentials: list[CredentialSummary]
