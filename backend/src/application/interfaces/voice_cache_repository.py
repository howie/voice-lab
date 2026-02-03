"""Voice Cache Repository Interface (Port).

Feature: 008-voai-multi-role-voice-generation
T006: Define VoiceCacheRepository protocol
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime

from src.domain.entities.voice import AgeGroup, VoiceProfile


class IVoiceCacheRepository(ABC):
    """Abstract interface for voice cache repository.

    This interface defines the contract for voice cache operations.
    Implementations provide database-backed caching of voice profiles
    from various TTS providers.
    """

    @abstractmethod
    async def get_by_id(self, voice_id: str) -> VoiceProfile | None:
        """Get voice by ID (format: provider:voice_id).

        Args:
            voice_id: Composite voice ID (e.g., "azure:zh-TW-HsiaoYuNeural")

        Returns:
            VoiceProfile if found, None otherwise
        """
        pass

    @abstractmethod
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
        """Get voices by provider with optional filters.

        Args:
            provider: Provider name (e.g., "azure", "elevenlabs", "gemini")
            language: Filter by language code (e.g., "zh-TW")
            gender: Filter by gender ("male", "female", "neutral")
            age_group: Filter by age group
            style: Filter by style (checks if style is in styles array)
            include_deprecated: Whether to include deprecated voices

        Returns:
            Sequence of matching VoiceProfile objects
        """
        pass

    @abstractmethod
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
        """List all voices with optional filters and pagination.

        Args:
            provider: Filter by provider name
            language: Filter by language code
            gender: Filter by gender
            age_group: Filter by age group
            style: Filter by style
            include_deprecated: Whether to include deprecated voices
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Sequence of matching VoiceProfile objects
        """
        pass

    @abstractmethod
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
        """Count voices matching filters.

        Args:
            provider: Filter by provider name
            language: Filter by language code
            gender: Filter by gender
            age_group: Filter by age group
            style: Filter by style
            include_deprecated: Whether to include deprecated voices

        Returns:
            Number of matching voices
        """
        pass

    @abstractmethod
    async def upsert(self, voice: VoiceProfile) -> VoiceProfile:
        """Insert or update a voice profile.

        Args:
            voice: Voice profile to upsert

        Returns:
            Updated voice profile with synced_at timestamp
        """
        pass

    @abstractmethod
    async def upsert_batch(self, voices: Sequence[VoiceProfile]) -> int:
        """Batch upsert voice profiles.

        Args:
            voices: Sequence of voice profiles to upsert

        Returns:
            Number of affected rows
        """
        pass

    @abstractmethod
    async def mark_deprecated(
        self,
        voice_ids: Sequence[str],
    ) -> int:
        """Mark voices as deprecated.

        Args:
            voice_ids: Sequence of voice IDs to deprecate

        Returns:
            Number of affected rows
        """
        pass

    @abstractmethod
    async def get_last_sync_time(self, provider: str) -> datetime | None:
        """Get the last sync time for a provider.

        Args:
            provider: Provider name

        Returns:
            Last sync timestamp, or None if never synced
        """
        pass

    @abstractmethod
    async def get_voice_ids_by_provider(
        self,
        provider: str,
        include_deprecated: bool = False,
    ) -> Sequence[str]:
        """Get all voice IDs for a provider.

        Useful for determining which voices to deprecate during sync.

        Args:
            provider: Provider name
            include_deprecated: Whether to include deprecated voices

        Returns:
            Sequence of voice IDs (format: provider:voice_id)
        """
        pass

    @abstractmethod
    async def update_sample_audio_url(
        self,
        voice_cache_id: str,
        sample_audio_url: str,
    ) -> None:
        """Update the sample audio URL for a voice.

        Args:
            voice_cache_id: The voice cache ID (format: provider:voice_id)
            sample_audio_url: URL to the preview audio file
        """
        pass
