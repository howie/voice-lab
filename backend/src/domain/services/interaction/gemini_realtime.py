"""Google Gemini Live API client implementation.

Feature: 004-interaction-module
T027c: Gemini Live API client for V2V voice interaction.

Implements voice-to-voice interaction using Google's Gemini Live API.
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

# Gemini Live API endpoint
GEMINI_LIVE_URL = "wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent"

# Available models for Gemini Live API (must support bidiGenerateContent)
# See: https://ai.google.dev/gemini-api/docs/models
AVAILABLE_MODELS = [
    "gemini-2.5-flash-native-audio-preview-09-2025",  # Native audio with Chinese support
    "gemini-2.0-flash-exp",  # Legacy, English only
]

# Default configuration - use 2.5 for multilingual support
DEFAULT_MODEL = "gemini-2.5-flash-native-audio-preview-09-2025"
DEFAULT_VOICE = "Kore"  # Female voice, good for Chinese


class GeminiRealtimeService(InteractionModeService):
    """Google Gemini Live API implementation.

    Provides voice-to-voice interaction using Gemini's Live API.

    The service manages:
    - WebSocket connection to Gemini
    - Audio streaming (input and output)
    - Turn management
    - Response generation and interruption
    """

    def __init__(self, api_key: str) -> None:
        """Initialize the service.

        Args:
            api_key: Google AI API key
        """
        self._api_key = api_key
        self._ws: ClientConnection | None = None
        self._session_id: UUID | None = None
        self._connected = False
        self._event_queue: asyncio.Queue[ResponseEvent] = asyncio.Queue()
        self._receive_task: asyncio.Task[None] | None = None
        self._config: dict[str, Any] = {}
        self._system_prompt = ""
        self._setup_complete = False

    @property
    def mode_name(self) -> str:
        return "realtime"

    async def connect(
        self,
        session_id: UUID,
        config: dict[str, Any],
        system_prompt: str = "",
    ) -> None:
        """Connect to Gemini Live API.

        Args:
            session_id: Unique session identifier
            config: Provider configuration (model, voice, etc.)
            system_prompt: System instructions for the AI
        """
        self._session_id = session_id
        self._config = config
        self._system_prompt = system_prompt

        # Build WebSocket URL with API key
        url = f"{GEMINI_LIVE_URL}?key={self._api_key}"

        try:
            print("[Gemini] Connecting to WebSocket...")
            self._ws = await websockets.connect(
                url,
                ping_interval=20,
                ping_timeout=20,
            )
            print("[Gemini] WebSocket connected!")
            self._connected = True

            # Start receiving messages
            self._receive_task = asyncio.create_task(self._receive_messages())

            # Send setup message
            await self._send_setup(config, system_prompt)

            # Wait for setup complete
            timeout = 10.0
            start_time = asyncio.get_event_loop().time()
            while not self._setup_complete:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout:
                    print(f"[Gemini] Setup timeout after {elapsed:.1f}s")
                    raise TimeoutError("Gemini setup timeout")
                await asyncio.sleep(0.1)

            print("[Gemini] Setup complete!")
            logger.info(f"Connected to Gemini Live API for session {session_id}")

        except Exception as e:
            logger.error(f"Failed to connect to Gemini Live API: {e}")
            self._connected = False
            raise

    async def _send_setup(
        self,
        config: dict[str, Any],
        system_prompt: str,
    ) -> None:
        """Send setup message to Gemini.

        Supports both gemini-2.0-flash-exp and gemini-2.5-flash-preview-native-audio-dialog.
        The 2.5 model provides native audio with 30 HD voices in 24 languages.
        """
        # Get model from config, fallback to settings, then default
        model = config.get("model")
        if not model:
            try:
                from src.config import get_settings

                settings = get_settings()
                model = settings.gemini_live_model
            except Exception:
                model = DEFAULT_MODEL

        voice = config.get("voice", DEFAULT_VOICE)

        # Note: Native audio models auto-detect language from conversation context
        # Language is controlled via system_prompt instead of language_code parameter
        # The Google AI API (ai.google.dev) doesn't support cmn-Hant-TW for native audio
        setup_message: dict[str, Any] = {
            "setup": {
                "model": f"models/{model}",
                "generation_config": {
                    "speech_config": {
                        "voice_config": {"prebuilt_voice_config": {"voice_name": voice}}
                    },
                    "response_modalities": ["AUDIO"],
                    # Disable thinking for faster response (no internal reasoning delay)
                    "thinking_config": {"thinking_budget": 0},
                },
                # Enable transcription for both input (user) and output (AI)
                "input_audio_transcription": {},
                "output_audio_transcription": {},
            }
        }

        # Add system instruction if provided
        if system_prompt:
            setup_message["setup"]["system_instruction"] = {"parts": [{"text": system_prompt}]}

        print(f"[Gemini] System prompt: {system_prompt[:200] if system_prompt else 'None'}...")

        print(f"[Gemini] Sending setup: model={model}, voice={voice}")
        logger.info(f"Connecting to Gemini with model: {model}, voice: {voice}")
        await self._send_message(setup_message)
        print("[Gemini] Setup message sent")

    async def disconnect(self) -> None:
        """Disconnect from the API and cleanup resources."""
        self._connected = False
        self._setup_complete = False

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
        logger.info("Disconnected from Gemini Live API")

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

        # Send realtime input
        message = {
            "realtime_input": {"media_chunks": [{"mime_type": "audio/pcm", "data": audio_b64}]}
        }
        await self._send_message(message)

    async def end_turn(self) -> None:
        """Signal end of user speech.

        Gemini uses turn-based conversation, so we send an end-of-turn signal.
        """
        if not self._connected or not self._ws:
            return

        # Send client content with turn complete
        message = {"client_content": {"turns": [], "turn_complete": True}}
        await self._send_message(message)

    async def interrupt(self) -> None:
        """Interrupt the current AI response.

        Gemini handles interruption through client content.
        """
        if not self._connected or not self._ws:
            return

        # Send empty client content to signal interruption
        message = {"client_content": {"turns": [], "turn_complete": True}}
        await self._send_message(message)
        logger.debug("Sent interrupt signal to Gemini")

    async def events(self) -> AsyncIterator[ResponseEvent]:
        """Async iterator for response events from Gemini.

        Yields ResponseEvent objects as they are received from the API.

        Note: Uses pure async wait without timeout to minimize latency.
        The loop exits when disconnected or cancelled.
        """
        while self._connected:
            try:
                # Use pure async wait without timeout for minimal latency
                event = await self._event_queue.get()
                yield event
            except asyncio.CancelledError:
                break

    def is_connected(self) -> bool:
        """Check if the service is connected."""
        return self._connected and self._ws is not None and self._setup_complete

    async def _send_message(self, message: dict[str, Any]) -> None:
        """Send a JSON message to the WebSocket."""
        if self._ws:
            await self._ws.send(json.dumps(message))

    async def _receive_messages(self) -> None:
        """Background task to receive and process messages from Gemini."""
        print("[Gemini] _receive_messages task started")
        if not self._ws:
            print("[Gemini] No WebSocket, exiting receive task")
            return

        try:
            async for message in self._ws:
                if isinstance(message, bytes):
                    message = message.decode()

                # Log all incoming messages for debugging
                print(f"[Gemini] Message received: {message[:300]}")
                logger.info(f"Gemini message received: {message[:500]}")

                try:
                    event = json.loads(message)
                    await self._handle_event(event)
                except json.JSONDecodeError:
                    print(f"[Gemini] Failed to decode: {message[:100]}")
                    logger.error(f"Failed to decode message: {message[:100]}")

        except websockets.ConnectionClosed as e:
            print(f"[Gemini] WebSocket closed: {e}")
            logger.info("WebSocket connection closed")
            self._connected = False
        except Exception as e:
            print(f"[Gemini] Error in receive: {e}")
            logger.error(f"Error receiving messages: {e}")
            self._connected = False

    async def _handle_event(self, event: dict[str, Any]) -> None:
        """Handle an event received from Gemini.

        Maps Gemini events to our ResponseEvent format.
        """
        # Setup complete event
        if "setupComplete" in event:
            self._setup_complete = True
            await self._event_queue.put(
                ResponseEvent(
                    type="connected",
                    data={"status": "setup_complete"},
                )
            )

        # Server content event (contains audio, text, transcription, or turn completion)
        elif "serverContent" in event:
            server_content = event["serverContent"]

            # Handle input transcription (user speech -> text)
            if "inputTranscription" in server_content:
                text = server_content["inputTranscription"].get("text", "")
                if text:
                    await self._event_queue.put(
                        ResponseEvent(
                            type="transcript",
                            data={"text": text, "is_final": False},
                        )
                    )

            # Handle output transcription (AI speech -> text)
            if "outputTranscription" in server_content:
                text = server_content["outputTranscription"].get("text", "")
                if text:
                    await self._event_queue.put(
                        ResponseEvent(
                            type="text_delta",
                            data={"delta": text},
                        )
                    )

            # Check for turn complete
            if server_content.get("turnComplete"):
                await self._event_queue.put(
                    ResponseEvent(
                        type="response_ended",
                        data={"status": "complete"},
                    )
                )

            # Check for interruption
            if server_content.get("interrupted"):
                await self._event_queue.put(
                    ResponseEvent(
                        type="interrupted",
                        data={"status": "interrupted"},
                    )
                )

            # Process model turn (audio/text content)
            if "modelTurn" in server_content:
                model_turn = server_content["modelTurn"]
                parts = model_turn.get("parts", [])
                print(f"[Gemini] modelTurn received with {len(parts)} parts")

                for part in parts:
                    # Handle audio data
                    if "inlineData" in part:
                        inline_data = part["inlineData"]
                        mime_type = inline_data.get("mimeType", "")
                        data_length = len(inline_data.get("data", ""))
                        print(
                            f"[Gemini] inlineData: mimeType={mime_type}, data_length={data_length}"
                        )
                        if mime_type.startswith("audio/"):
                            await self._event_queue.put(
                                ResponseEvent(
                                    type="audio",
                                    data={
                                        "audio": inline_data.get("data", ""),
                                        "format": "pcm16",
                                    },
                                )
                            )

                    # Handle text data
                    elif "text" in part:
                        await self._event_queue.put(
                            ResponseEvent(
                                type="text_delta",
                                data={"text": part["text"]},
                            )
                        )

        # Input transcription event (user speech -> text)
        elif "inputTranscription" in event:
            transcription = event["inputTranscription"]
            text = transcription.get("text", "")
            is_final = transcription.get("isFinal", True)
            if text:
                await self._event_queue.put(
                    ResponseEvent(
                        type="transcript",
                        data={
                            "text": text,
                            "is_final": is_final,
                        },
                    )
                )

        # Tool call event
        elif "toolCall" in event:
            tool_call = event["toolCall"]
            await self._event_queue.put(
                ResponseEvent(
                    type="tool_call",
                    data={
                        "function_calls": tool_call.get("functionCalls", []),
                    },
                )
            )

        # Tool call cancellation
        elif "toolCallCancellation" in event:
            await self._event_queue.put(
                ResponseEvent(
                    type="tool_call_cancelled",
                    data={"ids": event["toolCallCancellation"].get("ids", [])},
                )
            )

        else:
            # Log all unhandled events for debugging
            logger.info(f"Unhandled Gemini event: {list(event.keys())}, data: {str(event)[:500]}")
