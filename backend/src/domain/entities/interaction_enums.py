"""Enums for interaction module.

T007: InteractionMode and SessionStatus enums.
"""

from enum import Enum


class InteractionMode(str, Enum):
    """Mode of voice interaction."""

    REALTIME = "realtime"  # V2V Direct API (OpenAI Realtime, Gemini Live)
    CASCADE = "cascade"  # STT → LLM → TTS pipeline


class SessionStatus(str, Enum):
    """Status of an interaction session."""

    ACTIVE = "active"  # Session in progress
    COMPLETED = "completed"  # User ended session normally
    DISCONNECTED = "disconnected"  # WebSocket connection lost
    ERROR = "error"  # Session ended due to error
