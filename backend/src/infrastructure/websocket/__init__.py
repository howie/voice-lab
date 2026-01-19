"""WebSocket infrastructure for interaction module."""

from src.infrastructure.websocket.base_handler import BaseWebSocketHandler
from src.infrastructure.websocket.interaction_handler import InteractionWebSocketHandler

__all__ = [
    "BaseWebSocketHandler",
    "InteractionWebSocketHandler",
]
