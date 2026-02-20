"""Google Vertex AI Lyria 2 REST API client.

Feature: 016-integration-gemini-lyria-music
Low-level HTTP client for Lyria music generation via Vertex AI predict endpoint.
"""

import base64
import io
import logging
from dataclasses import dataclass

import google.auth
import google.auth.transport.requests
import httpx
from pydub import AudioSegment

from src.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class LyriaGenerationResult:
    """Single result from Lyria Vertex AI API."""

    audio_content: bytes  # Decoded WAV audio data
    mime_type: str = "audio/wav"
    sample_rate: int = 48000
    duration_ms: int = 32800  # ~32.8s fixed for Lyria 2


class LyriaAPIError(Exception):
    """Raised when Lyria Vertex AI API returns an error."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message
        super().__init__(f"Lyria API error {status_code}: {message}")


class LyriaAuthError(LyriaAPIError):
    """Raised on authentication/authorization failure (401/403)."""


class LyriaSafetyFilterError(LyriaAPIError):
    """Raised when prompt is rejected by safety filter (400)."""


class LyriaRateLimitError(LyriaAPIError):
    """Raised on rate limit (429)."""


class LyriaVertexAIClient:
    """Google Vertex AI Lyria 2 REST API client.

    Uses Application Default Credentials (ADC) for authentication.
    Sends predict requests to Vertex AI and returns decoded audio.
    """

    def __init__(
        self,
        project_id: str | None = None,
        location: str = "us-central1",
        model: str = "lyria-002",
        timeout: float = 30.0,
    ) -> None:
        settings = get_settings()
        self._project_id = project_id or settings.lyria_gcp_project_id or settings.gcp_project_id
        self._location = location or settings.lyria_gcp_location
        self._model = model or settings.lyria_model
        self._timeout = timeout or settings.lyria_timeout

        # Load ADC credentials
        self._credentials, detected_project = google.auth.default()
        if not self._project_id:
            self._project_id = detected_project or ""

        self._http_client = httpx.AsyncClient(timeout=self._timeout)

    @property
    def _endpoint_url(self) -> str:
        return (
            f"https://{self._location}-aiplatform.googleapis.com/v1/"
            f"projects/{self._project_id}/locations/{self._location}/"
            f"publishers/google/models/{self._model}:predict"
        )

    def _get_access_token(self) -> str:
        """Refresh and return a valid access token."""
        self._credentials.refresh(google.auth.transport.requests.Request())
        return self._credentials.token

    async def generate_instrumental(
        self,
        *,
        prompt: str,
        negative_prompt: str | None = None,
        seed: int | None = None,
        sample_count: int | None = None,
    ) -> list[LyriaGenerationResult]:
        """Generate instrumental music via Vertex AI predict endpoint.

        Args:
            prompt: English music description
            negative_prompt: Elements to exclude
            seed: Random seed for reproducibility
            sample_count: Number of variants (1-4)

        Returns:
            List of LyriaGenerationResult (one per sample)

        Raises:
            LyriaAuthError: On 401/403 authentication failure
            LyriaSafetyFilterError: On 400 safety filter rejection
            LyriaRateLimitError: On 429 rate limit
            LyriaAPIError: On other API errors
        """
        # Build request payload
        instance: dict = {"prompt": prompt}
        if negative_prompt:
            instance["negative_prompt"] = negative_prompt
        if seed is not None:
            instance["seed"] = seed

        payload: dict = {"instances": [instance]}
        if sample_count and sample_count > 1:
            payload["parameters"] = {"sample_count": sample_count}

        token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        logger.info(
            "Lyria generate_instrumental: model=%s, prompt_len=%d, negative=%s, seed=%s, samples=%s",
            self._model,
            len(prompt),
            bool(negative_prompt),
            seed,
            sample_count,
        )

        # Retry logic for transient errors (FR-016: max 3 attempts)
        max_retries = 3
        backoff_seconds = [2, 4, 8]

        for attempt in range(max_retries):
            try:
                response = await self._http_client.post(
                    self._endpoint_url,
                    headers=headers,
                    json=payload,
                )
                break
            except httpx.TransportError:
                if attempt < max_retries - 1:
                    import asyncio

                    await asyncio.sleep(backoff_seconds[attempt])
                    logger.warning(
                        "Lyria request transport error, retry %d/%d", attempt + 1, max_retries
                    )
                    continue
                raise

        self._handle_error_response(response)

        data = response.json()
        predictions = data.get("predictions", [])

        results: list[LyriaGenerationResult] = []
        for pred in predictions:
            audio_b64 = pred.get("audioContent", "")
            audio_bytes = base64.b64decode(audio_b64)
            results.append(
                LyriaGenerationResult(
                    audio_content=audio_bytes,
                    mime_type=pred.get("mimeType", "audio/wav"),
                )
            )

        logger.info("Lyria generation complete: %d result(s)", len(results))
        return results

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Map HTTP status codes to typed exceptions."""
        if response.is_success:
            return

        status = response.status_code
        try:
            body = response.json()
            message = body.get("error", {}).get("message", response.text)
        except Exception:
            message = response.text

        if status in (401, 403):
            raise LyriaAuthError(status, "Google Cloud 認證失敗，請檢查 Service Account 設定")
        if status == 400:
            raise LyriaSafetyFilterError(status, "您的描述被安全過濾器攔截，請修改內容")
        if status == 429:
            raise LyriaRateLimitError(status, "Google Cloud 配額不足，請稍後再試")
        raise LyriaAPIError(status, message)

    async def health_check(self) -> bool:
        """Test Vertex AI connectivity by refreshing credentials."""
        try:
            self._get_access_token()
            return True
        except Exception:
            logger.exception("Lyria health check failed")
            return False

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._http_client.aclose()


def convert_wav_to_mp3(wav_bytes: bytes, bitrate: str = "192k") -> bytes:
    """Convert WAV audio bytes to MP3 using pydub.

    Args:
        wav_bytes: Raw WAV audio data
        bitrate: MP3 encoding bitrate (default 192k for high quality)

    Returns:
        MP3 audio bytes

    Raises:
        Exception: If conversion fails (caller should handle fallback to WAV)
    """
    audio = AudioSegment.from_wav(io.BytesIO(wav_bytes))
    mp3_buffer = io.BytesIO()
    audio.export(mp3_buffer, format="mp3", bitrate=bitrate)
    return mp3_buffer.getvalue()
