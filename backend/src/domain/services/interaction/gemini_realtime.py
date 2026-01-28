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
from datetime import datetime
from pathlib import Path
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

# Debug file logger for Gemini messages (detailed logs for analysis)
_debug_log_path = Path("logs/gemini_debug.log")
_debug_log_path.parent.mkdir(parents=True, exist_ok=True)

# Session start time for relative timestamps
_session_start: float = 0.0


def _ts() -> str:
    """Get formatted timestamp with milliseconds relative to session start."""
    if _session_start == 0.0:
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]
    elapsed = time.time() - _session_start
    return f"+{elapsed:07.3f}s"


def _log(event: str, details: str = "") -> None:
    """Log event to console with timestamp."""
    ts = _ts()
    if details:
        print(f"[{ts}] [Gemini] {event}: {details}")
    else:
        print(f"[{ts}] [Gemini] {event}")

def _log_to_file(message: str) -> None:
    """Write debug message to file for detailed analysis."""
    timestamp = datetime.now().isoformat()
    with open(_debug_log_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


# Gemini Live API endpoint
GEMINI_LIVE_URL = "wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent"

# Available models for Gemini Live API (must support bidiGenerateContent)
# See: https://ai.google.dev/gemini-api/docs/models
# See: https://ai.google.dev/gemini-api/docs/live
# IMPORTANT: Only these models support Live API (bidiGenerateContent)
# Models like gemini-2.0-flash-exp or gemini-2.5-flash do NOT support Live API
AVAILABLE_MODELS = [
    "gemini-2.5-flash-native-audio-preview-12-2025",  # Latest native audio, Chinese support
    "gemini-2.0-flash-live-001",  # Gemini 2.0 Flash Live stable
]

# Default configuration - use 2.5 flash native audio for Chinese support
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
        # Track accumulated transcripts
        # Note: We only filter exact consecutive duplicates, not substrings
        # This avoids incorrectly filtering "No No No" or "A cat is a cat"
        self._accumulated_input_transcript = ""
        self._accumulated_output_transcript = ""
        self._last_input_chunk = ""  # For filtering exact consecutive duplicates
        self._last_output_chunk = ""  # For filtering exact consecutive duplicates
        self._setup_complete = False
        # Track first audio in response for latency measurement
        self._first_audio_sent = False

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

        # Reset session timing
        global _session_start
        _session_start = time.time()

        try:
            _log("CONNECT", "connecting to WebSocket...")
            self._ws = await websockets.connect(
                url,
                ping_interval=20,
                ping_timeout=20,
            )
            _log("CONNECT", "WebSocket connected")
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
                    _log("CONNECT", f"setup timeout after {elapsed:.1f}s")
                    raise TimeoutError("Gemini setup timeout")
                await asyncio.sleep(0.1)

            _log("CONNECT", "setup complete, ready for audio")
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
                    # "thinking_config": {"thinking_budget": 0},
                },
                # Enable transcription for both input (user) and output (AI)
                "input_audio_transcription": {},
                "output_audio_transcription": {},
            }
        }

        # Add system instruction (use default if not provided)
        effective_prompt = (
            system_prompt
            or "你是一個親切的幼兒園老師，正在跟小朋友互動。請用溫柔、有耐心的方式說話，使用簡單易懂的詞彙。"
        )
        setup_message["setup"]["system_instruction"] = {"parts": [{"text": effective_prompt}]}

        _log("SETUP", f"model={model}, voice={voice}")
        logger.info(f"Connecting to Gemini with model: {model}, voice: {voice}")
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

        # Track audio chunks sent (log first chunk and every 100 chunks)
        self._audio_chunk_count = getattr(self, "_audio_chunk_count", 0) + 1
        if self._audio_chunk_count == 1:
            _log("AUDIO_IN", f"first chunk, rate={sample_rate}Hz, size={len(audio.data)}B")
            _log_to_file(f"AUDIO_START: rate={sample_rate}, size={len(audio.data)} bytes")
        elif self._audio_chunk_count % 100 == 0:
            _log_to_file(f"AUDIO_PROGRESS: {self._audio_chunk_count} chunks sent")

        message = {
            "realtime_input": {"media_chunks": [{"mime_type": mime_type, "data": audio_b64}]}
        }
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
        chunk_count = getattr(self, "_audio_chunk_count", 0)
        # Store end_turn time for latency measurement
        self._end_turn_time = time.time()
        message = {"realtime_input": {"audio_stream_end": True}}
        _log("END_TURN", f"sent after {chunk_count} audio chunks")
        _log_to_file(f"END_TURN: after {chunk_count} chunks")
        self._audio_chunk_count = 0  # Reset counter for next turn
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

    async def trigger_greeting(self, greeting_prompt: str | None = None) -> None:
        """Trigger AI to start the conversation with a greeting.

        This sends a text-based turn to Gemini asking it to initiate the conversation.
        Useful for scenarios where the AI should greet the user first.

        Args:
            greeting_prompt: Optional custom prompt to trigger greeting.
                           If None, uses a default prompt based on the system_prompt.
        """
        if not self._connected or not self._ws:
            _log("GREETING", "cannot trigger: not connected")
            return

        # Default greeting prompt if not provided
        prompt = greeting_prompt or "請用你的角色開始這個對話，主動向用戶打招呼並開始互動。"

        _log("GREETING", f"triggering AI greeting with prompt: {prompt[:50]}...")

        # Send a text-based turn to Gemini to trigger the greeting
        # This tells Gemini to respond as if the user sent this text
        message = {
            "client_content": {
                "turns": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}],
                    }
                ],
                "turn_complete": True,
            }
        }
        await self._send_message(message)
        _log("GREETING", "greeting trigger sent")

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
            _log("ERROR", "no WebSocket, exiting receive task")
            return

        try:
            async for message in self._ws:
                if isinstance(message, bytes):
                    message = message.decode()

                # Log raw message to file only (for detailed debugging)
                _log_to_file(f"RECV: {message[:500]}...")

                try:
                    event = json.loads(message)
                    await self._handle_event(event)
                except json.JSONDecodeError:
                    _log("ERROR", f"failed to decode JSON: {message[:100]}")
                    logger.error(f"Failed to decode message: {message[:100]}")

        except websockets.ConnectionClosed as e:
            _log_to_file(f"WEBSOCKET_CLOSED: code={e.code}, reason={e.reason}")
            _log("DISCONNECT", f"WebSocket closed: code={e.code}")
            logger.info("WebSocket connection closed")
            self._connected = False
        except Exception as e:
            _log_to_file(f"ERROR: {type(e).__name__}: {e}")
            _log("ERROR", f"{type(e).__name__}: {e}")
            logger.error(f"Error receiving messages: {e}")
            self._connected = False

    async def _handle_event(self, event: dict[str, Any]) -> None:
        """Handle an event received from Gemini.

        Maps Gemini events to our ResponseEvent format.
        """
        # Setup complete event
        if "setupComplete" in event:
            self._setup_complete = True
            _log("RECV", "setupComplete")
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
            # Gemini sends delta (incremental) transcription
            # Only filter exact consecutive duplicates to avoid incorrectly
            # filtering legitimate repeated words like "No No No"
            if "inputTranscription" in server_content:
                text = server_content["inputTranscription"].get("text", "")
                _log_to_file(f"INPUT_TRANSCRIPT_RAW: '{text}'")
                # Only filter exact consecutive duplicates, not substrings
                if text and text != self._last_input_chunk:
                    self._last_input_chunk = text
                    self._accumulated_input_transcript += text
                    _log("TRANSCRIPT_USER", f"'{text}'")
                    _log_to_file(
                        f"INPUT_TRANSCRIPT_NEW: '{text}' -> total: '{self._accumulated_input_transcript}'"
                    )
                    await self._event_queue.put(
                        ResponseEvent(
                            type="transcript",
                            data={"text": text, "is_final": False},
                        )
                    )

            # Handle output transcription (AI speech -> text)
            # Same delta handling as input transcription
            if "outputTranscription" in server_content:
                text = server_content["outputTranscription"].get("text", "")
                _log_to_file(f"OUTPUT_TRANSCRIPT_RAW: '{text}'")
                # Only filter exact consecutive duplicates
                if text and text != self._last_output_chunk:
                    self._last_output_chunk = text
                    self._accumulated_output_transcript += text
                    _log("TRANSCRIPT_AI", f"'{text}'")
                    _log_to_file(f"OUTPUT_TRANSCRIPT_NEW: '{text}'")
                    await self._event_queue.put(
                        ResponseEvent(
                            type="text_delta",
                            data={"delta": text},
                        )
                    )

            # Check for turn complete
            if server_content.get("turnComplete"):
                _log("TURN_COMPLETE", f"user='{self._accumulated_input_transcript[:50]}...', ai_len={len(self._accumulated_output_transcript)}")
                _log_to_file(
                    f"TURN_COMPLETE: input='{self._accumulated_input_transcript}', output_len={len(self._accumulated_output_transcript)}"
                )
                self._accumulated_input_transcript = ""
                self._accumulated_output_transcript = ""
                self._last_input_chunk = ""
                self._last_output_chunk = ""
                self._first_audio_sent = False
                await self._event_queue.put(
                    ResponseEvent(
                        type="response_ended",
                        data={"status": "complete"},
                    )
                )

            # Check for interruption
            if server_content.get("interrupted"):
                _log("INTERRUPTED", "user barged in")
                # Reset accumulated transcripts and first audio flag on interruption
                self._accumulated_input_transcript = ""
                self._accumulated_output_transcript = ""
                self._last_input_chunk = ""
                self._last_output_chunk = ""
                self._first_audio_sent = False
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
                        # Get base64 data length (not decoded bytes)
                        data_b64 = inline_data.get("data", "")
                        data_bytes = len(data_b64) * 3 // 4  # Approximate decoded size
                        if mime_type.startswith("audio/"):
                            # Track first audio for latency measurement
                            is_first = not self._first_audio_sent
                            if is_first:
                                self._first_audio_sent = True
                                # Calculate latency from end_turn to first audio
                                end_turn_time = getattr(self, "_end_turn_time", 0)
                                if end_turn_time:
                                    latency_ms = (time.time() - end_turn_time) * 1000
                                    _log("FIRST_AUDIO", f"latency={latency_ms:.0f}ms, size={data_bytes}B")
                                else:
                                    _log("FIRST_AUDIO", f"size={data_bytes}B")
                            # Don't log every audio chunk - too noisy
                            await self._event_queue.put(
                                ResponseEvent(
                                    type="audio",
                                    data={
                                        "audio": data_b64,
                                        "format": "pcm16",
                                        "is_first": is_first,
                                    },
                                )
                            )

                    # Handle text data from modelTurn
                    # Note: In audio mode, text parts often contain internal
                    # reasoning/thinking content (e.g., "**Initiating the Story**")
                    # which should NOT be shown to users. We use outputTranscription
                    # for the actual speech transcription instead.
                    elif "text" in part:
                        text_content = part["text"]
                        # Log for debugging but don't send to frontend
                        # The actual transcription comes from outputTranscription
                        _log_to_file(f"MODEL_TEXT_PART (ignored): {text_content[:100]}...")

            # Log generation complete (but don't spam)
            if server_content.get("generationComplete"):
                _log("GENERATION_COMPLETE", "AI finished generating")

        # Input transcription event (user speech -> text)
        elif "inputTranscription" in event:
            transcription = event["inputTranscription"]
            text = transcription.get("text", "")
            is_final = transcription.get("isFinal", True)
            if text:
                _log("TRANSCRIPT_USER", f"'{text}' (final={is_final})")
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
            _log("TOOL_CALL", f"{len(tool_call.get('functionCalls', []))} functions")
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
            _log("TOOL_CANCELLED", f"ids={event['toolCallCancellation'].get('ids', [])}")
            await self._event_queue.put(
                ResponseEvent(
                    type="tool_call_cancelled",
                    data={"ids": event["toolCallCancellation"].get("ids", [])},
                )
            )

        # Usage metadata - log token counts
        elif "usageMetadata" in event:
            usage = event["usageMetadata"]
            _log("USAGE", f"prompt={usage.get('promptTokenCount', 0)}, response={usage.get('responseTokenCount', 0)}, total={usage.get('totalTokenCount', 0)}")

        else:
            # Log unhandled events (but not too verbose)
            keys = list(event.keys())
            if keys != ["serverContent"]:  # Already handled above
                _log("RECV_OTHER", f"keys={keys}")
