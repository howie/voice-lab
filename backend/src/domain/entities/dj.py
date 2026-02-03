"""DJ domain entities for Magic DJ Controller.

Feature: 011-magic-dj-audio-features
Phase 3: Backend Storage Support

This module defines the core domain entities for DJ presets and tracks.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class DJTrackType(StrEnum):
    """Track type enum representing different audio categories.

    Used to categorize tracks for organization and filtering.
    """

    INTRO = "intro"
    TRANSITION = "transition"
    EFFECT = "effect"
    SONG = "song"
    FILLER = "filler"
    RESCUE = "rescue"


class DJTrackSource(StrEnum):
    """Track source enum representing how the audio was created.

    - TTS: Generated via Text-to-Speech
    - UPLOAD: Uploaded audio file
    """

    TTS = "tts"
    UPLOAD = "upload"


@dataclass
class DJSettings:
    """Settings for a DJ preset.

    Attributes:
        master_volume: Master volume level (0.0 to 1.0)
        time_warning_at: Seconds before showing time warning (default: 1500 = 25min)
        session_time_limit: Maximum session duration in seconds (default: 1800 = 30min)
        ai_response_timeout: AI response timeout in seconds (default: 10)
        auto_play_filler: Whether to auto-play filler sound while waiting
    """

    master_volume: float = 1.0
    time_warning_at: int = 1500  # 25 minutes in seconds
    session_time_limit: int = 1800  # 30 minutes
    ai_response_timeout: int = 10  # seconds
    auto_play_filler: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary for JSON storage."""
        return {
            "master_volume": self.master_volume,
            "time_warning_at": self.time_warning_at,
            "session_time_limit": self.session_time_limit,
            "ai_response_timeout": self.ai_response_timeout,
            "auto_play_filler": self.auto_play_filler,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DJSettings":
        """Create settings from dictionary."""
        return cls(
            master_volume=data.get("master_volume", 1.0),
            time_warning_at=data.get("time_warning_at", 1500),
            session_time_limit=data.get("session_time_limit", 1800),
            ai_response_timeout=data.get("ai_response_timeout", 10),
            auto_play_filler=data.get("auto_play_filler", True),
        )


@dataclass
class DJPreset:
    """Domain entity representing a DJ preset (track collection).

    A preset contains a set of tracks with associated settings,
    owned by a specific user.

    Attributes:
        id: Unique identifier for the preset
        user_id: ID of the user who owns this preset
        name: Display name of the preset
        description: Optional description
        is_default: Whether this is the user's default preset
        settings: DJ settings for this preset
        created_at: Timestamp when preset was created
        updated_at: Timestamp when preset was last updated
    """

    user_id: UUID
    name: str
    id: UUID = field(default_factory=uuid4)
    description: str | None = None
    is_default: bool = False
    settings: DJSettings = field(default_factory=DJSettings)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def update(
        self,
        name: str | None = None,
        description: str | None = None,
        is_default: bool | None = None,
        settings: DJSettings | None = None,
    ) -> None:
        """Update preset fields.

        Args:
            name: New name (if provided)
            description: New description (if provided)
            is_default: New default flag (if provided)
            settings: New settings (if provided)
        """
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if is_default is not None:
            self.is_default = is_default
        if settings is not None:
            self.settings = settings
        self.updated_at = datetime.utcnow()


@dataclass
class DJTrack:
    """Domain entity representing a DJ track.

    A track is an audio segment that can be played during a DJ session.
    Tracks can be generated via TTS or uploaded directly.

    Attributes:
        id: Unique identifier for the track
        preset_id: ID of the preset this track belongs to
        name: Display name of the track
        type: Category of the track
        hotkey: Optional keyboard shortcut (e.g., "1", "2")
        loop: Whether to loop playback
        sort_order: Order in the track list
        source: How the audio was created (TTS or upload)

        # TTS fields (when source = 'tts')
        text_content: Text to synthesize
        tts_provider: TTS provider name (e.g., "voai", "azure")
        tts_voice_id: Voice identifier
        tts_speed: Playback speed multiplier

        # Upload fields (when source = 'upload')
        original_filename: Original uploaded filename

        # Audio info
        audio_storage_path: GCS storage path (gs://bucket/path)
        duration_ms: Audio duration in milliseconds
        file_size_bytes: File size in bytes
        content_type: MIME type of the audio

        # Playback settings
        volume: Volume level (0.0 to 1.0)

        # Timestamps
        created_at: Timestamp when track was created
        updated_at: Timestamp when track was last updated
    """

    preset_id: UUID
    name: str
    type: DJTrackType
    source: DJTrackSource
    id: UUID = field(default_factory=uuid4)
    hotkey: str | None = None
    loop: bool = False
    sort_order: int = 0

    # TTS fields
    text_content: str | None = None
    tts_provider: str | None = None
    tts_voice_id: str | None = None
    tts_speed: Decimal = field(default_factory=lambda: Decimal("1.0"))

    # Upload fields
    original_filename: str | None = None

    # Audio info
    audio_storage_path: str | None = None
    duration_ms: int | None = None
    file_size_bytes: int | None = None
    content_type: str = "audio/mpeg"

    # Playback settings
    volume: Decimal = field(default_factory=lambda: Decimal("1.0"))

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def has_audio(self) -> bool:
        """Check if the track has audio content."""
        return self.audio_storage_path is not None

    def is_tts(self) -> bool:
        """Check if the track is TTS-generated."""
        return self.source == DJTrackSource.TTS

    def is_upload(self) -> bool:
        """Check if the track was uploaded."""
        return self.source == DJTrackSource.UPLOAD

    def update(
        self,
        name: str | None = None,
        type: DJTrackType | None = None,
        hotkey: str | None = None,
        loop: bool | None = None,
        sort_order: int | None = None,
        text_content: str | None = None,
        tts_provider: str | None = None,
        tts_voice_id: str | None = None,
        tts_speed: Decimal | None = None,
        volume: Decimal | None = None,
    ) -> None:
        """Update track fields.

        Args:
            name: New name (if provided)
            type: New type (if provided)
            hotkey: New hotkey (if provided)
            loop: New loop setting (if provided)
            sort_order: New sort order (if provided)
            text_content: New text content (if provided)
            tts_provider: New TTS provider (if provided)
            tts_voice_id: New voice ID (if provided)
            tts_speed: New TTS speed (if provided)
            volume: New volume (if provided)
        """
        if name is not None:
            self.name = name
        if type is not None:
            self.type = type
        if hotkey is not None:
            self.hotkey = hotkey
        if loop is not None:
            self.loop = loop
        if sort_order is not None:
            self.sort_order = sort_order
        if text_content is not None:
            self.text_content = text_content
        if tts_provider is not None:
            self.tts_provider = tts_provider
        if tts_voice_id is not None:
            self.tts_voice_id = tts_voice_id
        if tts_speed is not None:
            self.tts_speed = tts_speed
        if volume is not None:
            self.volume = volume
        self.updated_at = datetime.utcnow()

    def set_audio(
        self,
        storage_path: str,
        duration_ms: int,
        file_size_bytes: int,
        content_type: str = "audio/mpeg",
        original_filename: str | None = None,
    ) -> None:
        """Set audio metadata after upload or TTS generation.

        Args:
            storage_path: GCS storage path
            duration_ms: Audio duration in milliseconds
            file_size_bytes: File size in bytes
            content_type: MIME type
            original_filename: Original filename (for uploads)
        """
        self.audio_storage_path = storage_path
        self.duration_ms = duration_ms
        self.file_size_bytes = file_size_bytes
        self.content_type = content_type
        if original_filename is not None:
            self.original_filename = original_filename
        self.updated_at = datetime.utcnow()

    def clear_audio(self) -> None:
        """Clear audio metadata (e.g., before re-generating TTS)."""
        self.audio_storage_path = None
        self.duration_ms = None
        self.file_size_bytes = None
        self.updated_at = datetime.utcnow()
