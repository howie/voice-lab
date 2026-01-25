"""ElevenLabs Voice Fetcher.

Feature: 008-voai-multi-role-voice-generation
T023: Implement ElevenLabs voice list fetching logic

Fetches voice list from ElevenLabs API.
"""

import logging
import os
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ElevenLabsVoiceLabels:
    """Voice labels from ElevenLabs API."""

    accent: str | None = None
    description: str | None = None
    age: str | None = None  # "young", "middle aged", "old"
    gender: str | None = None
    use_case: str | None = None


@dataclass
class ElevenLabsVoiceInfo:
    """Raw voice information from ElevenLabs API."""

    voice_id: str
    name: str
    category: str | None = None  # "premade", "cloned", "generated"
    description: str | None = None
    preview_url: str | None = None
    labels: ElevenLabsVoiceLabels = field(default_factory=ElevenLabsVoiceLabels)
    available_for_tiers: list[str] = field(default_factory=list)
    high_quality_base_model_ids: list[str] = field(default_factory=list)


class ElevenLabsVoiceFetcher:
    """Fetches voice list from ElevenLabs API.

    Uses the REST API to get available voices:
    GET https://api.elevenlabs.io/v1/voices
    """

    API_BASE = "https://api.elevenlabs.io/v1"

    def __init__(self, api_key: str | None = None):
        """Initialize the fetcher.

        Args:
            api_key: ElevenLabs API key. Defaults to ELEVENLABS_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY", "")

    @property
    def voices_endpoint(self) -> str:
        """Get the voices list endpoint URL."""
        return f"{self.API_BASE}/voices"

    async def fetch_voices(self, show_legacy: bool = False) -> list[ElevenLabsVoiceInfo]:
        """Fetch available voices from ElevenLabs.

        Args:
            show_legacy: Whether to include legacy voices.

        Returns:
            List of ElevenLabsVoiceInfo objects.

        Raises:
            ValueError: If API key is not configured.
            httpx.HTTPError: If API request fails.
        """
        if not self.api_key:
            raise ValueError("ElevenLabs API key not configured")

        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        params = {}
        if show_legacy:
            params["show_legacy"] = "true"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.voices_endpoint, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

        voices = []
        for item in data.get("voices", []):
            labels_data = item.get("labels", {}) or {}
            labels = ElevenLabsVoiceLabels(
                accent=labels_data.get("accent"),
                description=labels_data.get("description"),
                age=labels_data.get("age"),
                gender=labels_data.get("gender"),
                use_case=labels_data.get("use_case"),
            )

            voice = ElevenLabsVoiceInfo(
                voice_id=item.get("voice_id", ""),
                name=item.get("name", ""),
                category=item.get("category"),
                description=item.get("description"),
                preview_url=item.get("preview_url"),
                labels=labels,
                available_for_tiers=item.get("available_for_tiers", []) or [],
                high_quality_base_model_ids=item.get("high_quality_base_model_ids", []) or [],
            )
            voices.append(voice)

        logger.info(f"Fetched {len(voices)} voices from ElevenLabs")
        return voices

    async def fetch_premade_voices(self) -> list[ElevenLabsVoiceInfo]:
        """Fetch only premade voices from ElevenLabs.

        Returns:
            List of premade voices only.
        """
        all_voices = await self.fetch_voices()
        return [v for v in all_voices if v.category == "premade"]

    async def fetch_voice_by_id(self, voice_id: str) -> ElevenLabsVoiceInfo | None:
        """Fetch a specific voice by ID.

        Args:
            voice_id: The voice ID to fetch.

        Returns:
            ElevenLabsVoiceInfo if found, None otherwise.
        """
        if not self.api_key:
            raise ValueError("ElevenLabs API key not configured")

        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.voices_endpoint}/{voice_id}", headers=headers)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            item = response.json()

        labels_data = item.get("labels", {}) or {}
        labels = ElevenLabsVoiceLabels(
            accent=labels_data.get("accent"),
            description=labels_data.get("description"),
            age=labels_data.get("age"),
            gender=labels_data.get("gender"),
            use_case=labels_data.get("use_case"),
        )

        return ElevenLabsVoiceInfo(
            voice_id=item.get("voice_id", ""),
            name=item.get("name", ""),
            category=item.get("category"),
            description=item.get("description"),
            preview_url=item.get("preview_url"),
            labels=labels,
            available_for_tiers=item.get("available_for_tiers", []) or [],
            high_quality_base_model_ids=item.get("high_quality_base_model_ids", []) or [],
        )
