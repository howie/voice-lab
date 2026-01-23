"""Sync Voices Use Case.

Feature: 008-voai-multi-role-voice-generation
T025: Create SyncVoicesUseCase
T026: Implement exponential backoff retry logic

Synchronizes voice data from TTS providers to the local database.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from src.application.interfaces.voice_cache_repository import IVoiceCacheRepository
from src.application.interfaces.voice_sync_job_repository import IVoiceSyncJobRepository
from src.domain.entities.voice import Gender, VoiceProfile
from src.domain.entities.voice_sync_job import VoiceSyncJob
from src.domain.services.voice_metadata_inferrer import VoiceMetadataInferrer
from src.infrastructure.providers.tts.voice_fetchers.azure_voice_fetcher import (
    AzureVoiceFetcher,
    AzureVoiceInfo,
)
from src.infrastructure.providers.tts.voice_fetchers.elevenlabs_voice_fetcher import (
    ElevenLabsVoiceFetcher,
    ElevenLabsVoiceInfo,
)

logger = logging.getLogger(__name__)


class VoiceFetcherProtocol(Protocol):
    """Protocol for voice fetchers."""

    async def fetch_voices(self) -> list: ...


@dataclass
class SyncVoicesInput:
    """Input for voice sync operation."""

    providers: list[str] | None = None  # None means sync all
    language: str | None = None  # Optional language filter
    force: bool = False  # Force sync even if recently synced


@dataclass
class SyncVoicesResult:
    """Result of voice sync operation."""

    job_id: str
    providers_synced: list[str]
    voices_synced: int
    voices_deprecated: int
    duration_ms: int
    errors: list[str]


class SyncVoicesUseCase:
    """Use case for synchronizing voice data from providers.

    Fetches voice lists from configured TTS providers and updates
    the local voice cache with age_group inference.

    Implements exponential backoff retry (1s, 2s, 4s, max 3 retries).
    """

    SUPPORTED_PROVIDERS = ["azure", "elevenlabs"]
    MAX_RETRIES = 3
    INITIAL_BACKOFF_SECONDS = 1.0

    def __init__(
        self,
        voice_cache_repo: IVoiceCacheRepository,
        sync_job_repo: IVoiceSyncJobRepository,
        azure_fetcher: AzureVoiceFetcher | None = None,
        elevenlabs_fetcher: ElevenLabsVoiceFetcher | None = None,
    ):
        """Initialize the use case.

        Args:
            voice_cache_repo: Repository for voice cache operations.
            sync_job_repo: Repository for sync job tracking.
            azure_fetcher: Azure voice fetcher instance.
            elevenlabs_fetcher: ElevenLabs voice fetcher instance.
        """
        self.voice_cache_repo = voice_cache_repo
        self.sync_job_repo = sync_job_repo
        self.azure_fetcher = azure_fetcher or AzureVoiceFetcher()
        self.elevenlabs_fetcher = elevenlabs_fetcher or ElevenLabsVoiceFetcher()
        self.inferrer = VoiceMetadataInferrer()

    async def execute(self, input_data: SyncVoicesInput) -> SyncVoicesResult:
        """Execute voice synchronization.

        Args:
            input_data: Sync parameters.

        Returns:
            SyncVoicesResult with sync statistics.

        Raises:
            ValueError: If a sync job is already running.
        """
        start_time = datetime.utcnow()

        # Check for running jobs
        if await self.sync_job_repo.has_running_job():
            raise ValueError("A voice sync job is already running")

        # Determine which providers to sync
        providers = input_data.providers or self.SUPPORTED_PROVIDERS
        providers = [p for p in providers if p in self.SUPPORTED_PROVIDERS]

        if not providers:
            raise ValueError("No valid providers specified for sync")

        # Create sync job
        job = VoiceSyncJob.create(providers=providers)
        await self.sync_job_repo.create(job)

        # Start sync
        job = job.start()
        await self.sync_job_repo.update(job)

        total_synced = 0
        total_deprecated = 0
        errors: list[str] = []

        try:
            for provider in providers:
                try:
                    synced, deprecated = await self._sync_provider(
                        provider=provider,
                        language=input_data.language,
                    )
                    total_synced += synced
                    total_deprecated += deprecated
                except Exception as e:
                    error_msg = f"Failed to sync {provider}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            # Complete job
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            if errors:
                job = job.fail(error="; ".join(errors))
            else:
                job = job.complete(
                    voices_synced=total_synced,
                    voices_deprecated=total_deprecated,
                )
            await self.sync_job_repo.update(job)

            return SyncVoicesResult(
                job_id=job.id,
                providers_synced=providers,
                voices_synced=total_synced,
                voices_deprecated=total_deprecated,
                duration_ms=duration_ms,
                errors=errors,
            )

        except Exception as e:
            # Mark job as failed
            job = job.fail(error=str(e))
            await self.sync_job_repo.update(job)
            raise

    async def _sync_provider(
        self,
        provider: str,
        language: str | None = None,
    ) -> tuple[int, int]:
        """Sync voices from a specific provider.

        Args:
            provider: Provider name.
            language: Optional language filter.

        Returns:
            Tuple of (voices_synced, voices_deprecated).
        """
        if provider == "azure":
            return await self._sync_azure(language)
        elif provider == "elevenlabs":
            return await self._sync_elevenlabs()
        else:
            raise ValueError(f"Unknown provider: {provider}")

    async def _sync_azure(self, language: str | None = None) -> tuple[int, int]:
        """Sync Azure voices.

        Args:
            language: Optional language filter.

        Returns:
            Tuple of (voices_synced, voices_deprecated).
        """
        # Fetch voices with retry
        raw_voices = await self._fetch_with_retry(
            lambda: self.azure_fetcher.fetch_neural_voices(language)
        )

        # Convert to VoiceProfile entities
        profiles = []
        for v in raw_voices:
            profile = self._azure_to_voice_profile(v)
            profiles.append(profile)

        # Upsert to database
        await self.voice_cache_repo.upsert_batch(profiles)

        # Mark deprecated voices (voices in DB but not in API response)
        deprecated_count = await self._mark_deprecated_voices(
            provider="azure",
            current_voice_ids={p.voice_id for p in profiles},
        )

        logger.info(f"Synced {len(profiles)} Azure voices, deprecated {deprecated_count}")
        return len(profiles), deprecated_count

    async def _sync_elevenlabs(self) -> tuple[int, int]:
        """Sync ElevenLabs voices.

        Returns:
            Tuple of (voices_synced, voices_deprecated).
        """
        # Fetch voices with retry
        raw_voices = await self._fetch_with_retry(lambda: self.elevenlabs_fetcher.fetch_voices())

        # Convert to VoiceProfile entities
        profiles = []
        for v in raw_voices:
            profile = self._elevenlabs_to_voice_profile(v)
            profiles.append(profile)

        # Upsert to database
        await self.voice_cache_repo.upsert_batch(profiles)

        # Mark deprecated voices
        deprecated_count = await self._mark_deprecated_voices(
            provider="elevenlabs",
            current_voice_ids={p.voice_id for p in profiles},
        )

        logger.info(f"Synced {len(profiles)} ElevenLabs voices, deprecated {deprecated_count}")
        return len(profiles), deprecated_count

    async def _fetch_with_retry(self, fetch_fn) -> list:
        """Fetch with exponential backoff retry.

        Args:
            fetch_fn: Async function to call.

        Returns:
            Result of fetch_fn.

        Raises:
            Last exception if all retries fail.
        """
        last_error: Exception | None = None
        backoff = self.INITIAL_BACKOFF_SECONDS

        for attempt in range(self.MAX_RETRIES):
            try:
                return await fetch_fn()
            except Exception as e:
                last_error = e
                logger.warning(f"Fetch attempt {attempt + 1}/{self.MAX_RETRIES} failed: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(backoff)
                    backoff *= 2  # Exponential backoff

        raise last_error or Exception("Fetch failed after all retries")

    def _azure_to_voice_profile(self, v: AzureVoiceInfo) -> VoiceProfile:
        """Convert Azure voice info to VoiceProfile entity."""
        gender = self.inferrer.infer_gender_from_azure(v.gender)
        age_group = self.inferrer.infer_age_group_from_azure(
            display_name=v.display_name,
            local_name=v.local_name,
            style_list=v.style_list,
            role_play_list=v.role_play_list,
        )

        # Determine use cases based on styles
        use_cases = []
        if v.style_list:
            if "newscast" in v.style_list:
                use_cases.append("news")
            if "customerservice" in v.style_list:
                use_cases.append("customer_service")
            if "narration" in v.style_list:
                use_cases.append("narration")
            if any(s in v.style_list for s in ["chat", "cheerful", "friendly"]):
                use_cases.append("assistant")

        return VoiceProfile(
            id=f"azure:{v.short_name}",
            provider="azure",
            voice_id=v.short_name,
            display_name=v.display_name,
            language=v.locale,
            gender=Gender(gender) if gender else None,
            age_group=age_group,
            styles=tuple(v.style_list) if v.style_list else (),
            use_cases=tuple(use_cases),
            description=f"Azure Neural Voice - {v.local_name}",
            sample_audio_url=None,
            is_deprecated=False,
            synced_at=datetime.utcnow(),
        )

    def _elevenlabs_to_voice_profile(self, v: ElevenLabsVoiceInfo) -> VoiceProfile:
        """Convert ElevenLabs voice info to VoiceProfile entity."""
        gender = self.inferrer.infer_gender_from_elevenlabs(v.labels.gender)
        age_group = self.inferrer.infer_age_group_from_elevenlabs(
            name=v.name,
            age_label=v.labels.age,
            description=v.description,
        )

        # Determine use cases from labels
        use_cases = []
        if v.labels.use_case:
            use_cases.append(v.labels.use_case)
        if v.category == "premade":
            use_cases.append("general")

        return VoiceProfile(
            id=f"elevenlabs:{v.voice_id}",
            provider="elevenlabs",
            voice_id=v.voice_id,
            display_name=v.name,
            language="multilingual",  # ElevenLabs voices are multilingual
            gender=Gender(gender) if gender else None,
            age_group=age_group,
            styles=(),  # ElevenLabs doesn't have style presets
            use_cases=tuple(use_cases),
            description=v.description or f"ElevenLabs Voice - {v.name}",
            sample_audio_url=v.preview_url,
            is_deprecated=False,
            synced_at=datetime.utcnow(),
        )

    async def _mark_deprecated_voices(
        self,
        provider: str,
        current_voice_ids: set[str],
    ) -> int:
        """Mark voices that are no longer available as deprecated.

        Args:
            provider: Provider name.
            current_voice_ids: Set of voice IDs currently available.

        Returns:
            Number of voices marked as deprecated.
        """
        # Get all voices for this provider from DB
        db_voices = await self.voice_cache_repo.get_by_provider(provider)

        deprecated_count = 0
        for voice in db_voices:
            if voice.voice_id not in current_voice_ids and not voice.is_deprecated:
                await self.voice_cache_repo.mark_deprecated(voice.id)
                deprecated_count += 1

        return deprecated_count
