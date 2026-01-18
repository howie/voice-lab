"""Provider API Schemas."""

from pydantic import BaseModel, Field


class ProviderModel(BaseModel):
    """Schema for a provider's model/voice."""

    id: str
    name: str
    language: str
    gender: str | None = None
    description: str | None = None


class Provider(BaseModel):
    """Schema for a TTS/STT provider."""

    id: str
    name: str
    display_name: str
    type: list[str] = Field(description="Supported types: 'tts', 'stt', or both")
    is_active: bool

    model_config = {"from_attributes": True}


class ProviderListResponse(BaseModel):
    """Response schema for listing providers."""

    providers: list[Provider]


class ProviderModelsResponse(BaseModel):
    """Response schema for listing provider models."""

    models: list[ProviderModel]


class ErrorResponse(BaseModel):
    """Generic error response schema."""

    error: str
    message: str
