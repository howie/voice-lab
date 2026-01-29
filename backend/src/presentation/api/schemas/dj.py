"""DJ API Schemas for Magic DJ Controller.

Feature: 011-magic-dj-audio-features
Phase 3: Backend Storage Support

This module defines Pydantic schemas for DJ-related API endpoints.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.domain.entities.dj import DJTrackSource, DJTrackType

# =============================================================================
# Settings Schemas
# =============================================================================


class DJSettingsSchema(BaseModel):
    """Schema for DJ preset settings."""

    master_volume: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Master volume level (0.0 to 1.0)",
    )
    time_warning_at: int = Field(
        default=1500,
        ge=0,
        description="Seconds before showing time warning (default: 1500 = 25min)",
    )
    session_time_limit: int = Field(
        default=1800,
        ge=0,
        description="Maximum session duration in seconds (default: 1800 = 30min)",
    )
    ai_response_timeout: int = Field(
        default=10,
        ge=1,
        le=60,
        description="AI response timeout in seconds (default: 10)",
    )
    auto_play_filler: bool = Field(
        default=True,
        description="Whether to auto-play filler sound while waiting",
    )


# =============================================================================
# Preset Schemas
# =============================================================================


class CreatePresetRequest(BaseModel):
    """Request schema for creating a new preset."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Preset display name",
        examples=["兒童互動測試"],
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="Optional description",
        examples=["4-6歲兒童語音互動研究"],
    )
    is_default: bool = Field(
        default=False,
        description="Set as default preset",
    )
    settings: DJSettingsSchema = Field(
        default_factory=DJSettingsSchema,
        description="DJ settings",
    )


class UpdatePresetRequest(BaseModel):
    """Request schema for updating a preset."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Preset display name",
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="Optional description",
    )
    is_default: bool | None = Field(
        default=None,
        description="Set as default preset",
    )
    settings: DJSettingsSchema | None = Field(
        default=None,
        description="DJ settings",
    )


class PresetResponse(BaseModel):
    """Response schema for preset summary."""

    id: UUID = Field(..., description="Preset ID")
    user_id: UUID = Field(..., description="Owner user ID")
    name: str = Field(..., description="Preset display name")
    description: str | None = Field(default=None, description="Description")
    is_default: bool = Field(..., description="Is default preset")
    settings: DJSettingsSchema = Field(..., description="DJ settings")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class PresetDetailResponse(PresetResponse):
    """Response schema for preset with tracks."""

    tracks: list["TrackResponse"] = Field(
        default_factory=list,
        description="Tracks in this preset",
    )


class PresetListResponse(BaseModel):
    """Response schema for preset list."""

    items: list[PresetResponse] = Field(..., description="List of presets")
    total: int = Field(..., description="Total count")


# =============================================================================
# Track Schemas
# =============================================================================


class CreateTrackRequest(BaseModel):
    """Request schema for creating a new track."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Track display name",
        examples=["開場白"],
    )
    type: DJTrackType = Field(
        ...,
        description="Track category",
        examples=["intro"],
    )
    source: DJTrackSource = Field(
        ...,
        description="Audio source type",
        examples=["tts"],
    )
    hotkey: str | None = Field(
        default=None,
        max_length=10,
        description="Keyboard shortcut",
        examples=["1"],
    )
    loop: bool = Field(
        default=False,
        description="Loop playback",
    )
    sort_order: int = Field(
        default=0,
        ge=0,
        description="Order in track list",
    )

    # TTS fields
    text_content: str | None = Field(
        default=None,
        max_length=5000,
        description="Text to synthesize (for TTS tracks)",
        examples=["嗨！小朋友你好，我是魔法 DJ！"],
    )
    tts_provider: str | None = Field(
        default=None,
        max_length=50,
        description="TTS provider name",
        examples=["voai"],
    )
    tts_voice_id: str | None = Field(
        default=None,
        max_length=100,
        description="TTS voice identifier",
        examples=["voai-tw-female-1"],
    )
    tts_speed: Decimal = Field(
        default=Decimal("1.0"),
        ge=Decimal("0.5"),
        le=Decimal("2.0"),
        description="TTS playback speed multiplier",
    )

    # Playback settings
    volume: Decimal = Field(
        default=Decimal("1.0"),
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Volume level (0.0 to 1.0)",
    )


