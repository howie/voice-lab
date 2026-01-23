"""Voice Fetchers for TTS Providers.

Feature: 008-voai-multi-role-voice-generation
T022-T023: Implement voice list fetching from providers
"""

from src.infrastructure.providers.tts.voice_fetchers.azure_voice_fetcher import (
    AzureVoiceFetcher,
)
from src.infrastructure.providers.tts.voice_fetchers.elevenlabs_voice_fetcher import (
    ElevenLabsVoiceFetcher,
)

__all__ = [
    "AzureVoiceFetcher",
    "ElevenLabsVoiceFetcher",
]
