"""Azure Voice Fetcher.

Feature: 008-voai-multi-role-voice-generation
T022: Implement Azure voice list fetching logic

Fetches voice list from Azure Speech Services API.
"""

import logging
import os
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


@dataclass
class AzureVoiceInfo:
    """Raw voice information from Azure API."""

    short_name: str  # e.g., "zh-TW-HsiaoChenNeural"
    display_name: str  # e.g., "HsiaoChen"
    local_name: str  # e.g., "曉臻"
    locale: str  # e.g., "zh-TW"
    gender: str  # e.g., "Female"
    voice_type: str  # e.g., "Neural"
    style_list: list[str]  # e.g., ["chat", "cheerful"]
    role_play_list: list[str]  # e.g., ["Girl", "Boy"]
    sample_rate_hertz: str | None = None
    words_per_minute: str | None = None
    secondary_locale_list: list[str] | None = None


class AzureVoiceFetcher:
    """Fetches voice list from Azure Speech Services.

    Uses the REST API to get available voices:
    GET https://{region}.tts.speech.microsoft.com/cognitiveservices/voices/list
    """

    def __init__(
        self,
        api_key: str | None = None,
        region: str | None = None,
    ):
        """Initialize the fetcher.

        Args:
            api_key: Azure Speech API key. Defaults to AZURE_SPEECH_KEY env var.
            region: Azure region. Defaults to AZURE_SPEECH_REGION env var.
        """
        self.api_key = api_key or os.getenv("AZURE_SPEECH_KEY", "")
        self.region = region or os.getenv("AZURE_SPEECH_REGION", "eastasia")

    @property
    def endpoint(self) -> str:
        """Get the voices list endpoint URL."""
        return f"https://{self.region}.tts.speech.microsoft.com/cognitiveservices/voices/list"

    async def fetch_voices(self, language: str | None = None) -> list[AzureVoiceInfo]:
        """Fetch available voices from Azure.

        Args:
            language: Optional language filter (e.g., "zh-TW").

        Returns:
            List of AzureVoiceInfo objects.

        Raises:
            ValueError: If API key is not configured.
            httpx.HTTPError: If API request fails.
        """
        if not self.api_key:
            raise ValueError("Azure Speech API key not configured")

        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.endpoint, headers=headers)
            response.raise_for_status()
            data = response.json()

        voices = []
        for item in data:
            # Filter by language if specified
            if language and item.get("Locale") != language:
                continue

            voice = AzureVoiceInfo(
                short_name=item.get("ShortName", ""),
                display_name=item.get("DisplayName", ""),
                local_name=item.get("LocalName", ""),
                locale=item.get("Locale", ""),
                gender=item.get("Gender", ""),
                voice_type=item.get("VoiceType", ""),
                style_list=item.get("StyleList", []) or [],
                role_play_list=item.get("RolePlayList", []) or [],
                sample_rate_hertz=item.get("SampleRateHertz"),
                words_per_minute=item.get("WordsPerMinute"),
                secondary_locale_list=item.get("SecondaryLocaleList"),
            )
            voices.append(voice)

        logger.info(f"Fetched {len(voices)} voices from Azure")
        return voices

    async def fetch_neural_voices(self, language: str | None = None) -> list[AzureVoiceInfo]:
        """Fetch only Neural voices from Azure.

        Args:
            language: Optional language filter.

        Returns:
            List of Neural voices only.
        """
        all_voices = await self.fetch_voices(language)
        return [v for v in all_voices if v.voice_type == "Neural"]

    async def fetch_chinese_voices(self) -> list[AzureVoiceInfo]:
        """Fetch Chinese voices (zh-TW and zh-CN).

        Returns:
            List of Chinese voices.
        """
        all_voices = await self.fetch_voices()
        return [v for v in all_voices if v.locale.startswith("zh-")]
