"""Mureka AI music generation provider.

Wraps the existing MurekaAPIClient to implement the IMusicProvider interface.
"""

import logging

from src.application.interfaces.music_provider import (
    IMusicProvider,
    MusicSubmitResult,
    MusicTaskResult,
    MusicTaskStatus,
)
from src.infrastructure.adapters.mureka.client import (
    MurekaAPIClient,
    MurekaTaskStatus,
)

logger = logging.getLogger(__name__)

# Map Mureka-specific statuses to unified statuses
_STATUS_MAP: dict[MurekaTaskStatus, MusicTaskStatus] = {
    MurekaTaskStatus.PREPARING: MusicTaskStatus.PENDING,
    MurekaTaskStatus.PROCESSING: MusicTaskStatus.PROCESSING,
    MurekaTaskStatus.COMPLETED: MusicTaskStatus.COMPLETED,
    MurekaTaskStatus.FAILED: MusicTaskStatus.FAILED,
}


class MurekaMusicProvider(IMusicProvider):
    """Mureka AI music generation provider.

    Delegates to MurekaAPIClient for actual API calls and maps
    responses to the unified IMusicProvider interface.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 60.0,
    ):
        self._client = MurekaAPIClient(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )

    @property
    def name(self) -> str:
        return "mureka"

    @property
    def display_name(self) -> str:
        return "Mureka AI"

    async def generate_song(
        self,
        *,
        lyrics: str | None = None,
        prompt: str | None = None,
        model: str | None = None,
    ) -> MusicSubmitResult:
        result = await self._client.submit_song(
            lyrics=lyrics,
            prompt=prompt,
            model=model or "auto",
        )
        return MusicSubmitResult(
            task_id=result.task_id,
            provider=self.name,
            status=MusicTaskStatus.PENDING,
        )

    async def generate_instrumental(
        self,
        *,
        prompt: str,
        model: str | None = None,
    ) -> MusicSubmitResult:
        result = await self._client.submit_instrumental(
            prompt=prompt,
            model=model or "auto",
        )
        return MusicSubmitResult(
            task_id=result.task_id,
            provider=self.name,
            status=MusicTaskStatus.PENDING,
        )

    async def generate_lyrics(
        self,
        *,
        prompt: str | None = None,
    ) -> MusicSubmitResult:
        result = await self._client.submit_lyrics(prompt=prompt)
        return MusicSubmitResult(
            task_id=result.task_id,
            provider=self.name,
            # Mureka lyrics generation is synchronous
            status=MusicTaskStatus.COMPLETED,
        )

    async def query_task(
        self,
        task_id: str,
        task_type: str,
    ) -> MusicTaskResult:
        result = await self._client.query_task(task_id, task_type)
        return MusicTaskResult(
            task_id=result.task_id,
            provider=self.name,
            status=_STATUS_MAP.get(result.status, MusicTaskStatus.PROCESSING),
            audio_url=result.mp3_url,
            cover_url=result.cover_url,
            lyrics=result.lyrics,
            duration_ms=result.duration_ms,
            title=result.title,
            error_message=result.error_message,
        )

    async def health_check(self) -> bool:
        return bool(self._client.api_key)
