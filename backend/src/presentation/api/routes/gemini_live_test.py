"""Gemini Live API direct test endpoint.

Provides configuration for the frontend to connect directly to Gemini Live API
WebSocket, bypassing the backend proxy. Used for benchmarking raw v2v latency.
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gemini-live-test", tags=["Gemini Live Test"])


class GeminiLiveConfig(BaseModel):
    """Configuration for direct Gemini Live API connection."""

    api_key: str
    ws_url: str
    model: str
    default_voice: str
    available_models: list[str]
    available_voices: list[str]


# Available models for Gemini Live API
AVAILABLE_MODELS = [
    "gemini-2.5-flash-native-audio-preview-12-2025",
    "gemini-2.0-flash-live-001",
    "gemini-2.0-flash-exp",
]

# Available voices
AVAILABLE_VOICES = [
    "Kore",
    "Puck",
    "Charon",
    "Fenrir",
    "Aoede",
    "Leda",
    "Orus",
    "Zephyr",
]

GEMINI_LIVE_WS_URL = "wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent"


@router.get("/config", response_model=GeminiLiveConfig)
async def get_gemini_live_config() -> GeminiLiveConfig:
    """Get configuration for direct Gemini Live API connection.

    Returns the API key and WebSocket URL so the frontend can
    connect directly to Gemini without the backend proxy.
    This is for testing/benchmarking purposes only.
    """
    settings = get_settings()

    api_key = settings.google_ai_api_key
    if not api_key:
        raise HTTPException(
            status_code=404,
            detail="Google AI API key not configured. Set GOOGLE_AI_API_KEY env var.",
        )

    return GeminiLiveConfig(
        api_key=api_key,
        ws_url=GEMINI_LIVE_WS_URL,
        model=settings.gemini_live_model,
        default_voice="Kore",
        available_models=AVAILABLE_MODELS,
        available_voices=AVAILABLE_VOICES,
    )
