"""Bulk Update Voice Customization Use Case.

Feature: 013-tts-role-mgmt
T050: Create BulkUpdateVoiceCustomizationUseCase
"""

from dataclasses import dataclass

from src.domain.entities.voice_customization import VoiceCustomization
from src.domain.repositories.voice_customization_repository import (
    IVoiceCustomizationRepository,
)


@dataclass
class BulkUpdateItem:
    """Single item in a bulk update request."""

    voice_cache_id: str
    custom_name: str | None = None
    is_favorite: bool | None = None
    is_hidden: bool | None = None


@dataclass
class BulkUpdateInput:
    """Input for bulk update operation."""

    updates: list[BulkUpdateItem]


@dataclass
class BulkUpdateFailure:
    """Failed item in a bulk update result."""

    voice_cache_id: str
    error: str


@dataclass
class BulkUpdateOutput:
    """Output from bulk update operation."""

    updated_count: int
    failed: list[BulkUpdateFailure]


class BulkUpdateVoiceCustomizationUseCase:
    """Use case for bulk updating voice customizations.

    Processes up to 50 updates in a single request. Each item is
    validated independently - failures don't block other updates.
    """

    MAX_UPDATES = 50

    def __init__(self, repository: IVoiceCustomizationRepository) -> None:
        self._repository = repository

    async def execute(self, input_data: BulkUpdateInput) -> BulkUpdateOutput:
        """Bulk update voice customizations.

        Args:
            input_data: Bulk update request

        Returns:
            Result with success count and any failures

        Raises:
            ValueError: If more than MAX_UPDATES items are provided
        """
        if len(input_data.updates) > self.MAX_UPDATES:
            raise ValueError(f"Maximum {self.MAX_UPDATES} updates per request")

        # Build customization entities from input items
        customizations: list[VoiceCustomization] = []
        for item in input_data.updates:
            c = VoiceCustomization(
                voice_cache_id=item.voice_cache_id,
                custom_name=item.custom_name if item.custom_name else None,
                is_favorite=item.is_favorite if item.is_favorite is not None else False,
                is_hidden=item.is_hidden if item.is_hidden is not None else False,
            )

            # Apply business rule: hidden voices are auto-unfavorited
            if c.is_hidden:
                c.mark_as_hidden()

            customizations.append(c)

        success_count, failures = await self._repository.bulk_update(customizations)

        return BulkUpdateOutput(
            updated_count=success_count,
            failed=[BulkUpdateFailure(voice_cache_id=vid, error=err) for vid, err in failures],
        )
