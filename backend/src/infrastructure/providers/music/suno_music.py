"""Suno AI music generation provider (stub).

NOTE: As of Jan 2026, Suno does NOT provide an official public API.
All known access methods rely on unofficial cookie-based scraping which
violates TOS and is unsuitable for production use.

This stub is provided for forward-compatibility. Implement when/if
Suno releases an official developer API.
"""

from src.application.interfaces.music_provider import (
    IMusicProvider,
    MusicSubmitResult,
    MusicTaskResult,
)


class SunoMusicProvider(IMusicProvider):
    """Suno AI music generation provider (not yet available).

    Raises NotImplementedError for all operations until an
    official Suno API becomes available.
    """

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key

    @property
    def name(self) -> str:
        return "suno"

    @property
    def display_name(self) -> str:
        return "Suno AI"

    async def generate_song(
        self,
        *,
        lyrics: str | None = None,
        prompt: str | None = None,
        model: str | None = None,
    ) -> MusicSubmitResult:
        raise NotImplementedError(
            "Suno AI does not provide an official API. "
            "This provider will be implemented when an official API is released."
        )

    async def generate_instrumental(
        self,
        *,
        prompt: str,
        model: str | None = None,
    ) -> MusicSubmitResult:
        raise NotImplementedError(
            "Suno AI does not provide an official API. "
            "This provider will be implemented when an official API is released."
        )

    async def generate_lyrics(
        self,
        *,
        prompt: str | None = None,
    ) -> MusicSubmitResult:
        raise NotImplementedError(
            "Suno AI does not provide an official API. "
            "This provider will be implemented when an official API is released."
        )

    async def query_task(
        self,
        task_id: str,
        task_type: str,
    ) -> MusicTaskResult:
        raise NotImplementedError(
            "Suno AI does not provide an official API. "
            "This provider will be implemented when an official API is released."
        )

    async def health_check(self) -> bool:
        return False
