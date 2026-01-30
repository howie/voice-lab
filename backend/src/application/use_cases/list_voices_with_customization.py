"""List Voices with Customization Use Case.

Feature: 013-tts-role-mgmt
T023: Modify ListVoicesUseCase to include display_name (via new use case)

This use case retrieves voices from voice_cache and merges in
customization data for display_name, is_favorite, is_hidden.
"""

from dataclasses import dataclass

from src.application.interfaces.voice_cache_repository import IVoiceCacheRepository
from src.domain.entities.voice import AgeGroup
from src.domain.repositories.voice_customization_repository import (
    IVoiceCustomizationRepository,
)


@dataclass
class VoiceWithCustomization:
    """Voice profile merged with customization data."""

    id: str  # voice_cache_id (format: provider:voice_id)
    provider: str
    voice_id: str
    name: str  # Original name from provider
    display_name: str  # Custom name if set, otherwise original name
    language: str
    gender: str | None
    age_group: str | None
    styles: list[str]
    use_cases: list[str]
    sample_audio_url: str | None
    is_deprecated: bool
    is_favorite: bool
    is_hidden: bool


@dataclass
class VoiceListResult:
    """Paginated result of voices with customizations."""

    items: list[VoiceWithCustomization]
    total: int
    limit: int
    offset: int


@dataclass
class VoiceListFilters:
    """Filters for voice listing."""

    provider: str | None = None
    language: str | None = None
    gender: str | None = None
    age_group: str | None = None
    search: str | None = None
    exclude_hidden: bool = True  # Default: exclude hidden voices
    favorites_only: bool = False
    limit: int = 100
    offset: int = 0


class ListVoicesWithCustomizationUseCase:
    """Use case for listing voices with customization data merged."""

    def __init__(
        self,
        voice_cache_repo: IVoiceCacheRepository,
        customization_repo: IVoiceCustomizationRepository,
    ) -> None:
        """Initialize with repositories.

        Args:
            voice_cache_repo: Repository for voice cache data
            customization_repo: Repository for voice customizations
        """
        self._voice_cache_repo = voice_cache_repo
        self._customization_repo = customization_repo

    async def execute(self, filters: VoiceListFilters | None = None) -> VoiceListResult:
        """List voices with customization data.

        Args:
            filters: Optional filters to apply

        Returns:
            Paginated list of voices with customizations
        """
        filters = filters or VoiceListFilters()

        # Convert string age_group to enum if provided
        age_group_enum = AgeGroup(filters.age_group) if filters.age_group else None

        # Get voices from cache - get more than limit to apply post-filtering
        # We need to handle exclude_hidden and favorites_only after merging customizations
        # So fetch a larger set first
        fetch_limit = (
            (filters.offset + filters.limit) * 2
            if filters.exclude_hidden or filters.favorites_only
            else filters.limit
        )
        fetch_offset = 0 if filters.exclude_hidden or filters.favorites_only else filters.offset

        voices = await self._voice_cache_repo.list_all(
            provider=filters.provider,
            language=filters.language,
            gender=filters.gender,
            age_group=age_group_enum,
            include_deprecated=False,
            limit=fetch_limit,
            offset=fetch_offset,
        )

        # Get customizations for these voices
        voice_ids = [v.id for v in voices]
        customization_map = await self._customization_repo.get_customization_map(voice_ids)

        # Build results with merged data
        results: list[VoiceWithCustomization] = []
        for voice in voices:
            customization = customization_map.get(voice.id)

            # Get display name
            display_name = voice.display_name
            if customization and customization.custom_name:
                display_name = customization.custom_name

            is_favorite = customization.is_favorite if customization else False
            is_hidden = customization.is_hidden if customization else False

            # Apply search filter (on both name and custom_name)
            if filters.search:
                search_lower = filters.search.lower()
                if (
                    search_lower not in voice.display_name.lower()
                    and search_lower not in display_name.lower()
                    and search_lower not in voice.id.lower()
                ):
                    continue

            # Apply exclude_hidden filter
            if filters.exclude_hidden and is_hidden:
                continue

            # Apply favorites_only filter
            if filters.favorites_only and not is_favorite:
                continue

            results.append(
                VoiceWithCustomization(
                    id=voice.id,
                    provider=voice.provider,
                    voice_id=voice.voice_id,
                    name=voice.display_name,
                    display_name=display_name,
                    language=voice.language,
                    gender=voice.gender.value if voice.gender else None,
                    age_group=voice.age_group.value if voice.age_group else None,
                    styles=list(voice.styles),
                    use_cases=list(voice.use_cases),
                    sample_audio_url=voice.sample_audio_url,
                    is_deprecated=voice.is_deprecated,
                    is_favorite=is_favorite,
                    is_hidden=is_hidden,
                )
            )

        # Sort: favorites first, then by provider and name
        results.sort(key=lambda v: (not v.is_favorite, v.provider, v.name))

        # Get total count
        total = len(results)

        # Apply pagination if we did post-filtering
        if filters.exclude_hidden or filters.favorites_only or filters.search:
            results = results[filters.offset : filters.offset + filters.limit]
        else:
            # Pagination was already applied in the query
            pass

        return VoiceListResult(
            items=results,
            total=total,
            limit=filters.limit,
            offset=filters.offset,
        )
