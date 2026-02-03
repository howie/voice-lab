"""Music Generation API Schemas.

Feature: 012-music-generation
Pydantic schemas for music generation API requests and responses.
Supports multiple providers via MusicProviderEnum.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class MusicGenerationType(str, Enum):
    """Type of music generation."""

    SONG = "song"
    INSTRUMENTAL = "instrumental"
    LYRICS = "lyrics"


class MusicGenerationStatus(str, Enum):
    """Status of music generation job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MusicProviderEnum(str, Enum):
    """Supported music generation providers."""

    MUREKA = "mureka"
    SUNO = "suno"


class MusicModel(str, Enum):
    """Model selection (provider-specific)."""

    AUTO = "auto"
    MUREKA_01 = "mureka-01"
    V7_5 = "v7.5"
    V6 = "v6"


# =============================================================================
# Request Schemas
# =============================================================================


class InstrumentalRequest(BaseModel):
    """Request to submit instrumental/BGM generation."""

    prompt: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="場景/風格描述",
        examples=["magical fantasy forest, whimsical, children friendly"],
    )
    model: MusicModel = Field(
        default=MusicModel.AUTO,
        description="模型選擇",
    )
    provider: MusicProviderEnum = Field(
        default=MusicProviderEnum.MUREKA,
        description="音樂生成服務提供者",
    )


class SongRequest(BaseModel):
    """Request to submit song generation."""

    prompt: str | None = Field(
        default=None,
        max_length=500,
        description="風格描述",
        examples=["pop, cheerful, children, chinese, female vocal"],
    )
    lyrics: str | None = Field(
        default=None,
        max_length=3000,
        description="歌詞內容",
    )
    model: MusicModel = Field(
        default=MusicModel.AUTO,
        description="模型選擇",
    )
    provider: MusicProviderEnum = Field(
        default=MusicProviderEnum.MUREKA,
        description="音樂生成服務提供者",
    )


class LyricsRequest(BaseModel):
    """Request to submit lyrics generation."""

    prompt: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="主題描述",
        examples=["太空探險"],
    )
    provider: MusicProviderEnum = Field(
        default=MusicProviderEnum.MUREKA,
        description="音樂生成服務提供者",
    )


class ExtendLyricsRequest(BaseModel):
    """Request to extend existing lyrics."""

    lyrics: str = Field(
        ...,
        max_length=3000,
        description="現有歌詞",
    )
    prompt: str | None = Field(
        default=None,
        max_length=200,
        description="延伸方向描述",
    )
    provider: MusicProviderEnum = Field(
        default=MusicProviderEnum.MUREKA,
        description="音樂生成服務提供者",
    )


# =============================================================================
# Response Schemas
# =============================================================================


class MusicJobResponse(BaseModel):
    """Response for a music generation job."""

    id: UUID
    type: MusicGenerationType
    status: MusicGenerationStatus
    provider: MusicProviderEnum = MusicProviderEnum.MUREKA
    prompt: str | None = None
    lyrics: str | None = None
    model: MusicModel
    result_url: str | None = None
    cover_url: str | None = None
    generated_lyrics: str | None = None
    duration_ms: int | None = None
    title: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None


class MusicJobListResponse(BaseModel):
    """Response for a list of music generation jobs."""

    items: list[MusicJobResponse]
    total: int
    limit: int
    offset: int


class QuotaStatusResponse(BaseModel):
    """Response for user's quota status."""

    daily_used: int
    daily_limit: int
    monthly_used: int
    monthly_limit: int
    concurrent_jobs: int
    max_concurrent_jobs: int
    can_submit: bool


class ErrorResponse(BaseModel):
    """Error response schema."""

    code: str
    message: str
    details: dict | None = None
