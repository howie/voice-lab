"""OpenAI Realtime API client implementation.

Feature: 004-interaction-module
T027: OpenAI Realtime API client for V2V voice interaction.

Implements voice-to-voice interaction using OpenAI's Realtime API
for lowest latency voice conversations.
"""

import asyncio
import base64
import contextlib
import json
import logging
from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID

import websockets
from websockets.asyncio.client import ClientConnection

from src.domain.services.interaction.base import (
    AudioChunk,
    InteractionModeService,
    ResponseEvent,
)

logger = logging.getLogger(__name__)

# OpenAI Realtime API endpoint
OPENAI_REALTIME_URL = "wss://api.openai.com/v1/realtime"

# Default configuration
DEFAULT_MODEL = "gpt-4o-realtime-preview"
DEFAULT_VOICE = "alloy"
DEFAULT_TURN_DETECTION = {
    "type": "server_vad",
    "threshold": 0.5,
    "prefix_padding_ms": 300,
    "silence_duration_ms": 500,
}


class OpenAIRealtimeService(InteractionModeService):
    """OpenAI Realtime API implementation.

    Provides voice-to-voice interaction using OpenAI's Realtime API
    for lowest latency voice conversations.

    The service manages:
    - WebSocket connection to OpenAI
    - Audio streaming (input and output)
    - Turn detection (VAD)
    - Response generation and interruption
    """

    def __init__(self, api_key: str) -> None:
        """Initialize the service.

        Args:
            api_key: OpenAI API key
        """
        self._api_key = api_key
        self._ws: ClientConnection | None = None
        self._session_id: UUID | None = None
        self._connected = False
        self._event_queue: asyncio.Queue[ResponseEvent] = asyncio.Queue()
        self._receive_task: asyncio.Task[None] | None = None
        self._config: dict[str, Any] = {}
        self._system_prompt = ""

    @property
    def mode_name(self) -> str:
        return "realtime"

    async def connect(
        self,
        session_id: UUID,
        config: dict[str, Any],
        system_prompt: str = "",
    ) -> None:
        """Connect to OpenAI Realtime API.

        Args:
            session_id: Unique session identifier
            config: Provider configuration (model, voice, etc.)
            system_prompt: System instructions for the AI
        """
        self._session_id = session_id
        self._config = config
        self._system_prompt = system_prompt

        # Build WebSocket URL with model
        model = config.get("model", DEFAULT_MODEL)
        url = f"{OPENAI_REALTIME_URL}?model={model}"

        # Connect to WebSocket
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "OpenAI-Beta": "realtime=v1",
        }

        try:
            self._ws = await websockets.connect(
                url,
                additional_headers=headers,
                ping_interval=20,
                ping_timeout=20,
            )
            self._connected = True

            # Start receiving messages
            self._receive_task = asyncio.create_task(self._receive_messages())

            # Configure session
            await self._configure_session(config, system_prompt)

            logger.info(f"Connected to OpenAI Realtime API for session {session_id}")

        except Exception as e:
            logger.error(f"Failed to connect to OpenAI Realtime API: {e}")
            self._connected = False
            raise

    async def _configure_session(
        self,
        config: dict[str, Any],
        system_prompt: str,
    ) -> None:
        """Send session configuration to OpenAI."""
        session_data: dict[str, Any] = {
            "modalities": ["text", "audio"],
            "instructions": system_prompt or "You are a helpful assistant.",
            "voice": config.get("voice", DEFAULT_VOICE),
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "input_audio_transcription": {"model": "whisper-1"},
            "turn_detection": config.get("turn_detection", DEFAULT_TURN_DETECTION),
        }

        # Add optional configuration
        if "temperature" in config:
            session_data["temperature"] = config["temperature"]
        if "max_response_output_tokens" in config:
            session_data["max_response_output_tokens"] = config["max_response_output_tokens"]

        session_config: dict[str, Any] = {
            "type": "session.update",
            "session": session_data,
        }

        await self._send_message(session_config)

    async def disconnect(self) -> None:
        """Disconnect from the API and cleanup resources."""
        self._connected = False

        # Cancel receive task
        if self._receive_task:
            self._receive_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._receive_task
            self._receive_task = None

        # Close WebSocket
        if self._ws:
            await self._ws.close()
            self._ws = None

        self._session_id = None
        logger.info("Disconnected from OpenAI Realtime API")

    async def send_audio(self, audio: AudioChunk) -> None:
        """Send audio data to the API.

        Args:
            audio: Audio chunk to stream to the API
        """
        if not self._connected or not self._ws:
            logger.warning("Cannot send audio: not connected")
            return

        # Encode audio as base64
        audio_b64 = base64.b64encode(audio.data).decode()

        # Send audio buffer append
        message = {
            "type": "input_audio_buffer.append",
            "audio": audio_b64,
        }
        await self._send_message(message)

        # If this is the final chunk, commit the buffer
        if audio.is_final:
            await self._send_message({"type": "input_audio_buffer.commit"})

    async def end_turn(self) -> None:
        """Signal end of user speech (manual turn detection)."""
        if not self._connected or not self._ws:
            return

        # Commit the audio buffer and create response
        await self._send_message({"type": "input_audio_buffer.commit"})
        await self._send_message({"type": "response.create"})

    async def interrupt(self) -> None:
        """Interrupt the current AI response (barge-in)."""
        if not self._connected or not self._ws:
            return

        await self._send_message({"type": "response.cancel"})
        logger.debug("Sent interrupt signal to OpenAI")

    async def events(self) -> AsyncIterator[ResponseEvent]:
        """Async iterator for response events from OpenAI.

        Yields ResponseEvent objects as they are received from the API.
        """
        while self._connected:
            try:
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=0.1,
                )
                yield event
            except TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    def is_connected(self) -> bool:
        """Check if the service is connected."""
        return self._connected and self._ws is not None

    async def _send_message(self, message: dict[str, Any]) -> None:
        """Send a JSON message to the WebSocket."""
        if self._ws:
            await self._ws.send(json.dumps(message))

    async def _receive_messages(self) -> None:
        """Background task to receive and process messages from OpenAI."""
        if not self._ws:
            return

        try:
            async for message in self._ws:
                if isinstance(message, bytes):
                    message = message.decode()

                try:
                    event = json.loads(message)
                    await self._handle_event(event)
                except json.JSONDecodeError:
                    logger.error(f"Failed to decode message: {message[:100]}")

        except websockets.ConnectionClosed:
            logger.info("WebSocket connection closed")
            self._connected = False
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")
            self._connected = False

    async def _handle_event(self, event: dict[str, Any]) -> None:
        """Handle an event received from OpenAI.

        Maps OpenAI events to our ResponseEvent format.
        """
        event_type = event.get("type", "")

        # Session events
        if event_type == "session.created":
            await self._event_queue.put(
                ResponseEvent(
                    type="connected",
                    data={"session_id": event.get("session", {}).get("id")},
                )
            )

        # Speech detection events
        elif event_type == "input_audio_buffer.speech_started":
            await self._event_queue.put(
                ResponseEvent(
                    type="speech_started",
                    data={
                        "audio_start_ms": event.get("audio_start_ms"),
                        "item_id": event.get("item_id"),
                    },
                )
            )

        elif event_type == "input_audio_buffer.speech_stopped":
            await self._event_queue.put(
                ResponseEvent(
                    type="speech_ended",
                    data={
                        "audio_end_ms": event.get("audio_end_ms"),
                        "item_id": event.get("item_id"),
                    },
                )
            )

        # Transcription events
        elif event_type == "conversation.item.input_audio_transcription.completed":
            await self._event_queue.put(
                ResponseEvent(
                    type="transcript",
                    data={
                        "text": event.get("transcript", ""),
                        "is_final": True,
                        "item_id": event.get("item_id"),
                    },
                )
            )

        # Response events
        elif event_type == "response.created":
            await self._event_queue.put(
                ResponseEvent(
                    type="response_started",
                    data={"response_id": event.get("response", {}).get("id")},
                )
            )

        elif event_type == "response.audio.delta":
            # Decode base64 audio
            audio_b64 = event.get("delta", "")
            await self._event_queue.put(
                ResponseEvent(
                    type="audio",
                    data={
                        "audio": audio_b64,
                        "format": "pcm16",
                        "response_id": event.get("response_id"),
                        "item_id": event.get("item_id"),
                    },
                )
            )

        elif event_type == "response.audio_transcript.delta":
            await self._event_queue.put(
                ResponseEvent(
                    type="text_delta",
                    data={
                        "text": event.get("delta", ""),
                        "response_id": event.get("response_id"),
                    },
                )
            )

        elif event_type == "response.done":
            response_data = event.get("response", {})
            status = response_data.get("status")

            # T079: Handle cancelled status as interrupted event
            if status == "cancelled":
                await self._event_queue.put(
                    ResponseEvent(
                        type="interrupted",
                        data={
                            "response_id": response_data.get("id"),
                            "reason": "cancelled",
                        },
                    )
                )
            else:
                await self._event_queue.put(
                    ResponseEvent(
                        type="response_ended",
                        data={
                            "response_id": response_data.get("id"),
                            "status": status,
                        },
                    )
                )

        # Error events
        elif event_type == "error":
            error = event.get("error", {})
            await self._event_queue.put(
                ResponseEvent(
                    type="error",
                    data={
                        "error_code": error.get("type", "UNKNOWN_ERROR"),
                        "message": error.get("message", "An error occurred"),
                        "details": error,
                    },
                )
            )

        # Rate limit events
        elif event_type == "rate_limits.updated":
            logger.debug(f"Rate limits updated: {event.get('rate_limits')}")

        else:
            logger.debug(f"Unhandled event type: {event_type}")
