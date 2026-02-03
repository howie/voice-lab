"""Base WebSocket handler abstraction.

T017: Provides common WebSocket handling patterns for interaction module.
"""

import asyncio
import contextlib
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState


class MessageType(str, Enum):
    """WebSocket message types."""

    # Client -> Server
    AUDIO_CHUNK = "audio_chunk"
    TEXT_INPUT = "text_input"
    END_TURN = "end_turn"
    INTERRUPT = "interrupt"
    CONFIG = "config"
    PING = "ping"

    # Server -> Client
    SPEECH_STARTED = "speech_started"
    SPEECH_ENDED = "speech_ended"
    TRANSCRIPT = "transcript"
    AUDIO = "audio"
    TEXT_DELTA = "text_delta"
    RESPONSE_STARTED = "response_started"
    RESPONSE_ENDED = "response_ended"
    INTERRUPTED = "interrupted"
    ERROR = "error"
    PONG = "pong"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


@dataclass
class WebSocketMessage:
    """Structured WebSocket message."""

    type: MessageType
    data: dict[str, Any] = field(default_factory=dict)
    session_id: UUID | None = None
    turn_id: UUID | None = None


class BaseWebSocketHandler(ABC):
    """Base class for WebSocket handlers.

    Provides:
    - Connection lifecycle management
    - Message serialization/deserialization
    - Error handling
    - Heartbeat support
    """

    def __init__(
        self,
        websocket: WebSocket,
        heartbeat_interval: float = 30.0,
        logger: logging.Logger | None = None,
    ) -> None:
        self._websocket = websocket
        self._heartbeat_interval = heartbeat_interval
        self._logger = logger or logging.getLogger(self.__class__.__name__)
        self._connected = False
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._message_handlers: dict[MessageType, Callable[..., Any]] = {}

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self._connected and self._websocket.client_state == WebSocketState.CONNECTED

    async def accept(self) -> None:
        """Accept the WebSocket connection."""
        await self._websocket.accept()
        self._connected = True
        self._logger.info("WebSocket connection accepted")

    async def close(self, code: int = 1000, reason: str = "Normal closure") -> None:
        """Close the WebSocket connection."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._heartbeat_task

        if self.is_connected:
            try:
                await self._websocket.close(code=code, reason=reason)
            except Exception as e:
                self._logger.warning(f"Error closing WebSocket: {e}")

        self._connected = False
        self._logger.info(f"WebSocket connection closed: {reason}")

    async def send_message(self, message: WebSocketMessage) -> None:
        """Send a structured message to the client."""
        if not self.is_connected:
            self._logger.warning("Attempted to send message on closed connection")
            return

        payload = {
            "type": message.type.value,
            "data": message.data,
        }
        if message.session_id:
            payload["session_id"] = str(message.session_id)
        if message.turn_id:
            payload["turn_id"] = str(message.turn_id)

        try:
            await self._websocket.send_json(payload)
        except Exception as e:
            self._logger.error(f"Error sending message: {e}")
            raise

    async def send_binary(self, data: bytes) -> None:
        """Send binary data to the client."""
        if not self.is_connected:
            self._logger.warning("Attempted to send binary on closed connection")
            return

        try:
            await self._websocket.send_bytes(data)
        except Exception as e:
            self._logger.error(f"Error sending binary data: {e}")
            raise

    async def send_error(
        self,
        error_code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Send an error message to the client."""
        await self.send_message(
            WebSocketMessage(
                type=MessageType.ERROR,
                data={
                    "error_code": error_code,
                    "message": message,
                    "details": details or {},
                },
            )
        )

    async def receive_message(self) -> WebSocketMessage | None:
        """Receive and parse a message from the client."""
        try:
            data = await self._websocket.receive_json()
            msg_type = MessageType(data.get("type", ""))
            return WebSocketMessage(
                type=msg_type,
                data=data.get("data", {}),
                session_id=UUID(data["session_id"]) if data.get("session_id") else None,
                turn_id=UUID(data["turn_id"]) if data.get("turn_id") else None,
            )
        except ValueError as e:
            self._logger.warning(f"Invalid message type: {e}")
            await self.send_error("INVALID_MESSAGE_TYPE", str(e))
            return None
        except Exception as e:
            self._logger.error(f"Error receiving message: {e}")
            raise

    async def receive_binary(self) -> bytes:
        """Receive binary data from the client."""
        return await self._websocket.receive_bytes()

    def register_handler(self, msg_type: MessageType, handler: Callable[..., Any]) -> None:
        """Register a handler for a specific message type."""
        self._message_handlers[msg_type] = handler

    async def handle_message(self, message: WebSocketMessage) -> None:
        """Route message to appropriate handler."""
        handler = self._message_handlers.get(message.type)
        if handler:
            await handler(message)
        else:
            self._logger.warning(f"No handler for message type: {message.type}")

    async def start_heartbeat(self) -> None:
        """Start heartbeat task to keep connection alive."""
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    async def _heartbeat_loop(self) -> None:
        """Periodically send pong to keep connection alive."""
        while self.is_connected:
            try:
                await asyncio.sleep(self._heartbeat_interval)
                if self.is_connected:
                    await self.send_message(WebSocketMessage(type=MessageType.PONG))
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._logger.error(f"Heartbeat error: {e}")
                break

    @abstractmethod
    async def on_connect(self) -> None:
        """Called when connection is established. Override in subclass."""
        ...

    @abstractmethod
    async def on_disconnect(self) -> None:
        """Called when connection is closed. Override in subclass."""
        ...

    @abstractmethod
    async def run(self) -> None:
        """Main handler loop. Override in subclass."""
        ...

    async def handle(self) -> None:
        """Main entry point for handling WebSocket connection."""
        try:
            await self.accept()
            await self.on_connect()
            await self.run()
        except WebSocketDisconnect:
            self._logger.info("Client disconnected")
        except Exception as e:
            self._logger.error(f"WebSocket error: {e}")
            await self.send_error("INTERNAL_ERROR", str(e))
        finally:
            await self.on_disconnect()
            await self.close()
