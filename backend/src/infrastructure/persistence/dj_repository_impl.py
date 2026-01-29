"""SQLAlchemy implementation of DJ Repository.

Feature: 011-magic-dj-audio-features
Phase 3: Backend Storage Support

This module provides the PostgreSQL-based implementation of the DJ repository
for managing presets and tracks.
"""

import uuid
from decimal import Decimal

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entities.dj import (
    DJPreset,
    DJSettings,
    DJTrack,
    DJTrackSource,
    DJTrackType,
)
from src.infrastructure.persistence.models import DJPresetModel, DJTrackModel


class DJRepositoryImpl:
    """SQLAlchemy-based implementation of DJ Repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # =========================================================================
    # Preset Operations
    # =========================================================================

    async def save_preset(self, preset: DJPreset) -> DJPreset:
        """Save a new preset."""
        model = DJPresetModel(
            id=preset.id,
            user_id=preset.user_id,
            name=preset.name,
            description=preset.description,
            is_default=preset.is_default,
            settings=preset.settings.to_dict(),
            created_at=preset.created_at,
            updated_at=preset.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return preset

    async def get_preset_by_id(
        self, preset_id: uuid.UUID, include_tracks: bool = False
    ) -> DJPreset | None:
        """Get a preset by ID, optionally including tracks."""
        query = select(DJPresetModel).where(DJPresetModel.id == preset_id)
        if include_tracks:
            query = query.options(selectinload(DJPresetModel.tracks))

        result = await self._session.execute(query)
        model = result.scalar_one_or_none()
        return self._preset_model_to_entity(model) if model else None

    async def get_presets_by_user_id(self, user_id: uuid.UUID) -> list[DJPreset]:
        """List all presets for a user."""
        result = await self._session.execute(
            select(DJPresetModel)
            .where(DJPresetModel.user_id == user_id)
            .order_by(DJPresetModel.created_at.desc())
        )
        models = result.scalars().all()
        return [self._preset_model_to_entity(m) for m in models]

    async def get_default_preset(self, user_id: uuid.UUID) -> DJPreset | None:
        """Get the user's default preset."""
        result = await self._session.execute(
            select(DJPresetModel)
            .where(DJPresetModel.user_id == user_id)
            .where(DJPresetModel.is_default.is_(True))
        )
        model = result.scalar_one_or_none()
        return self._preset_model_to_entity(model) if model else None

    async def update_preset(self, preset: DJPreset) -> DJPreset:
        """Update an existing preset."""
        await self._session.execute(
            update(DJPresetModel)
            .where(DJPresetModel.id == preset.id)
            .values(
                name=preset.name,
                description=preset.description,
                is_default=preset.is_default,
                settings=preset.settings.to_dict(),
                updated_at=preset.updated_at,
            )
        )
        await self._session.flush()
        return preset

    async def delete_preset(self, preset_id: uuid.UUID) -> bool:
        """Delete a preset and all its tracks (cascade)."""
        result = await self._session.execute(
            delete(DJPresetModel).where(DJPresetModel.id == preset_id)
        )
        await self._session.flush()
        return result.rowcount > 0

    async def count_presets_by_user_id(self, user_id: uuid.UUID) -> int:
        """Count presets for a user."""
        result = await self._session.execute(
            select(func.count()).select_from(DJPresetModel).where(DJPresetModel.user_id == user_id)
        )
        return result.scalar() or 0

    async def preset_exists(self, user_id: uuid.UUID, name: str) -> bool:
        """Check if a preset with the given name exists for the user."""
        result = await self._session.execute(
            select(func.count())
            .select_from(DJPresetModel)
            .where(DJPresetModel.user_id == user_id)
            .where(DJPresetModel.name == name)
        )
        return (result.scalar() or 0) > 0

    async def clear_default_presets(self, user_id: uuid.UUID) -> None:
        """Clear the is_default flag for all user presets."""
        await self._session.execute(
            update(DJPresetModel)
            .where(DJPresetModel.user_id == user_id)
            .where(DJPresetModel.is_default.is_(True))
            .values(is_default=False)
        )
        await self._session.flush()

    # =========================================================================
    # Track Operations
    # =========================================================================

    async def save_track(self, track: DJTrack) -> DJTrack:
        """Save a new track."""
        model = DJTrackModel(
            id=track.id,
            preset_id=track.preset_id,
            name=track.name,
            type=track.type.value,
            source=track.source.value,
            hotkey=track.hotkey,
            loop=track.loop,
            sort_order=track.sort_order,
            text_content=track.text_content,
            tts_provider=track.tts_provider,
            tts_voice_id=track.tts_voice_id,
            tts_speed=track.tts_speed,
            original_filename=track.original_filename,
            audio_storage_path=track.audio_storage_path,
            duration_ms=track.duration_ms,
            file_size_bytes=track.file_size_bytes,
            content_type=track.content_type,
            volume=track.volume,
            created_at=track.created_at,
            updated_at=track.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        return track

    async def get_track_by_id(self, track_id: uuid.UUID) -> DJTrack | None:
        """Get a track by ID."""
        result = await self._session.execute(
            select(DJTrackModel).where(DJTrackModel.id == track_id)
        )
        model = result.scalar_one_or_none()
        return self._track_model_to_entity(model) if model else None

    async def get_tracks_by_preset_id(self, preset_id: uuid.UUID) -> list[DJTrack]:
        """List all tracks for a preset, ordered by sort_order."""
        result = await self._session.execute(
            select(DJTrackModel)
            .where(DJTrackModel.preset_id == preset_id)
            .order_by(DJTrackModel.sort_order.asc())
        )
        models = result.scalars().all()
        return [self._track_model_to_entity(m) for m in models]

    async def update_track(self, track: DJTrack) -> DJTrack:
        """Update an existing track."""
        await self._session.execute(
            update(DJTrackModel)
            .where(DJTrackModel.id == track.id)
            .values(
                name=track.name,
                type=track.type.value,
                hotkey=track.hotkey,
                loop=track.loop,
                sort_order=track.sort_order,
                text_content=track.text_content,
                tts_provider=track.tts_provider,
                tts_voice_id=track.tts_voice_id,
                tts_speed=track.tts_speed,
                original_filename=track.original_filename,
                audio_storage_path=track.audio_storage_path,
                duration_ms=track.duration_ms,
                file_size_bytes=track.file_size_bytes,
                content_type=track.content_type,
                volume=track.volume,
                updated_at=track.updated_at,
            )
        )
        await self._session.flush()
        return track

    async def delete_track(self, track_id: uuid.UUID) -> bool:
        """Delete a track."""
        result = await self._session.execute(
            delete(DJTrackModel).where(DJTrackModel.id == track_id)
        )
        await self._session.flush()
        return result.rowcount > 0

    async def count_tracks_by_preset_id(self, preset_id: uuid.UUID) -> int:
        """Count tracks in a preset."""
        result = await self._session.execute(
            select(func.count())
            .select_from(DJTrackModel)
            .where(DJTrackModel.preset_id == preset_id)
        )
        return result.scalar() or 0

    async def reorder_tracks(self, preset_id: uuid.UUID, track_ids: list[uuid.UUID]) -> None:
        """Reorder tracks by updating sort_order based on the provided ID list."""
        for index, track_id in enumerate(track_ids):
            await self._session.execute(
                update(DJTrackModel)
                .where(DJTrackModel.id == track_id)
                .where(DJTrackModel.preset_id == preset_id)
                .values(sort_order=index)
            )
        await self._session.flush()

    async def get_next_sort_order(self, preset_id: uuid.UUID) -> int:
        """Get the next available sort_order for a preset."""
        result = await self._session.execute(
            select(func.max(DJTrackModel.sort_order))
            .select_from(DJTrackModel)
            .where(DJTrackModel.preset_id == preset_id)
        )
        max_order = result.scalar()
        return (max_order or -1) + 1

    # =========================================================================
    # Conversion Methods
    # =========================================================================

    def _preset_model_to_entity(self, model: DJPresetModel) -> DJPreset:
        """Convert SQLAlchemy model to domain entity."""
        return DJPreset(
            id=model.id,
            user_id=model.user_id,
            name=model.name,
            description=model.description,
            is_default=model.is_default,
            settings=DJSettings.from_dict(model.settings or {}),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _track_model_to_entity(self, model: DJTrackModel) -> DJTrack:
        """Convert SQLAlchemy model to domain entity."""
        return DJTrack(
            id=model.id,
            preset_id=model.preset_id,
            name=model.name,
            type=DJTrackType(model.type),
            source=DJTrackSource(model.source),
            hotkey=model.hotkey,
            loop=model.loop,
            sort_order=model.sort_order,
            text_content=model.text_content,
            tts_provider=model.tts_provider,
            tts_voice_id=model.tts_voice_id,
            tts_speed=Decimal(str(model.tts_speed)) if model.tts_speed else Decimal("1.0"),
            original_filename=model.original_filename,
            audio_storage_path=model.audio_storage_path,
            duration_ms=model.duration_ms,
            file_size_bytes=model.file_size_bytes,
            content_type=model.content_type,
            volume=Decimal(str(model.volume)) if model.volume else Decimal("1.0"),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
