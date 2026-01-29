"""Mureka AI API client for music generation.

This module provides an async HTTP client for the Mureka AI music generation API.
Supports song generation, instrumental/BGM generation, and lyrics generation.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import httpx

from src.config import get_settings

logger = logging.getLogger(__name__)


class MurekaTaskStatus(str, Enum):
    """Mureka API task status values."""

    PREPARING = "preparing"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class MurekaTaskResult:
    """Result from a Mureka API task query."""

    task_id: str
    status: MurekaTaskStatus
    mp3_url: str | None = None
    cover_url: str | None = None
    lyrics: str | None = None
    duration_ms: int | None = None
    title: str | None = None
    error_message: str | None = None


@dataclass
class MurekaSubmitResult:
    """Result from submitting a generation task."""

    task_id: str
    status: str
    trace_id: str | None = None


class MurekaAPIError(Exception):
    """Exception for Mureka API errors."""

    def __init__(self, message: str, status_code: int | None = None, details: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


class MurekaAPIClient:
    """Async client for Mureka AI music generation API.

    Provides methods for:
    - Song generation (with vocals)
    - Instrumental/BGM generation
    - Lyrics generation and extension
    - Task status polling
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 60.0,
    ):
        """Initialize the Mureka API client.

        Args:
            api_key: Mureka API key. If None, uses settings.mureka_api_key
            base_url: API base URL. If None, uses settings.mureka_api_base_url
            timeout: Request timeout in seconds
        """
        settings = get_settings()
        self.api_key = api_key or settings.mureka_api_key
        self.base_url = (base_url or settings.mureka_api_base_url).rstrip("/")
        self.timeout = timeout

        if not self.api_key:
            logger.warning("Mureka API key not configured")

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authentication."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request to the Mureka API.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            json_body: Request body for POST requests

        Returns:
            Parsed JSON response

        Raises:
            MurekaAPIError: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=json_body)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                if response.status_code == 401:
                    raise MurekaAPIError(
                        "Authentication failed - invalid API key",
                        status_code=401,
                    )
                elif response.status_code == 402:
                    raise MurekaAPIError(
                        "Insufficient credits - please top up your account",
                        status_code=402,
                    )
                elif response.status_code == 429:
                    raise MurekaAPIError(
                        "Rate limit exceeded - too many concurrent requests",
                        status_code=429,
                    )
                elif response.status_code >= 400:
                    error_detail = response.text
                    try:
                        error_json = response.json()
                        error_detail = error_json.get("message", error_detail)
                    except Exception:
                        pass
                    raise MurekaAPIError(
                        f"API error: {error_detail}",
                        status_code=response.status_code,
                    )

                return response.json()

            except httpx.TimeoutException as e:
                raise MurekaAPIError(f"Request timeout: {e}") from e
            except httpx.RequestError as e:
                raise MurekaAPIError(f"Request failed: {e}") from e

    # =========================================================================
    # Song Generation
    # =========================================================================

    async def submit_song(
        self,
        lyrics: str | None = None,
        prompt: str | None = None,
        model: str = "auto",
    ) -> MurekaSubmitResult:
        """Submit a song generation task.

        Args:
            lyrics: Song lyrics with optional section markers like [Verse], [Chorus]
            prompt: Style description (e.g., "pop, upbeat, female vocal")
            model: Model selection (auto, mureka-01, v7.5, v6)

        Returns:
            MurekaSubmitResult with task_id

        Raises:
            MurekaAPIError: If submission fails
            ValueError: If neither lyrics nor prompt is provided
        """
        if not lyrics and not prompt:
            raise ValueError("Either lyrics or prompt must be provided for song generation")

        body: dict[str, Any] = {"model": model}
        if lyrics:
            body["lyrics"] = lyrics
        if prompt:
            body["prompt"] = prompt

        logger.info(f"Submitting song generation: model={model}")
        result = await self._make_request("POST", "/v1/song/generate", body)

        return MurekaSubmitResult(
            task_id=result["id"],
            status=result.get("status", "preparing"),
            trace_id=result.get("trace_id"),
        )

    async def query_song_task(self, task_id: str) -> MurekaTaskResult:
        """Query the status of a song generation task.

        Args:
            task_id: Task ID from submit_song

        Returns:
            MurekaTaskResult with current status and result if completed
        """
        result = await self._make_request("GET", f"/v1/song/query/{task_id}")

        status = MurekaTaskStatus(result.get("status", "processing"))
        song_data = result.get("song", {})

        return MurekaTaskResult(
            task_id=task_id,
            status=status,
            mp3_url=song_data.get("mp3_url"),
            cover_url=song_data.get("cover"),
            lyrics=song_data.get("lyrics"),
            duration_ms=song_data.get("duration_milliseconds"),
            title=song_data.get("title"),
            error_message=result.get("error"),
        )

    # =========================================================================
    # Instrumental/BGM Generation
    # =========================================================================

    async def submit_instrumental(
        self,
        prompt: str,
        model: str = "auto",
    ) -> MurekaSubmitResult:
        """Submit an instrumental/BGM generation task.

        Args:
            prompt: Scene/style description (e.g., "relaxing coffee shop, acoustic guitar")
            model: Model selection (auto, mureka-01, v7.5, v6)

        Returns:
            MurekaSubmitResult with task_id

        Raises:
            MurekaAPIError: If submission fails
        """
        body = {
            "prompt": prompt,
            "model": model,
        }

        logger.info(f"Submitting instrumental generation: model={model}")
        result = await self._make_request("POST", "/v1/instrumental/generate", body)

        return MurekaSubmitResult(
            task_id=result["id"],
            status=result.get("status", "preparing"),
            trace_id=result.get("trace_id"),
        )

    async def query_instrumental_task(self, task_id: str) -> MurekaTaskResult:
        """Query the status of an instrumental generation task.

        Args:
            task_id: Task ID from submit_instrumental

        Returns:
            MurekaTaskResult with current status and result if completed
        """
        result = await self._make_request("GET", f"/v1/instrumental/query/{task_id}")

        status = MurekaTaskStatus(result.get("status", "processing"))
        music_data = result.get("instrumental", result.get("song", {}))

        return MurekaTaskResult(
            task_id=task_id,
            status=status,
            mp3_url=music_data.get("mp3_url"),
            duration_ms=music_data.get("duration_milliseconds"),
            title=music_data.get("title"),
            error_message=result.get("error"),
        )

    # =========================================================================
    # Lyrics Generation
    # =========================================================================

    async def submit_lyrics(
        self,
        prompt: str | None = None,
    ) -> MurekaSubmitResult:
        """Submit a lyrics generation task.

        Args:
            prompt: Theme/topic description. If None, generates random lyrics.

        Returns:
            MurekaSubmitResult with task_id

        Raises:
            MurekaAPIError: If submission fails
        """
        body: dict[str, Any] = {}
        if prompt:
            body["prompt"] = prompt

        logger.info("Submitting lyrics generation")
        result = await self._make_request("POST", "/v1/lyrics/generate", body)

        return MurekaSubmitResult(
            task_id=result.get("id", ""),
            status=result.get("status", "completed"),
            trace_id=result.get("trace_id"),
        )

    async def extend_lyrics(
        self,
        lyrics: str,
        prompt: str | None = None,
    ) -> MurekaSubmitResult:
        """Submit a lyrics extension task.

        Args:
            lyrics: Existing lyrics to extend
            prompt: Direction for extension (optional)

        Returns:
            MurekaSubmitResult with task_id

        Raises:
            MurekaAPIError: If submission fails
        """
        body: dict[str, Any] = {"lyrics": lyrics}
        if prompt:
            body["prompt"] = prompt

        logger.info("Submitting lyrics extension")
        result = await self._make_request("POST", "/v1/lyrics/extend", body)

        return MurekaSubmitResult(
            task_id=result.get("id", ""),
            status=result.get("status", "completed"),
            trace_id=result.get("trace_id"),
        )

    # =========================================================================
    # Generic Task Query
    # =========================================================================

    async def query_task(
        self,
        task_id: str,
        task_type: str,
    ) -> MurekaTaskResult:
        """Query the status of any generation task.

        Args:
            task_id: Task ID from submission
            task_type: Type of task ("song", "instrumental", "lyrics")

        Returns:
            MurekaTaskResult with current status and result if completed
        """
        if task_type == "song":
            return await self.query_song_task(task_id)
        elif task_type == "instrumental":
            return await self.query_instrumental_task(task_id)
        else:
            # Lyrics are typically synchronous
            return MurekaTaskResult(
                task_id=task_id,
                status=MurekaTaskStatus.COMPLETED,
            )
