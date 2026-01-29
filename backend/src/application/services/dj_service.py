"""DJ Service for Magic DJ Controller.

Feature: 011-magic-dj-audio-features
Phase 3: Backend Storage Support

This service orchestrates DJ preset and track operations.
"""

import base64
import logging
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from src.domain.entities.dj import (
    DJPreset,
    DJSettings,
    DJTrack,
    DJTrackSource,
    DJTrackType,
)
from src.infrastructure.persistence.dj_repository_impl import DJRepositoryImpl
from src.infrastructure.storage.dj_audio_storage import DJAudioStorageService

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

MAX_PRESETS_PER_USER = 20
MAX_TRACKS_PER_PRESET = 50
MAX_AUDIO_SIZE_BYTES = 50 * 1024 * 1024  # 50MB per track


# =============================================================================
# Exceptions
# =============================================================================


class PresetNotFoundError(Exception):
    """Raised when preset is not found."""

    def __init__(self, preset_id: UUID):
        self.preset_id = preset_id
        super().__init__(f"Preset {preset_id} not found")


class PresetAccessDeniedError(Exception):
    """Raised when user doesn't have access to the preset."""

    def __init__(self, preset_id: UUID, user_id: UUID):
        self.preset_id = preset_id
        self.user_id = user_id
        super().__init__(f"Access denied to preset {preset_id}")


class PresetLimitExceededError(Exception):
    """Raised when user exceeds preset limit."""

    def __init__(self, current_count: int, max_count: int = MAX_PRESETS_PER_USER):
        self.current_count = current_count
        self.max_count = max_count
        super().__init__(f"Preset limit exceeded: {current_count}/{max_count}")


class PresetNameExistsError(Exception):
    """Raised when preset name already exists for user."""

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Preset with name '{name}' already exists")


class TrackNotFoundError(Exception):
    """Raised when track is not found."""

    def __init__(self, track_id: UUID):
        self.track_id = track_id
        super().__init__(f"Track {track_id} not found")


class TrackLimitExceededError(Exception):
    """Raised when preset exceeds track limit."""

    def __init__(self, current_count: int, max_count: int = MAX_TRACKS_PER_PRESET):
        self.current_count = current_count
        self.max_count = max_count
        super().__init__(f"Track limit exceeded: {current_count}/{max_count}")


class AudioUploadError(Exception):
    """Raised when audio upload fails."""

    def __init__(self, message: str):
        super().__init__(message)


# =============================================================================
# DTOs
# =============================================================================


class AudioInfo(BaseModel):
    """Audio file information."""

    storage_path: str
    duration_ms: int
    file_size_bytes: int
    content_type: str


# =============================================================================
# Service
# =============================================================================