class UpdateTrackRequest(BaseModel):
    """Request schema for updating a track."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Track display name",
    )
    type: DJTrackType | None = Field(
        default=None,
        description="Track category",
    )
    hotkey: str | None = Field(
        default=None,
        max_length=10,
        description="Keyboard shortcut",
    )
    loop: bool | None = Field(
        default=None,
        description="Loop playback",
    )
    sort_order: int | None = Field(
        default=None,
        ge=0,
        description="Order in track list",
    )

    # TTS fields
    text_content: str | None = Field(
        default=None,
        max_length=5000,
        description="Text to synthesize",
    )
    tts_provider: str | None = Field(
        default=None,
        max_length=50,
        description="TTS provider name",
    )
    tts_voice_id: str | None = Field(
        default=None,
        max_length=100,
        description="TTS voice identifier",
    )
    tts_speed: Decimal | None = Field(
        default=None,
        ge=Decimal("0.5"),
        le=Decimal("2.0"),
        description="TTS playback speed multiplier",
    )

    # Playback settings
    volume: Decimal | None = Field(
        default=None,
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Volume level",
    )


class ReorderTracksRequest(BaseModel):
    """Request schema for reordering tracks."""

    track_ids: list[UUID] = Field(
        ...,
        min_length=1,
        description="Track IDs in new order",
    )


class TrackResponse(BaseModel):
    """Response schema for track."""

    id: UUID = Field(..., description="Track ID")
    preset_id: UUID = Field(..., description="Parent preset ID")
    name: str = Field(..., description="Track display name")
    type: DJTrackType = Field(..., description="Track category")
    source: DJTrackSource = Field(..., description="Audio source type")
    hotkey: str | None = Field(default=None, description="Keyboard shortcut")
    loop: bool = Field(..., description="Loop playback")
    sort_order: int = Field(..., description="Order in track list")

    # TTS fields
    text_content: str | None = Field(default=None, description="Text content")
    tts_provider: str | None = Field(default=None, description="TTS provider")
    tts_voice_id: str | None = Field(default=None, description="TTS voice ID")
    tts_speed: Decimal = Field(..., description="TTS speed")

    # Upload fields
    original_filename: str | None = Field(default=None, description="Original filename")

    # Audio info
    audio_url: str | None = Field(
        default=None,
        description="Signed URL for audio playback (generated on read)",
    )
    duration_ms: int | None = Field(default=None, description="Audio duration in ms")
    file_size_bytes: int | None = Field(default=None, description="File size in bytes")
    content_type: str = Field(..., description="MIME type")

    # Playback settings
    volume: Decimal = Field(..., description="Volume level")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class TrackListResponse(BaseModel):
    """Response schema for track list."""

    items: list[TrackResponse] = Field(..., description="List of tracks")
    total: int = Field(..., description="Total count")


# =============================================================================
# Audio Upload Schemas
# =============================================================================


class AudioUploadResponse(BaseModel):
    """Response schema for audio upload."""

    track_id: UUID = Field(..., description="Track ID")
    storage_path: str = Field(..., description="GCS storage path")
    audio_url: str = Field(..., description="Signed URL for playback")
    duration_ms: int = Field(..., description="Audio duration in ms")
    file_size_bytes: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type")


# =============================================================================
# Import/Export Schemas
# =============================================================================


class LocalStorageTrack(BaseModel):
    """Schema for a track from localStorage format."""

    id: str = Field(..., description="Track ID (e.g., 'track_01')")
    name: str = Field(..., description="Track name")
    type: str = Field(..., description="Track type")
    source: str = Field(default="tts", description="Track source")
    hotkey: str | None = Field(default=None, description="Hotkey")
    loop: bool = Field(default=False, description="Loop")
    text_content: str | None = Field(default=None, description="TTS text")
    audio_base64: str | None = Field(
        default=None,
        alias="audioBase64",
        description="Base64-encoded audio data",
    )
    volume: float = Field(default=1.0, description="Volume")

    class Config:
        populate_by_name = True


class LocalStorageData(BaseModel):
    """Schema for localStorage data format."""

    settings: dict[str, Any] = Field(default_factory=dict, description="DJ settings")
    master_volume: float = Field(
        default=1.0,
        alias="masterVolume",
        description="Master volume",
    )
    tracks: list[LocalStorageTrack] = Field(
        default_factory=list,
        description="Track list",
    )

    class Config:
        populate_by_name = True


class ImportRequest(BaseModel):
    """Request schema for importing from localStorage."""

    preset_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name for the imported preset",
        examples=["匯入的設定"],
    )
    data: LocalStorageData = Field(..., description="localStorage data")


class ExportResponse(BaseModel):
    """Response schema for exporting a preset."""

    preset: PresetResponse = Field(..., description="Preset metadata")
    tracks: list[TrackResponse] = Field(..., description="Tracks with audio URLs")


# Enable forward references
PresetDetailResponse.model_rebuild()
