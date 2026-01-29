"""VoiceCustomization Repository Interface.

Feature: 013-tts-role-mgmt
Abstract repository interface for voice customization storage.
"""

from abc import ABC, abstractmethod

from src.domain.entities.voice_customization import VoiceCustomization


class IVoiceCustomizationRepository(ABC):
    """Abstract repository interface for voice customizations.

    This interface defines the contract for voice customization storage.
    Implementations handle persistence to specific storage backends.
    """

    @abstractmethod
    async def save(self, customization: VoiceCustomization) -> VoiceCustomization:
        """Save or update a voice customization (upsert).

        If a customization for the voice_cache_id already exists, it will be updated.
        Otherwise, a new record will be created.

        Args:
            customization: Voice customization to save

        Returns:
            Saved voice customization with updated id and timestamps
        """
        pass

    @abstractmethod
    async def get_by_voice_cache_id(self, voice_cache_id: str) -> VoiceCustomization | None:
        """Get a voice customization by voice cache ID.

        Args:
            voice_cache_id: Voice cache ID (format: provider:voice_id)

        Returns:
            Voice customization if found, None otherwise
        """
        pass

    @abstractmethod
    async def list_all(self) -> list[VoiceCustomization]:
        """List all voice customizations.

        Returns:
            List of all voice customizations
        """
        pass

    @abstractmethod
    async def list_by_filter(
        self,
        is_favorite: bool | None = None,
        is_hidden: bool | None = None,
    ) -> list[VoiceCustomization]:
        """List voice customizations with optional filters.

        Args:
            is_favorite: Filter by favorite status (None = no filter)
            is_hidden: Filter by hidden status (None = no filter)

        Returns:
            List of voice customizations matching the filters
        """
        pass

    @abstractmethod
    async def delete(self, voice_cache_id: str) -> bool:
        """Delete a voice customization (reset to defaults).

        Args:
            voice_cache_id: Voice cache ID to delete customization for

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def bulk_update(
        self, customizations: list[VoiceCustomization]
    ) -> tuple[int, list[tuple[str, str]]]:
        """Bulk update multiple voice customizations.

        Args:
            customizations: List of voice customizations to update

        Returns:
            Tuple of (success_count, list of (voice_cache_id, error_message) for failures)
        """
        pass

    @abstractmethod
    async def get_customization_map(
        self, voice_cache_ids: list[str]
    ) -> dict[str, VoiceCustomization]:
        """Get customizations for multiple voice cache IDs.

        Efficiently retrieves customizations for a list of voice IDs.
        Useful for merging customizations with voice profiles.

        Args:
            voice_cache_ids: List of voice cache IDs to look up

        Returns:
            Dictionary mapping voice_cache_id to VoiceCustomization
            (only includes IDs that have customizations)
        """
        pass
