"""Update Voice Customization Use Case.

Feature: 013-tts-role-mgmt
T013: Create UpdateVoiceCustomizationUseCase
"""

from dataclasses import dataclass

from src.domain.entities.voice_customization import VoiceCustomization
from src.domain.repositories.voice_customization_repository import (
    IVoiceCustomizationRepository,
)


@dataclass
class UpdateVoiceCustomizationInput:
    """Input data for updating a voice customization."""

    voice_cache_id: str
    custom_name: str | None = None  # None means don't update, empty string clears
    is_favorite: bool | None = None  # None means don't update
    is_hidden: bool | None = None  # None means don't update


@dataclass
class UpdateVoiceCustomizationOutput:
    """Output data from updating a voice customization."""

    customization: VoiceCustomization
    created: bool  # True if new record was created, False if existing was updated


class UpdateVoiceCustomizationUseCase:
    """Use case for creating or updating voice customizations.

    This use case implements upsert semantics - if a customization exists
    for the given voice_cache_id, it will be updated. Otherwise, a new
    customization will be created.
    """

    def __init__(self, repository: IVoiceCustomizationRepository) -> None:
        """Initialize with repository.

        Args:
            repository: Voice customization repository
        """
        self._repository = repository

    async def execute(
        self, input_data: UpdateVoiceCustomizationInput
    ) -> UpdateVoiceCustomizationOutput:
        """Update or create a voice customization.

        Args:
            input_data: Update request data

        Returns:
            Updated customization with created flag

        Raises:
            ValueError: If validation fails
        """
        # Get existing customization or create new one
        existing = await self._repository.get_by_voice_cache_id(input_data.voice_cache_id)
        created = existing is None

        customization = existing or VoiceCustomization.create_default(input_data.voice_cache_id)

        # Apply updates (only for fields that are not None in input)
        if input_data.custom_name is not None:
            # Empty string should be treated as None (clear the custom name)
            customization.custom_name = input_data.custom_name if input_data.custom_name else None

        if input_data.is_favorite is not None:
            # Can only favorite if not hidden
            if input_data.is_favorite and not customization.is_hidden:
                customization.is_favorite = True
            elif not input_data.is_favorite:
                customization.is_favorite = False

        if input_data.is_hidden is not None:
            if input_data.is_hidden:
                customization.mark_as_hidden()  # This also unfavorites
            else:
                customization.mark_as_visible()

        # Validate before saving
        errors = customization.validate()
        if errors:
            raise ValueError(f"Validation failed: {', '.join(errors)}")

        # Save and return
        saved = await self._repository.save(customization)
        return UpdateVoiceCustomizationOutput(customization=saved, created=created)