class DJService:
    """Service for orchestrating DJ operations."""

    def __init__(
        self,
        dj_repository: DJRepositoryImpl,
        audio_storage: DJAudioStorageService,
    ):
        self._repo = dj_repository
        self._audio_storage = audio_storage

    # =========================================================================
    # Preset Operations
    # =========================================================================

    async def create_preset(
        self,
        user_id: UUID,
        name: str,
        description: str | None = None,
        is_default: bool = False,
        settings: DJSettings | None = None,
    ) -> DJPreset:
        """Create a new preset.

        Args:
            user_id: Owner user ID
            name: Preset name
            description: Optional description
            is_default: Set as default preset
            settings: DJ settings

        Returns:
            Created DJPreset entity

        Raises:
            PresetLimitExceededError: If user exceeds preset limit
            PresetNameExistsError: If preset name already exists
        """
        # Check preset limit
        count = await self._repo.count_presets_by_user_id(user_id)
        if count >= MAX_PRESETS_PER_USER:
            raise PresetLimitExceededError(count)

        # Check name uniqueness
        if await self._repo.preset_exists(user_id, name):
            raise PresetNameExistsError(name)

        # Clear other default presets if setting this as default
        if is_default:
            await self._repo.clear_default_presets(user_id)

        preset = DJPreset(
            user_id=user_id,
            name=name,
            description=description,
            is_default=is_default,
            settings=settings or DJSettings(),
        )

        await self._repo.save_preset(preset)
        logger.info(f"Created preset {preset.id} for user {user_id}")

        return preset

    async def get_preset(
        self,
        preset_id: UUID,
        user_id: UUID,
        include_tracks: bool = False,
    ) -> DJPreset:
        """Get preset by ID.

        Args:
            preset_id: Preset ID
            user_id: User ID (for access check)
            include_tracks: Whether to include tracks

        Returns:
            DJPreset entity

        Raises:
            PresetNotFoundError: If preset not found
            PresetAccessDeniedError: If user doesn't own the preset
        """
        preset = await self._repo.get_preset_by_id(preset_id, include_tracks=include_tracks)

        if preset is None:
            raise PresetNotFoundError(preset_id)

        if preset.user_id != user_id:
            raise PresetAccessDeniedError(preset_id, user_id)

        return preset

    async def list_presets(self, user_id: UUID) -> list[DJPreset]:
        """List all presets for a user.

        Args:
            user_id: User ID

        Returns:
            List of DJPreset entities
        """
        return await self._repo.get_presets_by_user_id(user_id)

    async def update_preset(
        self,
        preset_id: UUID,
        user_id: UUID,
        name: str | None = None,
        description: str | None = None,
        is_default: bool | None = None,
        settings: DJSettings | None = None,
    ) -> DJPreset:
        """Update a preset.

        Args:
            preset_id: Preset ID
            user_id: User ID (for access check)
            name: New name (if provided)
            description: New description (if provided)
            is_default: New default flag (if provided)
            settings: New settings (if provided)

        Returns:
            Updated DJPreset entity

        Raises:
            PresetNotFoundError: If preset not found
            PresetAccessDeniedError: If user doesn't own the preset
            PresetNameExistsError: If new name already exists
        """
        preset = await self.get_preset(preset_id, user_id)

        # Check name uniqueness if changing name
        if (
            name is not None
            and name != preset.name
            and await self._repo.preset_exists(user_id, name)
        ):
            raise PresetNameExistsError(name)

        # Clear other defaults if setting this as default
        if is_default is True and not preset.is_default:
            await self._repo.clear_default_presets(user_id)

        preset.update(
            name=name,
            description=description,
            is_default=is_default,
            settings=settings,
        )

        await self._repo.update_preset(preset)
        logger.info(f"Updated preset {preset_id}")

        return preset

    async def delete_preset(self, preset_id: UUID, user_id: UUID) -> bool:
        """Delete a preset and all its tracks.

        Args:
            preset_id: Preset ID
            user_id: User ID (for access check)

        Returns:
            True if deleted

        Raises:
            PresetNotFoundError: If preset not found
            PresetAccessDeniedError: If user doesn't own the preset
        """
        # Verify access
        await self.get_preset(preset_id, user_id)

        # Delete audio files for all tracks
        tracks = await self._repo.get_tracks_by_preset_id(preset_id)
        for track in tracks:
            if track.audio_storage_path:
                await self._audio_storage.delete(track.audio_storage_path)

        # Delete preset (cascades to tracks)
        result = await self._repo.delete_preset(preset_id)
        logger.info(f"Deleted preset {preset_id} with {len(tracks)} tracks")

        return result

    async def clone_preset(
        self,
        preset_id: UUID,
        user_id: UUID,
        new_name: str,
    ) -> DJPreset:
        """Clone a preset with all its tracks.

        Args:
            preset_id: Source preset ID
            user_id: User ID
            new_name: Name for the cloned preset

        Returns:
            New DJPreset entity

        Raises:
            PresetNotFoundError: If preset not found
            PresetAccessDeniedError: If user doesn't own the preset
            PresetLimitExceededError: If user exceeds preset limit
            PresetNameExistsError: If new name already exists
        """
        source = await self.get_preset(preset_id, user_id, include_tracks=False)

        # Create new preset
        new_preset = await self.create_preset(
            user_id=user_id,
            name=new_name,
            description=source.description,
            is_default=False,
            settings=source.settings,
        )

        # Clone tracks
        source_tracks = await self._repo.get_tracks_by_preset_id(preset_id)
        for source_track in source_tracks:
            new_track = DJTrack(
                preset_id=new_preset.id,
                name=source_track.name,
                type=source_track.type,
                source=source_track.source,
                hotkey=source_track.hotkey,
                loop=source_track.loop,
                sort_order=source_track.sort_order,
                text_content=source_track.text_content,
                tts_provider=source_track.tts_provider,
                tts_voice_id=source_track.tts_voice_id,
                tts_speed=source_track.tts_speed,
                volume=source_track.volume,
                # Don't copy audio - let user regenerate
            )
            await self._repo.save_track(new_track)

        logger.info(f"Cloned preset {preset_id} to {new_preset.id}")
        return new_preset

    # =========================================================================
    # Track Operations
    # =========================================================================

    async def create_track(
        self,
        preset_id: UUID,
        user_id: UUID,
        name: str,
        track_type: DJTrackType,
        source: DJTrackSource,
        hotkey: str | None = None,
        loop: bool = False,
        sort_order: int | None = None,
        text_content: str | None = None,
        tts_provider: str | None = None,
        tts_voice_id: str | None = None,
        tts_speed: Decimal = Decimal("1.0"),
        volume: Decimal = Decimal("1.0"),
    ) -> DJTrack:
        """Create a new track.

        Args:
            preset_id: Parent preset ID
            user_id: User ID (for access check)
            name: Track name
            track_type: Track category
            source: Audio source type
            hotkey: Keyboard shortcut
            loop: Loop playback
            sort_order: Order in track list
            text_content: TTS text
            tts_provider: TTS provider
            tts_voice_id: TTS voice ID
            tts_speed: TTS speed
            volume: Volume level

        Returns:
            Created DJTrack entity

        Raises:
            PresetNotFoundError: If preset not found
            PresetAccessDeniedError: If user doesn't own the preset
            TrackLimitExceededError: If preset exceeds track limit
        """
        # Verify preset access
        await self.get_preset(preset_id, user_id)

        # Check track limit
        count = await self._repo.count_tracks_by_preset_id(preset_id)
        if count >= MAX_TRACKS_PER_PRESET:
            raise TrackLimitExceededError(count)

        # Get next sort order if not provided
        if sort_order is None:
            sort_order = await self._repo.get_next_sort_order(preset_id)

        track = DJTrack(
            preset_id=preset_id,
            name=name,
            type=track_type,
            source=source,
            hotkey=hotkey,
            loop=loop,
            sort_order=sort_order,
            text_content=text_content,
            tts_provider=tts_provider,
            tts_voice_id=tts_voice_id,
            tts_speed=tts_speed,
            volume=volume,
        )

        await self._repo.save_track(track)
        logger.info(f"Created track {track.id} in preset {preset_id}")

        return track

    async def get_track(
        self,
        track_id: UUID,
        user_id: UUID,
    ) -> DJTrack:
        """Get track by ID.

        Args:
            track_id: Track ID
            user_id: User ID (for access check)

        Returns:
            DJTrack entity

        Raises:
            TrackNotFoundError: If track not found
            PresetAccessDeniedError: If user doesn't own the preset
        """
        track = await self._repo.get_track_by_id(track_id)

        if track is None:
            raise TrackNotFoundError(track_id)

        # Verify preset access
        await self.get_preset(track.preset_id, user_id)

        return track

    async def list_tracks(self, preset_id: UUID, user_id: UUID) -> list[DJTrack]:
        """List all tracks for a preset.

        Args:
            preset_id: Preset ID
            user_id: User ID (for access check)

        Returns:
            List of DJTrack entities
        """
        # Verify preset access
        await self.get_preset(preset_id, user_id)

        return await self._repo.get_tracks_by_preset_id(preset_id)

    async def update_track(
        self,
        track_id: UUID,
        user_id: UUID,
        name: str | None = None,
        track_type: DJTrackType | None = None,
        hotkey: str | None = None,
        loop: bool | None = None,
        sort_order: int | None = None,
        text_content: str | None = None,
        tts_provider: str | None = None,
        tts_voice_id: str | None = None,
        tts_speed: Decimal | None = None,
        volume: Decimal | None = None,
    ) -> DJTrack:
        """Update a track.

        Args:
            track_id: Track ID
            user_id: User ID (for access check)
            ... other fields

        Returns:
            Updated DJTrack entity
        """
        track = await self.get_track(track_id, user_id)

        track.update(
            name=name,
            type=track_type,
            hotkey=hotkey,
            loop=loop,
            sort_order=sort_order,
            text_content=text_content,
            tts_provider=tts_provider,
            tts_voice_id=tts_voice_id,
            tts_speed=tts_speed,
            volume=volume,
        )

        await self._repo.update_track(track)
        logger.info(f"Updated track {track_id}")

        return track

    async def delete_track(self, track_id: UUID, user_id: UUID) -> bool:
        """Delete a track.

        Args:
            track_id: Track ID
            user_id: User ID (for access check)

        Returns:
            True if deleted
        """
        track = await self.get_track(track_id, user_id)

        # Delete audio file
        if track.audio_storage_path:
            await self._audio_storage.delete(track.audio_storage_path)

        result = await self._repo.delete_track(track_id)
        logger.info(f"Deleted track {track_id}")

        return result

    async def reorder_tracks(
        self,
        preset_id: UUID,
        user_id: UUID,
        track_ids: list[UUID],
    ) -> list[DJTrack]:
        """Reorder tracks in a preset.

        Args:
            preset_id: Preset ID
            user_id: User ID (for access check)
            track_ids: Track IDs in new order

        Returns:
            Reordered list of DJTrack entities
        """
        # Verify preset access
        await self.get_preset(preset_id, user_id)

        await self._repo.reorder_tracks(preset_id, track_ids)
        logger.info(f"Reordered {len(track_ids)} tracks in preset {preset_id}")

        return await self._repo.get_tracks_by_preset_id(preset_id)

    # =========================================================================
    # Audio Operations
    # =========================================================================

    async def upload_audio(
        self,
        track_id: UUID,
        user_id: UUID,
        audio_data: bytes,
        content_type: str = "audio/mpeg",
        original_filename: str | None = None,
    ) -> AudioInfo:
        """Upload audio for a track.

        Args:
            track_id: Track ID
            user_id: User ID (for access check)
            audio_data: Audio bytes
            content_type: MIME type
            original_filename: Original filename

        Returns:
            AudioInfo with storage details

        Raises:
            TrackNotFoundError: If track not found
            PresetAccessDeniedError: If user doesn't own the preset
            AudioUploadError: If upload fails
        """
        track = await self.get_track(track_id, user_id)

        # Validate size
        if len(audio_data) > MAX_AUDIO_SIZE_BYTES:
            raise AudioUploadError(
                f"Audio file too large: {len(audio_data)} bytes (max {MAX_AUDIO_SIZE_BYTES} bytes)"
            )

        # Delete old audio if exists
        if track.audio_storage_path:
            await self._audio_storage.delete(track.audio_storage_path)

        # Determine extension from content type
        extension_map = {
            "audio/mpeg": "mp3",
            "audio/mp3": "mp3",
            "audio/wav": "wav",
            "audio/wave": "wav",
            "audio/ogg": "ogg",
            "audio/webm": "webm",
        }
        extension = extension_map.get(content_type, "mp3")

        # Upload new audio
        storage_path = await self._audio_storage.upload(
            user_id=user_id,
            track_id=track_id,
            audio_data=audio_data,
            content_type=content_type,
            extension=extension,
        )

        # Get audio duration (placeholder - would need audio processing library)
        duration_ms = await self._get_audio_duration(audio_data, content_type)

        # Update track with audio info
        track.set_audio(
            storage_path=storage_path,
            duration_ms=duration_ms,
            file_size_bytes=len(audio_data),
            content_type=content_type,
            original_filename=original_filename,
        )
        await self._repo.update_track(track)

        logger.info(f"Uploaded audio for track {track_id}: {storage_path}")

        return AudioInfo(
            storage_path=storage_path,
            duration_ms=duration_ms,
            file_size_bytes=len(audio_data),
            content_type=content_type,
        )

    async def get_audio_url(self, track_id: UUID, user_id: UUID) -> str | None:
        """Get signed URL for track audio.

        Args:
            track_id: Track ID
            user_id: User ID (for access check)

        Returns:
            Signed URL or None if no audio
        """
        track = await self.get_track(track_id, user_id)

        if not track.audio_storage_path:
            return None

        return self._audio_storage.get_signed_url(track.audio_storage_path)

    async def delete_audio(self, track_id: UUID, user_id: UUID) -> bool:
        """Delete audio for a track.

        Args:
            track_id: Track ID
            user_id: User ID (for access check)

        Returns:
            True if deleted
        """
        track = await self.get_track(track_id, user_id)

        if not track.audio_storage_path:
            return False

        result = await self._audio_storage.delete(track.audio_storage_path)
        track.clear_audio()
        await self._repo.update_track(track)

        logger.info(f"Deleted audio for track {track_id}")
        return result

    async def _get_audio_duration(self, audio_data: bytes, content_type: str) -> int:
        """Get audio duration in milliseconds.

        Note: This is a placeholder. For accurate duration detection,
        you would need to use a library like pydub or mutagen.
        """
        # Rough estimation based on file size and content type
        # Assumes ~128kbps for MP3, ~1411kbps for WAV
        size_bytes = len(audio_data)

        if content_type in ("audio/wav", "audio/wave"):
            # WAV: 44.1kHz * 16bit * 2ch = ~176400 bytes/sec
            return int(size_bytes / 176.4)
        else:
            # MP3: assume 128kbps = 16000 bytes/sec
            return int(size_bytes / 16.0)

    # =========================================================================
    # Import/Export Operations
    # =========================================================================

    async def import_from_local_storage(
        self,
        user_id: UUID,
        preset_name: str,
        data: dict[str, Any],
    ) -> DJPreset:
        """Import preset from localStorage format.

        Args:
            user_id: User ID
            preset_name: Name for the imported preset
            data: localStorage data

        Returns:
            Created DJPreset entity
        """
        # Parse settings
        settings_data = data.get("settings", {})
        master_volume = data.get("masterVolume", settings_data.get("master_volume", 1.0))

        settings = DJSettings(
            master_volume=master_volume,
            time_warning_at=settings_data.get("timeWarningAt", 1500),
            session_time_limit=settings_data.get("sessionTimeLimit", 1800),
            ai_response_timeout=settings_data.get("aiResponseTimeout", 10),
            auto_play_filler=settings_data.get("autoPlayFiller", True),
        )

        # Create preset
        preset = await self.create_preset(
            user_id=user_id,
            name=preset_name,
            settings=settings,
        )

        # Import tracks
        tracks_data = data.get("tracks", [])
        for i, track_data in enumerate(tracks_data):
            track_type = self._parse_track_type(track_data.get("type", "effect"))
            track_source = DJTrackSource(track_data.get("source", "tts"))

            track = await self.create_track(
                preset_id=preset.id,
                user_id=user_id,
                name=track_data.get("name", f"Track {i + 1}"),
                track_type=track_type,
                source=track_source,
                hotkey=track_data.get("hotkey"),
                loop=track_data.get("loop", False),
                sort_order=i,
                text_content=track_data.get("textContent"),
                volume=Decimal(str(track_data.get("volume", 1.0))),
            )

            # Import audio if base64 is provided
            audio_base64 = track_data.get("audioBase64")
            if audio_base64:
                try:
                    # Parse base64 data URL
                    if audio_base64.startswith("data:"):
                        # data:audio/mpeg;base64,xxxxx
                        header, data_part = audio_base64.split(",", 1)
                        content_type = header.split(":")[1].split(";")[0]
                    else:
                        data_part = audio_base64
                        content_type = "audio/mpeg"

                    audio_bytes = base64.b64decode(data_part)
                    await self.upload_audio(
                        track_id=track.id,
                        user_id=user_id,
                        audio_data=audio_bytes,
                        content_type=content_type,
                    )
                except Exception as e:
                    logger.warning(f"Failed to import audio for track {track.id}: {e}")

        logger.info(f"Imported {len(tracks_data)} tracks to preset {preset.id}")
        return preset

    def _parse_track_type(self, type_str: str) -> DJTrackType:
        """Parse track type string to enum."""
        type_map = {
            "intro": DJTrackType.INTRO,
            "transition": DJTrackType.TRANSITION,
            "effect": DJTrackType.EFFECT,
            "song": DJTrackType.SONG,
            "filler": DJTrackType.FILLER,
            "rescue": DJTrackType.RESCUE,
        }
        return type_map.get(type_str.lower(), DJTrackType.EFFECT)
