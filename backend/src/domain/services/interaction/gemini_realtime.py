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
import time
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
# See: https://ai.google.dev/gemini-api/docs/live
AVAILABLE_MODELS = [
    "gemini-2.5-flash-native-audio-preview-12-2025",  # Latest native audio, Chinese support
    "gemini-2.0-flash-live-001",  # Gemini 2.0 Flash Live stable
    "gemini-2.0-flash-exp",  # Legacy, retiring March 2026
]

# Default configuration - use 2.0 flash live for stability
DEFAULT_MODEL = "gemini-2.0-flash-live-001"
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
        # Track accumulated transcripts to avoid duplicates
        self._accumulated_input_transcript = ""
        self._accumulated_output_transcript = ""
        self._setup_complete = False
        # Audio stats tracking
        self._reset_send_stats()
        self._reset_recv_stats()

    def _reset_send_stats(self) -> None:
        """Reset audio send statistics for a new turn."""
        self._send_chunk_count = 0
        self._send_bytes = 0

    def _reset_recv_stats(self) -> None:
        """Reset audio receive statistics for a new turn."""
        self._recv_chunk_count = 0
        self._recv_bytes = 0
        self._recv_first_chunk_time: float | None = None
        self._recv_start_time: float | None = None

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
            logger.info("Connecting to Gemini WebSocket...")
            self._ws = await websockets.connect(
                url,
                ping_interval=20,
                ping_timeout=20,
            )
            logger.info("Gemini WebSocket connected")
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
                    logger.error("Gemini setup timeout after %.1fs", elapsed)
                    raise TimeoutError("Gemini setup timeout")
                await asyncio.sleep(0.1)

            logger.info("Connected to Gemini Live API for session %s", session_id)

        except Exception as e:
            logger.error("Failed to connect to Gemini Live API: %s", e)
            self._connected = False
            raise

    async def _send_setup(
        self,
        config: dict[str, Any],
        system_prompt: str,
    ) -> None:
        """Send setup message to Gemini.

        Supports gemini-2.0-flash-live-001 and gemini-2.5-flash-native-audio-preview.
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

        # Add system instruction (use default if not provided)
        # Always prepend Chinese language instruction to ensure Gemini
        # understands both user speech and its own responses in Chinese
        chinese_language_preamble = (
            "[語言設定] 這是一個中文對話。"
            "請你全程使用繁體中文理解使用者的語音輸入，並用繁體中文回覆。"
            "即使使用者的語音被辨識為其他語言或有混合語言的情況，"
            "也請優先以繁體中文來理解和回應。\n\n"
        )
        base_prompt = (
            system_prompt
            or "你是一個親切的幼兒園老師，正在跟小朋友互動。請用溫柔、有耐心的方式說話，使用簡單易懂的詞彙。"
        )
        effective_prompt = chinese_language_preamble + base_prompt
        setup_message["setup"]["system_instruction"] = {"parts": [{"text": effective_prompt}]}

        logger.info(
            "Gemini setup: model=%s, voice=%s, prompt=%s",
            model,
            voice,
            (system_prompt[:100] + "...")
            if system_prompt and len(system_prompt) > 100
            else system_prompt or "(default)",
        )
        await self._send_message(setup_message)

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

        # Send realtime input with PCM audio
        # IMPORTANT: MIME type must include sample rate for Gemini VAD to work correctly
        # Per Gemini Live API docs: "audio/pcm;rate=16000"
        sample_rate = audio.sample_rate or 16000
        mime_type = f"audio/pcm;rate={sample_rate}"

        # Track send stats
        self._send_chunk_count += 1
        self._send_bytes += len(audio.data)

        message = {
            "realtime_input": {"media_chunks": [{"mime_type": mime_type, "data": audio_b64}]}
        }
        await self._send_message(message)

    async def send_text(self, text: str) -> None:
        """Send a text message to Gemini as user input.

        This allows sending text prompts during a V2V session, which can be used
        to interrupt the current voice conversation with a text-based instruction.
        Gemini treats this as a user turn with text content.
        """
        if not self._connected or not self._ws:
            logger.warning("Cannot send text: not connected")
            return

        message = {
            "client_content": {
                "turns": [
                    {
                        "role": "user",
                        "parts": [{"text": text}],
                    }
                ],
                "turn_complete": True,
            }
        }
        logger.info("Gemini sending text input: %s", text[:100])
        await self._send_message(message)

    async def end_turn(self) -> None:
        """Signal end of user speech.

        For Gemini Live API with realtime audio, we send an audio_stream_end
        signal to indicate the user has finished speaking.
        """
        if not self._connected or not self._ws:
            return

        # Send empty realtime_input to signal end of audio stream
        # This tells Gemini to process accumulated audio and generate response
        logger.info(
            "Gemini audio sent: %d chunks, %d bytes",
            self._send_chunk_count,
            self._send_bytes,
        )
        message = {"realtime_input": {"audio_stream_end": True}}
        self._reset_send_stats()
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
        if not self._ws:
            logger.warning("No WebSocket, exiting receive task")
            return

        try:
            async for message in self._ws:
                if isinstance(message, bytes):
                    message = message.decode()

                try:
                    event = json.loads(message)
                    await self._handle_event(event)
                except json.JSONDecodeError:
                    logger.error("Failed to decode Gemini message: %s", message[:100])

        except websockets.ConnectionClosed as e:
            logger.info("Gemini WebSocket closed: code=%s, reason=%s", e.code, e.reason)
            self._connected = False
        except Exception as e:
            logger.error("Error receiving Gemini messages: %s", e)
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
            # Gemini sends incremental transcription with duplicates, so we accumulate
            # and only send truly new content to the frontend
            if "inputTranscription" in server_content:
                text = server_content["inputTranscription"].get("text", "")
                # Check if this text is already part of accumulated transcript
                # If not, it's new content - append and send only the new part
                if text and text not in self._accumulated_input_transcript:
                    self._accumulated_input_transcript += text
                    await self._event_queue.put(
                        ResponseEvent(
                            type="transcript",
                            data={"text": text, "is_final": False},
                        )
                    )

            # Handle output transcription (AI speech -> text)
            # Same deduplication logic for AI responses
            if "outputTranscription" in server_content:
                text = server_content["outputTranscription"].get("text", "")
                # Same deduplication logic for AI responses
                if text and text not in self._accumulated_output_transcript:
                    self._accumulated_output_transcript += text
                    await self._event_queue.put(
                        ResponseEvent(
                            type="text_delta",
                            data={"delta": text},
                        )
                    )

            # Check for turn complete
            if server_content.get("turnComplete"):
                self._log_turn_summary()
                self._accumulated_input_transcript = ""
                self._accumulated_output_transcript = ""
                self._reset_recv_stats()
                await self._event_queue.put(
                    ResponseEvent(
                        type="response_ended",
                        data={"status": "complete"},
                    )
                )

            # Check for interruption
            if server_content.get("interrupted"):
                # Reset accumulated transcripts on interruption
                self._accumulated_input_transcript = ""
                self._accumulated_output_transcript = ""
                self._reset_recv_stats()
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

                for part in parts:
                    # Handle audio data
                    if "inlineData" in part:
                        inline_data = part["inlineData"]
                        mime_type = inline_data.get("mimeType", "")
                        data_b64 = inline_data.get("data", "")
                        if mime_type.startswith("audio/"):
                            # Track recv stats
                            now = time.monotonic()
                            self._recv_chunk_count += 1
                            self._recv_bytes += len(data_b64)
                            if self._recv_chunk_count == 1:
                                self._recv_start_time = now
                                self._recv_first_chunk_time = now
                                logger.info("Gemini audio recv started (%s)", mime_type)

                            await self._event_queue.put(
                                ResponseEvent(
                                    type="audio",
                                    data={
                                        "audio": data_b64,
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
            logger.info("Unhandled Gemini event: %s", list(event.keys()))

    def _log_turn_summary(self) -> None:
        """Log a concise summary of the completed turn."""
        parts = []

        # Input transcript
        if self._accumulated_input_transcript:
            parts.append(f'input="{self._accumulated_input_transcript}"')

        # Output transcript
        if self._accumulated_output_transcript:
            out = self._accumulated_output_transcript
            parts.append(f"output={len(out)} chars")

        # Recv audio stats
        if self._recv_chunk_count > 0 and self._recv_start_time is not None:
            duration = time.monotonic() - self._recv_start_time
            first_chunk_ms = (
                (self._recv_first_chunk_time - self._recv_start_time) * 1000
                if self._recv_first_chunk_time and self._recv_start_time
                else 0
            )
            parts.append(
                f"recv_audio={self._recv_chunk_count} chunks/{self._recv_bytes} bytes/"
                f"{duration:.1f}s (first_chunk: {first_chunk_ms:.0f}ms)"
            )

        logger.info("Gemini turn complete: %s", ", ".join(parts) if parts else "(empty)")
