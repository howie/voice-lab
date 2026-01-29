"""Get Voice Customization Use Case.

Feature: 013-tts-role-mgmt
T014: Create GetVoiceCustomizationUseCase
"""

from src.domain.entities.voice_customization import VoiceCustomization
from src.domain.repositories.voice_customization_repository import (
    IVoiceCustomizationRepository,
)


class GetVoiceCustomizationUseCase:
    """Use case for retrieving voice customizations.

    Returns the customization if it exists, or None for default values.
    """

    def __init__(self, repository: IVoiceCustomizationRepository) -> None:
        """Initialize with repository.

        Args:
            repository: Voice customization repository
        """
        self._repository = repository

    async def execute(self, voice_cache_id: str) -> VoiceCustomization | None:
        """Get customization for a voice.

        Args:
            voice_cache_id: Voice cache ID (format: provider:voice_id)

        Returns:
            VoiceCustomization if exists, None otherwise
        """
        return await self._repository.get_by_voice_cache_id(voice_cache_id)

    async def get_or_default(self, voice_cache_id: str) -> VoiceCustomization:
        """Get customization or return default values.

        Args:
            voice_cache_id: Voice cache ID

        Returns:
            Existing customization or default VoiceCustomization
        """
        customization = await self._repository.get_by_voice_cache_id(voice_cache_id)
        if customization:
            return customization
        return VoiceCustomization.create_default(voice_cache_id)

    async def list_all(self) -> list[VoiceCustomization]:
        """List all customizations.

        Returns:
            List of all voice customizations
        """
        return await self._repository.list_all()

    async def list_favorites(self) -> list[VoiceCustomization]:
        """List favorite customizations.

        Returns:
            List of favorited voice customizations
        """
        return await self._repository.list_by_filter(is_favorite=True)

    async def list_hidden(self) -> list[VoiceCustomization]:
        """List hidden customizations.

        Returns:
            List of hidden voice customizations
        """
        return await self._repository.list_by_filter(is_hidden=True)

    async def get_customization_map(
        self, voice_cache_ids: list[str]
    ) -> dict[str, VoiceCustomization]:
        """Get customizations for multiple voice IDs.

        Args:
            voice_cache_ids: List of voice cache IDs

        Returns:
            Dictionary mapping voice_cache_id to customization
        """
        return await self._repository.get_customization_map(voice_cache_ids)
