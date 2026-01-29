"""Voice Customization API Schemas.

Feature: 013-tts-role-mgmt
Pydantic schemas for voice customization API endpoints.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class VoiceCustomizationSchema(BaseModel):
    """Schema for a voice customization record."""

    id: int = Field(..., description="Database ID")
    voice_cache_id: str = Field(..., description="Associated voice cache ID", examples=["gemini:Puck"])
    custom_name: str | None = Field(
        None,
        max_length=50,
        description="User-defined display name",
        examples=["陽光男孩聲"],
    )
    is_favorite: bool = Field(False, description="Favorite status")
    is_hidden: bool = Field(False, description="Hidden status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class VoiceCustomizationDefaultSchema(BaseModel):
    """Schema for default values when no customization exists."""

    voice_cache_id: str = Field(..., description="Voice cache ID")
    custom_name: None = Field(None, description="No custom name set")
    is_favorite: bool = Field(False, description="Not favorited")
    is_hidden: bool = Field(False, description="Not hidden")


class UpdateVoiceCustomizationRequest(BaseModel):
    """Request schema for updating a voice customization."""

    custom_name: str | None = Field(
        None,
        max_length=50,
        description="Set to null to clear custom name",
    )
    is_favorite: bool | None = Field(None, description="Set favorite status")
    is_hidden: bool | None = Field(None, description="Set hidden status")

    class Config:
        json_schema_extra = {
            "example": {
                "custom_name": "陽光男孩聲",
                "is_favorite": True,
                "is_hidden": False,
            }
        }


class BulkUpdateItem(BaseModel):
    """Single item in a bulk update request."""

    voice_cache_id: str = Field(..., description="Voice cache ID to update")
    custom_name: str | None = Field(None, max_length=50, description="Custom name")
    is_favorite: bool | None = Field(None, description="Favorite status")
    is_hidden: bool | None = Field(None, description="Hidden status")


class BulkUpdateVoiceCustomizationRequest(BaseModel):
    """Request schema for bulk updating voice customizations."""

    updates: list[BulkUpdateItem] = Field(
        ...,
        max_length=50,
        description="List of updates (max 50)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "updates": [
                    {"voice_cache_id": "gemini:Puck", "is_favorite": True},
                    {"voice_cache_id": "gemini:Kore", "custom_name": "溫柔女聲"},
                    {"voice_cache_id": "voai:tw-male-01", "is_hidden": True},
                ]
            }
        }


class BulkUpdateFailure(BaseModel):
    """Failed item in a bulk update result."""

    voice_cache_id: str = Field(..., description="Voice cache ID that failed")
    error: str = Field(..., description="Error message")


class BulkUpdateResultSchema(BaseModel):
    """Schema for bulk update result."""

    updated_count: int = Field(..., description="Number of successfully updated records")
    failed: list[BulkUpdateFailure] = Field(
        default_factory=list,
        description="List of failed updates",
    )


class VoiceProfileSchema(BaseModel):
    """Schema for voice profile data from voice_cache."""

    id: str = Field(..., description="Voice ID (provider:voice_id)", examples=["gemini:Puck"])
    provider: str = Field(..., description="Provider name", examples=["gemini"])
    voice_id: str = Field(..., description="Provider-specific voice ID", examples=["Puck"])
    name: str = Field(..., description="Original voice name", examples=["Puck"])
    language: str = Field(..., description="Language code", examples=["zh-TW"])
    gender: str | None = Field(None, description="Voice gender", examples=["male"])
    age_group: str | None = Field(None, description="Age group", examples=["young"])
    styles: list[str] = Field(default_factory=list, description="Available styles")
    use_cases: list[str] = Field(default_factory=list, description="Recommended use cases")
    sample_audio_url: str | None = Field(None, description="Sample audio URL")
    is_deprecated: bool = Field(False, description="Whether voice is deprecated")

    class Config:
        from_attributes = True


class VoiceWithCustomizationSchema(BaseModel):
    """Schema for voice profile merged with customization data."""

    id: str = Field(..., description="Voice ID (provider:voice_id)")
    provider: str = Field(..., description="Provider name")
    voice_id: str = Field(..., description="Provider-specific voice ID")
    name: str = Field(..., description="Original voice name")
    display_name: str = Field(..., description="Display name (custom or original)")
    language: str = Field(..., description="Language code")
    gender: str | None = Field(None, description="Voice gender")
    age_group: str | None = Field(None, description="Age group")
    styles: list[str] = Field(default_factory=list, description="Available styles")
    use_cases: list[str] = Field(default_factory=list, description="Recommended use cases")
    sample_audio_url: str | None = Field(None, description="Sample audio URL")
    is_deprecated: bool = Field(False, description="Whether voice is deprecated")
    is_favorite: bool = Field(False, description="Favorite status")
    is_hidden: bool = Field(False, description="Hidden status")

    class Config:
        from_attributes = True


class VoiceListResponseSchema(BaseModel):
    """Schema for paginated voice list response."""

    items: list[VoiceWithCustomizationSchema] = Field(..., description="List of voices")
    total: int = Field(..., description="Total count before pagination")
    limit: int = Field(..., description="Requested limit")
    offset: int = Field(..., description="Requested offset")


class ValidationErrorDetail(BaseModel):
    """Schema for validation error detail."""

    loc: list[str] = Field(..., description="Error location")
    msg: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")


class ValidationErrorSchema(BaseModel):
    """Schema for validation error response."""

    detail: list[ValidationErrorDetail] = Field(..., description="Validation errors")


class NotFoundErrorSchema(BaseModel):
    """Schema for not found error response."""

    detail: str = Field(..., description="Error message", examples=["Voice not found: gemini:InvalidVoice"])
