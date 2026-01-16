"""Voice Repository Interface."""

from abc import ABC, abstractmethod

from src.domain.entities.voice import VoiceProfile, Gender


class IVoiceRepository(ABC):
    """Abstract repository interface for voice profiles.

    This interface defines the contract for voice profile storage.
    """

    @abstractmethod
    async def save(self, voice: VoiceProfile) -> VoiceProfile:
        """Save a voice profile.

        Args:
            voice: Voice profile to save

        Returns:
            Saved voice profile
        """
        pass

    @abstractmethod
    async def get_by_id(self, voice_id: str) -> VoiceProfile | None:
        """Get a voice profile by ID.

        Args:
            voice_id: Voice profile ID

        Returns:
            Voice profile if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_provider_voice_id(
        self, provider: str, provider_voice_id: str
    ) -> VoiceProfile | None:
        """Get a voice profile by provider and provider-specific voice ID.

        Args:
            provider: Provider name
            provider_voice_id: Provider-specific voice ID

        Returns:
            Voice profile if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_voices(
        self,
        provider: str | None = None,
        language: str | None = None,
        gender: Gender | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[VoiceProfile]:
        """List voice profiles with filters.

        Args:
            provider: Filter by provider
            language: Filter by language (supports prefix matching, e.g., "zh")
            gender: Filter by gender
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of voice profiles matching the filters
        """
        pass

    @abstractmethod
    async def list_by_provider(self, provider: str) -> list[VoiceProfile]:
        """List all voice profiles for a specific provider.

        Args:
            provider: Provider name

        Returns:
            List of voice profiles for the provider
        """
        pass

    @abstractmethod
    async def delete(self, voice_id: str) -> bool:
        """Delete a voice profile.

        Args:
            voice_id: Voice profile ID to delete

        Returns:
            True if deleted, False if not found
        """
        pass
