"""SQLAlchemy implementation of VoiceCacheRepository.

Feature: 008-voai-multi-role-voice-generation
T008: Implement VoiceCacheRepositoryImpl (DB-backed)
"""

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.interfaces.voice_cache_repository import IVoiceCacheRepository
from src.domain.entities.voice import AgeGroup, Gender, VoiceProfile
from src.infrastructure.persistence.models import VoiceCache


class VoiceCacheRepositoryImpl(IVoiceCacheRepository):
    """SQLAlchemy-based implementation of IVoiceCacheRepository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, voice_id: str) -> VoiceProfile | None:
        """Get voice by ID (format: provider:voice_id)."""
        result = await self._session.execute(select(VoiceCache).where(VoiceCache.id == voice_id))
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def get_by_provider(
        self,
        provider: str,
        *,
        language: str | None = None,
        gender: str | None = None,
        age_group: AgeGroup | None = None,
        style: str | None = None,
        include_deprecated: bool = False,
    ) -> Sequence[VoiceProfile]:
        """Get voices by provider with optional filters."""
        query = select(VoiceCache).where(VoiceCache.provider == provider)
        query = self._apply_filters(query, language, gender, age_group, style, include_deprecated)
        query = query.order_by(VoiceCache.name)

        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def list_all(
        self,
        *,
        provider: str | None = None,
        language: str | None = None,
        gender: str | None = None,
        age_group: AgeGroup | None = None,
        style: str | None = None,
        include_deprecated: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[VoiceProfile]:
        """List all voices with optional filters and pagination."""
        query = select(VoiceCache)

        if provider is not None:
            query = query.where(VoiceCache.provider == provider)

        query = self._apply_filters(query, language, gender, age_group, style, include_deprecated)
        query = query.order_by(VoiceCache.provider, VoiceCache.name)
        query = query.offset(offset).limit(limit)

        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def count(
        self,
        *,
        provider: str | None = None,
        language: str | None = None,
        gender: str | None = None,
        age_group: AgeGroup | None = None,
        style: str | None = None,
        include_deprecated: bool = False,
    ) -> int:
        """Count voices matching filters."""
        query = select(func.count()).select_from(VoiceCache)

        if provider is not None:
            query = query.where(VoiceCache.provider == provider)

        query = self._apply_filters(query, language, gender, age_group, style, include_deprecated)

        result = await self._session.execute(query)
        return result.scalar() or 0

    async def upsert(self, voice: VoiceProfile) -> VoiceProfile:
        """Insert or update a voice profile."""
        now = datetime.utcnow()
        stmt = insert(VoiceCache).values(
            id=voice.id,
            provider=voice.provider,
            voice_id=voice.voice_id,
            name=voice.display_name,
            language=voice.language,
            gender=voice.gender.value if voice.gender else None,
            age_group=voice.age_group.value if voice.age_group else None,
            styles=list(voice.styles),
            use_cases=list(voice.use_cases),
            sample_audio_url=voice.sample_audio_url,
            is_deprecated=voice.is_deprecated,
            metadata_=voice.metadata,
            synced_at=now,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "name": stmt.excluded.name,
                "language": stmt.excluded.language,
                "gender": stmt.excluded.gender,
                "age_group": stmt.excluded.age_group,
                "styles": stmt.excluded.styles,
                "use_cases": stmt.excluded.use_cases,
                "sample_audio_url": stmt.excluded.sample_audio_url,
                "is_deprecated": stmt.excluded.is_deprecated,
                "metadata": stmt.excluded.metadata,
                "synced_at": now,
                "updated_at": now,
            },
        )
        await self._session.execute(stmt)
        await self._session.flush()

        # Return updated voice with synced_at
        return VoiceProfile(
            id=voice.id,
            provider=voice.provider,
            voice_id=voice.voice_id,
            display_name=voice.display_name,
            language=voice.language,
            gender=voice.gender,
            age_group=voice.age_group,
            styles=voice.styles,
            use_cases=voice.use_cases,
            description=voice.description,
            sample_audio_url=voice.sample_audio_url,
            is_deprecated=voice.is_deprecated,
            tags=voice.tags,
            metadata=voice.metadata,
            synced_at=now,
        )

    async def upsert_batch(self, voices: Sequence[VoiceProfile]) -> int:
        """Batch upsert voice profiles."""
        if not voices:
            return 0

        now = datetime.utcnow()
        values = [
            {
                "id": v.id,
                "provider": v.provider,
                "voice_id": v.voice_id,
                "name": v.display_name,
                "language": v.language,
                "gender": v.gender.value if v.gender else None,
                "age_group": v.age_group.value if v.age_group else None,
                "styles": list(v.styles),
                "use_cases": list(v.use_cases),
                "sample_audio_url": v.sample_audio_url,
                "is_deprecated": v.is_deprecated,
                "metadata_": v.metadata,
                "synced_at": now,
            }
            for v in voices
        ]

        stmt = insert(VoiceCache).values(values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
                "name": stmt.excluded.name,
                "language": stmt.excluded.language,
                "gender": stmt.excluded.gender,
                "age_group": stmt.excluded.age_group,
                "styles": stmt.excluded.styles,
                "use_cases": stmt.excluded.use_cases,
                "sample_audio_url": stmt.excluded.sample_audio_url,
                "is_deprecated": stmt.excluded.is_deprecated,
                "metadata": stmt.excluded.metadata,
                "synced_at": now,
                "updated_at": now,
            },
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount

    async def mark_deprecated(self, voice_ids: Sequence[str]) -> int:
        """Mark voices as deprecated."""
        if not voice_ids:
            return 0

        result = await self._session.execute(
            update(VoiceCache)
            .where(VoiceCache.id.in_(voice_ids))
            .values(is_deprecated=True, updated_at=datetime.utcnow())
        )
        await self._session.flush()
        return result.rowcount

    async def get_last_sync_time(self, provider: str) -> datetime | None:
        """Get the last sync time for a provider."""
        result = await self._session.execute(
            select(func.max(VoiceCache.synced_at)).where(VoiceCache.provider == provider)
        )
        return result.scalar()

    async def get_voice_ids_by_provider(
        self,
        provider: str,
        include_deprecated: bool = False,
    ) -> Sequence[str]:
        """Get all voice IDs for a provider."""
        query = select(VoiceCache.id).where(VoiceCache.provider == provider)

        if not include_deprecated:
            query = query.where(VoiceCache.is_deprecated == False)  # noqa: E712

        result = await self._session.execute(query)
        return [row[0] for row in result.all()]

    async def update_sample_audio_url(
        self,
        voice_cache_id: str,
        sample_audio_url: str,
    ) -> None:
        """Update the sample audio URL for a voice."""
        await self._session.execute(
            update(VoiceCache)
            .where(VoiceCache.id == voice_cache_id)
            .values(sample_audio_url=sample_audio_url)
        )
        await self._session.flush()

    def _apply_filters(
        self,
        query,
        language: str | None,
        gender: str | None,
        age_group: AgeGroup | None,
        style: str | None,
        include_deprecated: bool,
    ):
        """Apply common filters to a query."""
        if language is not None:
            # Support prefix matching (e.g., "zh" matches "zh-TW", "zh-CN")
            query = query.where(VoiceCache.language.startswith(language))

        if gender is not None:
            query = query.where(VoiceCache.gender == gender)

        if age_group is not None:
            query = query.where(VoiceCache.age_group == age_group.value)

        if style is not None:
            # Check if style exists in JSON array
            query = query.where(VoiceCache.styles.contains([style]))

        if not include_deprecated:
            query = query.where(VoiceCache.is_deprecated == False)  # noqa: E712

        return query

    def _model_to_entity(self, model: VoiceCache) -> VoiceProfile:
        """Convert SQLAlchemy model to domain entity."""
        return VoiceProfile(
            id=model.id,
            provider=model.provider,
            voice_id=model.voice_id,
            display_name=model.name,
            language=model.language,
            gender=Gender(model.gender) if model.gender else None,
            age_group=AgeGroup(model.age_group) if model.age_group else None,
            styles=tuple(model.styles) if model.styles else (),
            use_cases=tuple(model.use_cases) if model.use_cases else (),
            description="",  # Not stored in cache
            sample_audio_url=model.sample_audio_url,
            is_deprecated=model.is_deprecated,
            tags=(),  # Not stored in cache
            metadata=model.metadata_ or {},
            synced_at=model.synced_at,
        )
