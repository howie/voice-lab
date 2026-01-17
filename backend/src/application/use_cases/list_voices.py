"""List Voices Use Case.

T054: Implement ListVoicesUseCase
Retrieves available voices from TTS providers with optional filtering.
"""

from dataclasses import dataclass
from typing import Optional

from src.application.interfaces.tts_provider import ITTSProvider


@dataclass
class VoiceProfile:
    """Voice profile information."""

    id: str
    name: str
    provider: str
    language: str
    gender: Optional[str] = None
    description: Optional[str] = None
    sample_url: Optional[str] = None
    supported_styles: Optional[list[str]] = None


@dataclass
class VoiceFilter:
    """Filters for voice listing."""

    provider: Optional[str] = None
    language: Optional[str] = None
    gender: Optional[str] = None
    search: Optional[str] = None


class ListVoicesUseCase:
    """Use case for listing available voices from TTS providers."""

    def __init__(self, providers: dict[str, ITTSProvider]):
        """Initialize with available TTS providers.

        Args:
            providers: Dictionary mapping provider names to provider instances
        """
        self._providers = providers

    async def execute(
        self,
        filter: Optional[VoiceFilter] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> list[VoiceProfile]:
        """List available voices with optional filtering.

        Args:
            filter: Optional filters to apply
            limit: Maximum number of voices to return
            offset: Number of voices to skip

        Returns:
            List of voice profiles matching the filters
        """
        all_voices: list[VoiceProfile] = []

        # Determine which providers to query
        if filter and filter.provider:
            providers_to_query = {filter.provider: self._providers.get(filter.provider)}
            providers_to_query = {k: v for k, v in providers_to_query.items() if v}
        else:
            providers_to_query = self._providers

        # Fetch voices from each provider
        for provider_name, provider in providers_to_query.items():
            try:
                voices = await provider.list_voices(
                    language=filter.language if filter else None
                )
                for voice in voices:
                    profile = VoiceProfile(
                        id=voice.get("id", voice.get("voice_id", "")),
                        name=voice.get("name", voice.get("display_name", "")),
                        provider=provider_name,
                        language=voice.get("language", ""),
                        gender=voice.get("gender"),
                        description=voice.get("description"),
                        sample_url=voice.get("sample_url"),
                        supported_styles=voice.get("supported_styles"),
                    )
                    all_voices.append(profile)
            except Exception as e:
                # Log error but continue with other providers
                print(f"Error fetching voices from {provider_name}: {e}")
                continue

        # Apply filters
        if filter:
            all_voices = self._apply_filters(all_voices, filter)

        # Apply pagination
        if offset:
            all_voices = all_voices[offset:]
        if limit:
            all_voices = all_voices[:limit]

        return all_voices

    def _apply_filters(
        self, voices: list[VoiceProfile], filter: VoiceFilter
    ) -> list[VoiceProfile]:
        """Apply filters to voice list.

        Args:
            voices: List of voices to filter
            filter: Filters to apply

        Returns:
            Filtered list of voices
        """
        filtered = voices

        if filter.gender:
            filtered = [v for v in filtered if v.gender == filter.gender]

        if filter.search:
            search_lower = filter.search.lower()
            filtered = [
                v
                for v in filtered
                if search_lower in v.name.lower()
                or search_lower in v.id.lower()
                or (v.description and search_lower in v.description.lower())
            ]

        return filtered

    async def get_voice_by_id(
        self, provider: str, voice_id: str
    ) -> Optional[VoiceProfile]:
        """Get a specific voice by provider and voice ID.

        Args:
            provider: Provider name
            voice_id: Voice ID

        Returns:
            Voice profile if found, None otherwise
        """
        if provider not in self._providers:
            return None

        provider_instance = self._providers[provider]

        try:
            voices = await provider_instance.list_voices()
            for voice in voices:
                vid = voice.get("id", voice.get("voice_id", ""))
                if vid == voice_id:
                    return VoiceProfile(
                        id=vid,
                        name=voice.get("name", voice.get("display_name", "")),
                        provider=provider,
                        language=voice.get("language", ""),
                        gender=voice.get("gender"),
                        description=voice.get("description"),
                        sample_url=voice.get("sample_url"),
                        supported_styles=voice.get("supported_styles"),
                    )
        except Exception:
            pass

        return None


# Factory function to create use case with default providers
def create_list_voices_use_case() -> ListVoicesUseCase:
    """Create ListVoicesUseCase with configured providers.

    Returns:
        Configured ListVoicesUseCase instance
    """
    from src.infrastructure.providers.tts.azure import AzureTTSProvider
    from src.infrastructure.providers.tts.google import GoogleTTSProvider
    from src.infrastructure.providers.tts.elevenlabs import ElevenLabsTTSProvider
    from src.infrastructure.providers.tts.voai import VoAITTSProvider

    providers: dict[str, ITTSProvider] = {}

    # Initialize providers (they handle their own configuration)
    try:
        providers["azure"] = AzureTTSProvider()
    except Exception:
        pass

    try:
        providers["gcp"] = GoogleTTSProvider()
    except Exception:
        pass

    try:
        providers["elevenlabs"] = ElevenLabsTTSProvider()
    except Exception:
        pass

    try:
        providers["voai"] = VoAITTSProvider()
    except Exception:
        pass

    return ListVoicesUseCase(providers)


# Global instance
list_voices_use_case = create_list_voices_use_case()
