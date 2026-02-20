"""Google Lyria music generation provider.

Feature: 016-integration-gemini-lyria-music
Implements IMusicProvider for Lyria 2 via Vertex AI.
Lyria 2 is a synchronous API — results are returned immediately.
"""

import logging
import uuid

from src.application.interfaces.music_provider import (
    IMusicProvider,
    MusicSubmitResult,
    MusicTaskResult,
    MusicTaskStatus,
)
from src.infrastructure.adapters.lyria.client import (
    LyriaVertexAIClient,
    convert_wav_to_mp3,
)

logger = logging.getLogger(__name__)


class NotSupportedError(Exception):
    """Raised when a Lyria-unsupported operation is attempted."""


class LyriaMusicProvider(IMusicProvider):
    """Google Lyria 2 music generation provider.

    Lyria 2 only supports instrumental/BGM generation.
    Song and lyrics generation raise NotSupportedError.
    Lyria 2 is a synchronous API — generate returns completed results directly.
    """

    def __init__(
        self,
        project_id: str | None = None,
        location: str | None = None,
        model: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self._client = LyriaVertexAIClient(
            project_id=project_id,
            location=location or "us-central1",
            model=model or "lyria-002",
            timeout=timeout or 30.0,
        )

    @property
    def name(self) -> str:
        return "lyria"

    @property
    def display_name(self) -> str:
        return "Google Lyria"

    @property
    def capabilities(self) -> list[str]:
        return ["instrumental"]

    async def generate_song(
        self,
        *,
        lyrics: str | None = None,  # noqa: ARG002
        prompt: str | None = None,  # noqa: ARG002
        model: str | None = None,  # noqa: ARG002
    ) -> MusicSubmitResult:
        raise NotSupportedError("Lyria 2 does not support song generation with vocals")

    async def generate_instrumental(
        self,
        *,
        prompt: str,
        model: str | None = None,  # noqa: ARG002
        negative_prompt: str | None = None,
        seed: int | None = None,
        sample_count: int | None = None,
    ) -> MusicSubmitResult:
        """Generate instrumental music via Lyria 2.

        Lyria 2 is synchronous — this method calls the API and returns
        a COMPLETED result with audio bytes stored in the result.

        Returns:
            MusicSubmitResult with status=COMPLETED and task_id containing
            the storage path of the generated MP3.
        """
        results = await self._client.generate_instrumental(
            prompt=prompt,
            negative_prompt=negative_prompt,
            seed=seed,
            sample_count=sample_count,
        )

        if not results:
            return MusicSubmitResult(
                task_id="",
                provider=self.name,
                status=MusicTaskStatus.FAILED,
            )

        # Convert first result WAV→MP3 (EC-004: fallback to WAV on failure)
        first = results[0]
        try:
            audio_bytes = convert_wav_to_mp3(first.audio_content)
            file_ext = "mp3"
        except Exception:
            logger.warning("WAV→MP3 conversion failed, falling back to WAV")
            audio_bytes = first.audio_content
            file_ext = "wav"

        # Generate a unique task_id to use as storage reference
        task_id = str(uuid.uuid4())

        return MusicSubmitResult(
            task_id=task_id,
            provider=self.name,
            status=MusicTaskStatus.COMPLETED,
            audio_bytes=audio_bytes,
            file_ext=file_ext,
            duration_ms=first.duration_ms,
            extra_results=[
                {
                    "audio_content": r.audio_content,
                    "duration_ms": r.duration_ms,
                }
                for r in results[1:]
            ]
            if len(results) > 1
            else None,
        )

    async def generate_lyrics(
        self,
        *,
        prompt: str | None = None,  # noqa: ARG002
    ) -> MusicSubmitResult:
        raise NotSupportedError("Lyria 2 does not support lyrics generation")

    async def query_task(
        self,
        task_id: str,
        task_type: str,  # noqa: ARG002
    ) -> MusicTaskResult:
        """Query task status — Lyria tasks are always immediately complete."""
        return MusicTaskResult(
            task_id=task_id,
            provider=self.name,
            status=MusicTaskStatus.COMPLETED,
        )

    async def health_check(self) -> bool:
        return await self._client.health_check()
