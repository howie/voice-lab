"""SQLAlchemy implementation of VoiceCustomizationRepository.

Feature: 013-tts-role-mgmt
T007: Implement VoiceCustomizationRepositoryImpl (DB-backed)
"""

from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.voice_customization import VoiceCustomization
from src.domain.repositories.voice_customization_repository import (
    IVoiceCustomizationRepository,
)
from src.infrastructure.persistence.models import VoiceCustomizationModel


class VoiceCustomizationRepositoryImpl(IVoiceCustomizationRepository):
    """SQLAlchemy-based implementation of IVoiceCustomizationRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, customization: VoiceCustomization) -> VoiceCustomization:
        """Save or update a voice customization (upsert)."""
        now = datetime.now(UTC)

        # Validate before saving
        errors = customization.validate()
        if errors:
            raise ValueError(f"Validation failed: {', '.join(errors)}")

        stmt = insert(VoiceCustomizationModel).values(
            voice_cache_id=customization.voice_cache_id,
            custom_name=customization.custom_name,
            is_favorite=customization.is_favorite,
            is_hidden=customization.is_hidden,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["voice_cache_id"],
            set_={
                "custom_name": stmt.excluded.custom_name,
                "is_favorite": stmt.excluded.is_favorite,
                "is_hidden": stmt.excluded.is_hidden,
                "updated_at": now,
            },
        )
        await self._session.execute(stmt)
        await self._session.flush()

        # Fetch the saved record to get the ID and timestamps
        result = await self._session.execute(
            select(VoiceCustomizationModel).where(
                VoiceCustomizationModel.voice_cache_id == customization.voice_cache_id
            )
        )
        model = result.scalar_one()
        return self._model_to_entity(model)

    async def get_by_voice_cache_id(self, voice_cache_id: str) -> VoiceCustomization | None:
        """Get a voice customization by voice cache ID."""
        result = await self._session.execute(
            select(VoiceCustomizationModel).where(
                VoiceCustomizationModel.voice_cache_id == voice_cache_id
            )
        )
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def list_all(self) -> list[VoiceCustomization]:
        """List all voice customizations."""
        result = await self._session.execute(
            select(VoiceCustomizationModel).order_by(VoiceCustomizationModel.voice_cache_id)
        )
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def list_by_filter(
        self,
        is_favorite: bool | None = None,
        is_hidden: bool | None = None,
    ) -> list[VoiceCustomization]:
        """List voice customizations with optional filters."""
        query = select(VoiceCustomizationModel)

        if is_favorite is not None:
            query = query.where(VoiceCustomizationModel.is_favorite == is_favorite)

        if is_hidden is not None:
            query = query.where(VoiceCustomizationModel.is_hidden == is_hidden)

        query = query.order_by(VoiceCustomizationModel.voice_cache_id)
        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def delete(self, voice_cache_id: str) -> bool:
        """Delete a voice customization (reset to defaults)."""
        result = await self._session.execute(
            delete(VoiceCustomizationModel).where(
                VoiceCustomizationModel.voice_cache_id == voice_cache_id
            )
        )
        await self._session.flush()
        return result.rowcount > 0

    async def bulk_update(
        self, customizations: list[VoiceCustomization]
    ) -> tuple[int, list[tuple[str, str]]]:
        """Bulk update multiple voice customizations."""
        success_count = 0
        failures: list[tuple[str, str]] = []

        for customization in customizations:
            try:
                # Validate
                errors = customization.validate()
                if errors:
                    failures.append((customization.voice_cache_id, ", ".join(errors)))
                    continue

                await self.save(customization)
                success_count += 1
            except Exception as e:
                failures.append((customization.voice_cache_id, str(e)))

        return success_count, failures

    async def get_customization_map(
        self, voice_cache_ids: list[str]
    ) -> dict[str, VoiceCustomization]:
        """Get customizations for multiple voice cache IDs."""
        if not voice_cache_ids:
            return {}

        result = await self._session.execute(
            select(VoiceCustomizationModel).where(
                VoiceCustomizationModel.voice_cache_id.in_(voice_cache_ids)
            )
        )
        models = result.scalars().all()
        return {m.voice_cache_id: self._model_to_entity(m) for m in models}

    def _model_to_entity(self, model: VoiceCustomizationModel) -> VoiceCustomization:
        """Convert SQLAlchemy model to domain entity."""
        return VoiceCustomization(
            id=model.id,
            voice_cache_id=model.voice_cache_id,
            custom_name=model.custom_name,
            is_favorite=model.is_favorite,
            is_hidden=model.is_hidden,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
