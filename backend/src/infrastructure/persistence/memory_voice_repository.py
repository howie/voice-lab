"""In-Memory Voice Repository Implementation."""

from src.domain.entities.voice import Gender, VoiceProfile
from src.domain.repositories.voice_repository import IVoiceRepository


class InMemoryVoiceRepository(IVoiceRepository):
    """In-memory implementation of voice repository.

    Caches voice profiles from providers.
    """

    def __init__(self):
        self._voices: dict[str, VoiceProfile] = {}

    async def get_by_id(self, voice_id: str, provider: str) -> VoiceProfile | None:
        """Get a voice profile by ID and provider."""
        key = f"{provider}:{voice_id}"
        return self._voices.get(key)

    async def list_by_provider(
        self, provider: str, language: str | None = None
    ) -> list[VoiceProfile]:
        """List voice profiles for a provider."""
        voices = [
            v for v in self._voices.values() if v.provider == provider
        ]

        if language:
            voices = [v for v in voices if v.language == language]

        return sorted(voices, key=lambda v: v.name)

    async def list_by_language(self, language: str) -> list[VoiceProfile]:
        """List voice profiles for a language across all providers."""
        voices = [v for v in self._voices.values() if v.language == language]
        return sorted(voices, key=lambda v: (v.provider, v.name))

    async def save(self, voice: VoiceProfile) -> VoiceProfile:
        """Save or update a voice profile."""
        key = f"{voice.provider}:{voice.voice_id}"
        self._voices[key] = voice
        return voice

    async def save_batch(self, voices: list[VoiceProfile]) -> int:
        """Save multiple voice profiles."""
        for voice in voices:
            await self.save(voice)
        return len(voices)

    async def search(
        self,
        query: str,
        provider: str | None = None,
        language: str | None = None,
        gender: Gender | None = None,
    ) -> list[VoiceProfile]:
        """Search voice profiles."""
        query_lower = query.lower()
        voices = list(self._voices.values())

        # Filter by provider
        if provider:
            voices = [v for v in voices if v.provider == provider]

        # Filter by language
        if language:
            voices = [v for v in voices if v.language == language]

        # Filter by gender
        if gender:
            voices = [v for v in voices if v.gender == gender]

        # Search by query
        results = []
        for v in voices:
            if (
                query_lower in v.name.lower()
                or query_lower in v.voice_id.lower()
                or (v.description and query_lower in v.description.lower())
            ):
                results.append(v)

        return sorted(results, key=lambda v: v.name)
