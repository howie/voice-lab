"""Gemini TTS Provider using Google AI API.

Implements TTS synthesis using Gemini 2.5 TTS models with support for:
- 30 prebuilt voices
- Natural language style prompts for voice control
- PCM to MP3/WAV/OGG conversion
"""

import asyncio
import base64
import contextlib
import io
import logging
from collections.abc import AsyncGenerator

import httpx
from pydub import AudioSegment

from src.domain.entities.audio import AudioData, AudioFormat
from src.domain.entities.tts import TTSRequest
from src.domain.entities.voice import Gender, VoiceProfile
from src.domain.errors import QuotaExceededError, RateLimitError
from src.infrastructure.providers.tts.base import BaseTTSProvider

logger = logging.getLogger(__name__)


class GeminiTTSProvider(BaseTTSProvider):
    """Gemini TTS provider using Google AI API.

    Features:
    - Models: gemini-2.5-pro-tts (high quality), gemini-2.5-flash-preview-tts (low latency)
    - 30 prebuilt voices with multilingual support
    - Natural language style prompts for emotional/stylistic control
    - Output: PCM 24kHz (converted to MP3/WAV/OGG)
    - Limits: Input max 4000 bytes, output max ~655 seconds
    """

    API_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    # Gemini TTS input limit is 4000 bytes (not characters).
    # CJK characters are 3 bytes each in UTF-8, so ~1333 characters max.
    GEMINI_MAX_INPUT_BYTES = 4000

    # Retry config for transient finishReason=OTHER errors
    _MAX_RETRIES = 2  # total attempts = _MAX_RETRIES + 1
    _RETRY_BACKOFFS = (0.5, 1.0)

    # Retry config for 429 rate limit errors (independent counter)
    _MAX_429_RETRIES = 3
    _429_RETRY_BACKOFFS = (1.0, 2.0, 4.0)
    _429_MAX_RETRY_AFTER = 30  # cap Retry-After header value for sleep

    # 30 Gemini prebuilt voices
    VOICES: dict[str, dict[str, str]] = {
        "Zephyr": {"gender": "male", "description": "Bright and cheerful"},
        "Puck": {"gender": "male", "description": "Playful and energetic"},
        "Charon": {"gender": "male", "description": "Deep and resonant"},
        "Kore": {"gender": "female", "description": "Warm and friendly, good for Chinese"},
        "Fenrir": {"gender": "male", "description": "Bold and confident"},
        "Leda": {"gender": "female", "description": "Gentle and soothing"},
        "Orus": {"gender": "male", "description": "Calm and measured"},
        "Aoede": {"gender": "female", "description": "Melodic and elegant"},
        "Callirrhoe": {"gender": "female", "description": "Clear and articulate"},
        "Autonoe": {"gender": "female", "description": "Professional and polished"},
        "Enceladus": {"gender": "male", "description": "Strong and authoritative"},
        "Iapetus": {"gender": "male", "description": "Wise and thoughtful"},
        "Umbriel": {"gender": "male", "description": "Mysterious and intriguing"},
        "Algieba": {"gender": "male", "description": "Warm and inviting"},
        "Despina": {"gender": "female", "description": "Bright and optimistic"},
        "Erinome": {"gender": "female", "description": "Sophisticated and refined"},
        "Algenib": {"gender": "male", "description": "Enthusiastic and dynamic"},
        "Rasalgethi": {"gender": "male", "description": "Rich and expressive"},
        "Laomedeia": {"gender": "female", "description": "Graceful and composed"},
        "Achernar": {"gender": "male", "description": "Clear and precise"},
        "Alnilam": {"gender": "male", "description": "Steady and reliable"},
        "Schedar": {"gender": "female", "description": "Nurturing and supportive"},
        "Gacrux": {"gender": "male", "description": "Friendly and approachable"},
        "Pulcherrima": {"gender": "female", "description": "Beautiful and harmonious"},
        "Achird": {"gender": "male", "description": "Casual and relaxed"},
        "Zubenelgenubi": {"gender": "male", "description": "Balanced and neutral"},
        "Vindemiatrix": {"gender": "female", "description": "Crisp and clear"},
        "Sadachbia": {"gender": "male", "description": "Hopeful and uplifting"},
        "Sadaltager": {"gender": "male", "description": "Trustworthy and sincere"},
        "Sulafat": {"gender": "female", "description": "Soft and gentle"},
    }

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-pro-preview-tts",
    ):
        """Initialize Gemini TTS provider.

        Args:
            api_key: Google AI API key
            model: Model to use (gemini-2.5-pro-preview-tts or gemini-2.5-flash-preview-tts)
        """
        super().__init__("gemini")
        self._api_key = api_key
        self._model = model
        self._client = httpx.AsyncClient(timeout=180.0)

    @staticmethod
    def _validate_input_byte_length(text_content: str) -> None:
        """Validate that text_content does not exceed Gemini's byte limit.

        Gemini TTS API limits input to 4000 bytes (UTF-8). CJK characters
        use 3 bytes each, so the character limit varies by language.

        Args:
            text_content: The full text to send (including style prompt if any).

        Raises:
            ValueError: If text exceeds the byte limit.
        """
        byte_length = len(text_content.encode("utf-8"))
        if byte_length > GeminiTTSProvider.GEMINI_MAX_INPUT_BYTES:
            char_length = len(text_content)
            raise ValueError(
                f"Gemini TTS input exceeds the {GeminiTTSProvider.GEMINI_MAX_INPUT_BYTES}-byte limit: "
                f"{byte_length} bytes ({char_length} characters). "
                "CJK characters use 3 bytes each. Please shorten the text or split into smaller segments."
            )

    async def _do_synthesize(self, request: TTSRequest) -> AudioData:
        """Synthesize speech using Gemini TTS API.

        Args:
            request: TTS synthesis request

        Returns:
            AudioData with synthesized audio
        """
        url = f"{self.API_URL}/{self._model}:generateContent"

        # Build text content with optional style prompt
        text_content = request.text
        if request.style_prompt:
            text_content = f"{request.style_prompt}: {request.text}"

        # Validate byte-level input length before calling API
        self._validate_input_byte_length(text_content)

        # Extract voice name - strip provider prefix if present (e.g., "gemini:Kore" -> "Kore")
        voice_name = request.voice_id
        if voice_name.startswith("gemini:"):
            voice_name = voice_name[7:]  # Remove "gemini:" prefix

        logger.debug(
            "Gemini TTS request: voice_id=%s -> voice_name=%s, text_len=%d, style=%s",
            request.voice_id,
            voice_name,
            len(text_content),
            request.style_prompt or "(none)",
        )

        payload = {
            "contents": [{"parts": [{"text": text_content}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice_name}}},
            },
        }

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self._api_key,
        }

        # Retry loop for transient finishReason=OTHER errors
        last_error: ValueError | None = None
        for attempt in range(self._MAX_RETRIES + 1):
            # Inner retry loop for 429 rate limiting (independent counter)
            for retry_429 in range(self._MAX_429_RETRIES + 1):
                response = await self._client.post(url, json=payload, headers=headers)

                if response.status_code != 429:
                    break  # Not a 429, proceed to normal handling

                # Extract 429 error details
                try:
                    error_json = response.json()
                    error_message_429 = error_json.get("error", {}).get("message", response.text)
                except Exception:
                    error_message_429 = response.text

                if retry_429 < self._MAX_429_RETRIES:
                    # Determine wait: prefer Retry-After header (capped), else backoff
                    wait = self._429_RETRY_BACKOFFS[retry_429]
                    if "retry-after" in response.headers:
                        with contextlib.suppress(ValueError, TypeError):
                            ra = int(response.headers["retry-after"])
                            wait = min(float(ra), float(self._429_MAX_RETRY_AFTER))

                    logger.warning(
                        "Gemini TTS 429 on attempt %d/%d, retrying after %.1fs: %s",
                        retry_429 + 1,
                        self._MAX_429_RETRIES + 1,
                        wait,
                        error_message_429,
                    )
                    await asyncio.sleep(wait)
                    continue

                # All 429 retries exhausted → always RateLimitError
                retry_after_val = None
                if "retry-after" in response.headers:
                    with contextlib.suppress(ValueError, TypeError):
                        retry_after_val = int(response.headers["retry-after"])

                raise RateLimitError(
                    provider="gemini",
                    retry_after=retry_after_val,
                    original_error=error_message_429,
                )

            if response.status_code != 200:
                # Extract error details from Gemini API response
                try:
                    error_json = response.json()
                    error_message = error_json.get("error", {}).get("message", response.text)
                except Exception:
                    error_message = response.text

                # Detect quota exhaustion in non-429 responses (e.g., status 400)
                is_quota_exhausted = "exceeded your current quota" in error_message.lower()
                if is_quota_exhausted:
                    retry_after = None
                    if "retry-after" in response.headers:
                        with contextlib.suppress(ValueError, TypeError):
                            retry_after = int(response.headers["retry-after"])

                    raise QuotaExceededError(
                        provider="gemini",
                        retry_after=retry_after,
                        original_error=error_message,
                    )

                raise RuntimeError(
                    f"Gemini TTS API error (status {response.status_code}): {error_message}"
                )

            result = response.json()

            # Check for empty or blocked candidates
            candidates = result.get("candidates", [])
            if not candidates:
                logger.error("Gemini TTS returned no candidates: %s", result)
                raise ValueError(
                    "Gemini TTS returned no candidates. "
                    "The input may have been blocked by safety filters."
                )

            candidate = candidates[0]
            finish_reason = candidate.get("finishReason", "")

            # Detect safety-blocked responses (candidates exist but no content)
            if "content" not in candidate:
                if finish_reason == "SAFETY":
                    raise ValueError(
                        "Gemini TTS blocked the request due to safety filters. "
                        "Try rephrasing the text or using a different style prompt."
                    )

                # finishReason=OTHER may be transient — retry
                byte_len = len(text_content.encode("utf-8"))
                char_len = len(text_content)
                logger.warning(
                    "Gemini TTS finishReason=%s on attempt %d/%d (text: %d bytes, %d chars)",
                    finish_reason,
                    attempt + 1,
                    self._MAX_RETRIES + 1,
                    byte_len,
                    char_len,
                )
                last_error = ValueError(
                    f"Gemini TTS returned no audio content (finishReason={finish_reason}). "
                    "This may be caused by Gemini's internal safety filters (e.g. PII detection). "
                    "Try avoiding personal names, addresses, phone numbers, or other "
                    "personally identifiable information in the text."
                )
                if attempt < self._MAX_RETRIES:
                    await asyncio.sleep(self._RETRY_BACKOFFS[attempt])
                    continue
                raise last_error

            # Extract audio data from response
            try:
                audio_base64 = candidate["content"]["parts"][0]["inlineData"]["data"]
            except (KeyError, IndexError) as e:
                logger.error("Unexpected Gemini TTS response structure: %s", candidate)
                raise ValueError(f"Invalid API response structure: {e}") from e

            pcm_data = base64.b64decode(audio_base64)

            # Convert PCM to target format
            audio_data = await self._convert_pcm_to_format(pcm_data, request.output_format)

            return AudioData(
                data=audio_data,
                format=request.output_format,
                sample_rate=24000,
            )

        # Should not reach here, but just in case
        raise last_error  # type: ignore[misc]

    async def _convert_pcm_to_format(self, pcm_data: bytes, target_format: AudioFormat) -> bytes:
        """Convert PCM 24kHz to target audio format.

        Args:
            pcm_data: Raw PCM audio data (16-bit, 24kHz, mono)
            target_format: Target audio format

        Returns:
            Converted audio data
        """
        # Create AudioSegment from raw PCM data
        audio = AudioSegment(
            data=pcm_data,
            sample_width=2,  # 16-bit
            frame_rate=24000,
            channels=1,
        )

        buffer = io.BytesIO()
        format_map = {
            AudioFormat.MP3: "mp3",
            AudioFormat.WAV: "wav",
            AudioFormat.OGG: "ogg",
            AudioFormat.OPUS: "opus",
            AudioFormat.FLAC: "flac",
        }
        export_format = format_map.get(target_format, "mp3")
        audio.export(buffer, format=export_format)
        return buffer.getvalue()

    async def synthesize_stream(self, request: TTSRequest) -> AsyncGenerator[bytes, None]:
        """Synthesize speech with streaming output.

        Note: Gemini TTS doesn't support native streaming, so this synthesizes
        the complete audio and yields it in chunks.

        Args:
            request: TTS synthesis request

        Yields:
            Audio data chunks
        """
        audio = await self._do_synthesize(request)
        # Yield in 32KB chunks for streaming simulation
        chunk_size = 32768
        for i in range(0, len(audio.data), chunk_size):
            yield audio.data[i : i + chunk_size]

    async def list_voices(self, language: str | None = None) -> list[VoiceProfile]:
        """List available Gemini voices.

        Args:
            language: Optional language filter (Gemini voices are multilingual)

        Returns:
            List of available voice profiles
        """
        voices = []
        for voice_id, info in self.VOICES.items():
            voices.append(
                VoiceProfile(
                    id=f"gemini:{voice_id}",
                    provider="gemini",
                    voice_id=voice_id,
                    display_name=voice_id,
                    language=language or "multilingual",
                    gender=Gender.MALE if info["gender"] == "male" else Gender.FEMALE,
                    description=info["description"],
                )
            )
        return voices

    async def get_voice(self, voice_id: str) -> VoiceProfile | None:
        """Get a specific voice profile.

        Args:
            voice_id: Voice identifier (can be "Kore" or "gemini:Kore")

        Returns:
            Voice profile if found, None otherwise
        """
        # Strip provider prefix if present
        lookup_id = voice_id
        if lookup_id.startswith("gemini:"):
            lookup_id = lookup_id[7:]

        if lookup_id in self.VOICES:
            info = self.VOICES[lookup_id]
            return VoiceProfile(
                id=f"gemini:{lookup_id}",
                provider="gemini",
                voice_id=lookup_id,
                display_name=lookup_id,
                language="multilingual",
                gender=Gender.MALE if info["gender"] == "male" else Gender.FEMALE,
                description=info["description"],
            )
        return None

    def get_supported_params(self) -> dict:
        """Get supported parameters and their valid ranges.

        Note: Gemini TTS uses style prompts for control instead of
        traditional speed/pitch/volume parameters.

        Returns:
            Dictionary with parameter names and their constraints
        """
        return {
            "speed": {"min": 0.5, "max": 2.0, "default": 1.0, "note": "Use style prompt"},
            "pitch": {"min": -20.0, "max": 20.0, "default": 0.0, "note": "Use style prompt"},
            "volume": {"min": 0.0, "max": 2.0, "default": 1.0, "note": "Use style prompt"},
            "style_prompt": {
                "type": "string",
                "default": None,
                "description": "Natural language prompt for voice style control",
                "examples": [
                    "Say this cheerfully with excitement",
                    "Speak slowly and calmly",
                    "Use a professional news anchor tone",
                ],
            },
        }

    async def health_check(self) -> bool:
        """Check API connectivity.

        Returns:
            True if API is accessible
        """
        if not self._api_key:
            return False

        try:
            # Simple API connectivity check
            url = f"{self.API_URL}/{self._model}"
            headers = {"x-goog-api-key": self._api_key}
            response = await self._client.get(url, headers=headers)
            # 200 or 404 both indicate the API is reachable
            return response.status_code in (200, 404)
        except Exception:
            return False

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
