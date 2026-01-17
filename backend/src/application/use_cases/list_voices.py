"""List Voices Use Case.

T054: Implement ListVoicesUseCase
Retrieves available voices from TTS providers with optional filtering.
"""

import contextlib
from dataclasses import dataclass

from src.application.interfaces.tts_provider import ITTSProvider


@dataclass
class VoiceProfile:
    """Voice profile information."""

    id: str
    name: str
    provider: str
    language: str
    gender: str | None = None
    description: str | None = None
    sample_url: str | None = None
    supported_styles: list[str] | None = None


@dataclass
class VoiceFilter:
    """Filters for voice listing."""

    provider: str | None = None
    language: str | None = None
    gender: str | None = None
    search: str | None = None


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
        filter: VoiceFilter | None = None,
        limit: int | None = None,
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
                voices = await provider.list_voices(language=filter.language if filter else None)
                for voice in voices:
                    # Convert various VoiceProfile types to use case VoiceProfile
                    # Handle domain VoiceProfile objects (from tts/voice entities)
                    if hasattr(voice, "id"):
                        # It's a dataclass, extract attributes
                        gender_val = getattr(voice, "gender", None)
                        # Convert Gender enum to string if needed
                        if gender_val is not None and hasattr(gender_val, "value"):
                            gender_str = gender_val.value
                        else:
                            gender_str = str(gender_val) if gender_val else None

                        profile = VoiceProfile(
                            id=getattr(voice, "id", ""),
                            name=getattr(voice, "name", getattr(voice, "display_name", "")),
                            provider=provider_name,
                            language=getattr(voice, "language", ""),
                            gender=gender_str,
                            description=getattr(voice, "description", None),
                            sample_url=getattr(
                                voice, "sample_url", getattr(voice, "sample_audio_url", None)
                            ),
                            supported_styles=getattr(
                                voice, "supported_styles", getattr(voice, "styles", None)
                            ),
                        )
                        all_voices.append(profile)
                    else:
                        # Dict format, convert to VoiceProfile
                        profile = VoiceProfile(
                            id=voice.get("id", voice.get("voice_id", "")),
                            name=voice.get("name", voice.get("display_name", "")),
                            provider=provider_name,
                            language=voice.get("language", ""),
                            gender=voice.get("gender"),
                            description=voice.get("description"),
                            sample_url=voice.get("sample_url", voice.get("sample_audio_url")),
                            supported_styles=voice.get("supported_styles", voice.get("styles")),
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

    def _apply_filters(self, voices: list[VoiceProfile], filter: VoiceFilter) -> list[VoiceProfile]:
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

    async def get_voice_by_id(self, provider: str, voice_id: str) -> VoiceProfile | None:
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
                # Handle both VoiceProfile objects and dicts
                if hasattr(voice, "id"):
                    # It's a dataclass
                    vid = getattr(voice, "id", getattr(voice, "voice_id", ""))
                    if vid == voice_id:
                        gender_val = getattr(voice, "gender", None)
                        if gender_val is not None and hasattr(gender_val, "value"):
                            gender_str = gender_val.value
                        else:
                            gender_str = str(gender_val) if gender_val else None

                        return VoiceProfile(
                            id=vid,
                            name=getattr(voice, "name", getattr(voice, "display_name", "")),
                            provider=provider,
                            language=getattr(voice, "language", ""),
                            gender=gender_str,
                            description=getattr(voice, "description", None),
                            sample_url=getattr(
                                voice, "sample_url", getattr(voice, "sample_audio_url", None)
                            ),
                            supported_styles=getattr(
                                voice, "supported_styles", getattr(voice, "styles", None)
                            ),
                        )
                else:
                    # It's a dict
                    vid = voice.get("id", voice.get("voice_id", ""))
                    if vid == voice_id:
                        return VoiceProfile(
                            id=vid,
                            name=voice.get("name", voice.get("display_name", "")),
                            provider=provider,
                            language=voice.get("language", ""),
                            gender=voice.get("gender"),
                            description=voice.get("description"),
                            sample_url=voice.get("sample_url", voice.get("sample_audio_url")),
                            supported_styles=voice.get("supported_styles", voice.get("styles")),
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
    from src.infrastructure.providers.tts.elevenlabs import ElevenLabsTTSProvider
    from src.infrastructure.providers.tts.google import GoogleTTSProvider
    from src.infrastructure.providers.tts.voai import VoAITTSProvider

    providers: dict[str, ITTSProvider] = {}

    # Initialize providers (they handle their own configuration)
    with contextlib.suppress(Exception):
        providers["azure"] = AzureTTSProvider()

    with contextlib.suppress(Exception):
        providers["gcp"] = GoogleTTSProvider()

    with contextlib.suppress(Exception):
        providers["elevenlabs"] = ElevenLabsTTSProvider()

    with contextlib.suppress(Exception):
        providers["voai"] = VoAITTSProvider()

    return ListVoicesUseCase(providers)


# Global instance
list_voices_use_case = create_list_voices_use_case()
