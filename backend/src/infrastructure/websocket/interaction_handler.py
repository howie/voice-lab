"""WebSocket handler for voice interaction sessions.

T018: Implements the full interaction protocol for realtime voice conversations.
"""

import asyncio
import base64
import contextlib
import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import WebSocket

from src.domain.entities import (
    ConversationTurn,
    InteractionMode,
    InteractionSession,
    LatencyMetrics,
    SessionStatus,
)
from src.domain.repositories.interaction_repository import InteractionRepository
from src.domain.services.interaction.base import (
    AudioChunk,
    InteractionModeService,
    ResponseEvent,
)
from src.domain.services.interaction.latency_tracker import LatencyTracker
from src.infrastructure.storage.audio_storage import AudioStorageService
from src.infrastructure.websocket.base_handler import (
    BaseWebSocketHandler,
    MessageType,
    WebSocketMessage,
)


class InteractionWebSocketHandler(BaseWebSocketHandler):
    """Handles WebSocket communication for voice interaction sessions.

    Supports both Realtime API mode and Cascade mode through the
    unified InteractionModeService interface.

    Lightweight Mode:
        When lightweight_mode=True, audio storage is deferred to batch upload
        via REST API, reducing latency for realtime V2V interactions.
    """

    def __init__(
        self,
        websocket: WebSocket,
        user_id: UUID,
        mode_service: InteractionModeService,
        repository: InteractionRepository,
        audio_storage: AudioStorageService,
        logger: logging.Logger | None = None,
        lightweight_mode: bool = False,
    ) -> None:
        super().__init__(websocket, logger=logger)
        self._user_id = user_id
        self._mode_service = mode_service
        self._repository = repository
        self._audio_storage = audio_storage
        self._lightweight_mode = lightweight_mode

        self._session: InteractionSession | None = None
        self._current_turn: ConversationTurn | None = None
        self._latency_tracker = LatencyTracker()

        # US4: Role configuration for transcript display
        self._user_role: str = "使用者"
        self._ai_role: str = "AI 助理"

        # US5: Barge-in configuration
        self._barge_in_enabled: bool = True

        # Track if response_started has been sent for current turn
        self._response_started_sent: bool = False

        self._event_task: asyncio.Task[None] | None = None
        self._receive_task: asyncio.Task[None] | None = None

        # Lightweight mode: buffer audio for batch upload instead of sync storage
        self._audio_buffer: list[tuple[bytes, int]] = []  # (audio_bytes, turn_number)
        self._audio_buffer_task: asyncio.Task[None] | None = None

        # Register message handlers
        self.register_handler(MessageType.CONFIG, self._handle_config)
        self.register_handler(MessageType.AUDIO_CHUNK, self._handle_audio_chunk)
        self.register_handler(MessageType.TEXT_INPUT, self._handle_text_input)
        self.register_handler(MessageType.END_TURN, self._handle_end_turn)
        self.register_handler(MessageType.INTERRUPT, self._handle_interrupt)
        self.register_handler(MessageType.PING, self._handle_ping)

    @property
    def session_id(self) -> UUID | None:
        """Get current session ID."""
        return self._session.id if self._session else None

    async def on_connect(self) -> None:
        """Handle new connection."""
        self._logger.info(f"User {self._user_id} connected for interaction")
        await self.send_message(
            WebSocketMessage(
                type=MessageType.CONNECTED,
                data={"user_id": str(self._user_id), "mode": self._mode_service.mode_name},
            )
        )

    async def on_disconnect(self) -> None:
        """Handle disconnection - cleanup resources."""
        self._logger.info(f"User {self._user_id} disconnecting")

        # Cancel tasks
        if self._event_task:
            self._event_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._event_task

        if self._receive_task:
            self._receive_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._receive_task

        # Disconnect mode service
        if self._mode_service.is_connected():
            await self._mode_service.disconnect()

        # Update session status
        if self._session:
            self._session.end_session(SessionStatus.DISCONNECTED)
            await self._repository.update_session(self._session)

        self._latency_tracker.clear_all()

    async def run(self) -> None:
        """Main handler loop - process messages and events concurrently.

        Supports both Text (JSON) and Binary messages:
        - Text: Control messages (config, end_turn, interrupt, ping)
        - Binary: Audio data with header [4 bytes sample_rate (u32 LE)] + [PCM16 data]
        """
        await self.start_heartbeat()

        # Start event listener for mode service responses
        self._event_task = asyncio.create_task(self._process_mode_events())

        # Process incoming messages (both text and binary)
        while self.is_connected:
            try:
                # Use low-level receive to handle both text and binary
                ws_message = await self._websocket.receive()

                if ws_message["type"] == "websocket.receive":
                    if "text" in ws_message:
                        # JSON control message
                        message = await self._parse_text_message(ws_message["text"])
                        if message:
                            await self.handle_message(message)
                    elif "bytes" in ws_message:
                        # Binary audio data
                        await self._handle_binary_audio(ws_message["bytes"])
                elif ws_message["type"] == "websocket.disconnect":
                    break
            except Exception as e:
                self._logger.error(f"Error processing message: {e}")
                await self.send_error("MESSAGE_ERROR", str(e))
                break

    async def _parse_text_message(self, text: str) -> WebSocketMessage | None:
        """Parse a text message into WebSocketMessage."""
        import json

        try:
            data = json.loads(text)
            msg_type = MessageType(data.get("type", ""))
            return WebSocketMessage(
                type=msg_type,
                data=data.get("data", {}),
            )
        except ValueError as e:
            self._logger.warning(f"Invalid message type: {e}")
            await self.send_error("INVALID_MESSAGE_TYPE", str(e))
            return None
        except json.JSONDecodeError as e:
            self._logger.warning(f"Invalid JSON: {e}")
            await self.send_error("INVALID_JSON", str(e))
            return None

    async def _handle_binary_audio(self, data: bytes) -> None:
        """Handle binary audio data.

        Binary format: [4 bytes sample_rate (uint32 LE)] + [PCM16 audio data]
        This is more efficient than Base64 JSON (~33% smaller, no encode/decode overhead).
        """
        if not self._session or not self._mode_service.is_connected():
            await self.send_error("NOT_CONNECTED", "No active session")
            return

        if len(data) < 4:
            self._logger.warning("Binary audio data too short (missing header)")
            return

        # Parse header: sample_rate as uint32 little-endian
        sample_rate = int.from_bytes(data[:4], byteorder="little")
        audio_bytes = data[4:]

        if not audio_bytes:
            return

        # Create turn if needed
        if not self._current_turn:
            await self._start_new_turn()

        # Lightweight mode: skip sync storage, forward immediately
        if not self._lightweight_mode and self._current_turn:
            await self._audio_storage.append_user_audio(
                session_id=self._session.id,
                turn_number=self._current_turn.turn_number,
                audio_chunk=audio_bytes,
                format="webm",
            )

        # Send to mode service immediately (minimal latency path)
        audio_chunk = AudioChunk(
            data=audio_bytes,
            format="pcm16",
            sample_rate=sample_rate,
            is_final=False,
        )
        await self._mode_service.send_audio(audio_chunk)

    async def _handle_config(self, message: WebSocketMessage) -> None:
        """Handle session configuration message."""
        data = message.data
        config = data.get("config", {})
        system_prompt = data.get("system_prompt", "")

        # T073b [US4]: Extract role and scenario configuration
        user_role = data.get("user_role", "使用者")
        ai_role = data.get("ai_role", "AI 助理")
        scenario_context = data.get("scenario_context", "")

        # T084 [US5]: Extract barge-in configuration
        barge_in_enabled = data.get("barge_in_enabled", True)

        # Lightweight mode configuration (can be set at connection or config time)
        if "lightweight_mode" in data:
            self._lightweight_mode = data.get("lightweight_mode", False)

        # Store for use in transcript messages
        self._user_role = user_role
        self._ai_role = ai_role
        self._barge_in_enabled = barge_in_enabled

        # T073a: Generate system prompt from role/scenario if not provided
        effective_system_prompt = system_prompt
        if not effective_system_prompt and scenario_context:
            effective_system_prompt = f"你是{ai_role}。{scenario_context}"

        try:
            # Create session with role/scenario configuration
            mode = InteractionMode(self._mode_service.mode_name)
            self._session = InteractionSession(
                user_id=self._user_id,
                mode=mode,
                provider_config=config,
                started_at=datetime.now(UTC),
                system_prompt=effective_system_prompt,
                user_role=user_role,
                ai_role=ai_role,
                scenario_context=scenario_context,
            )
            self._session = await self._repository.create_session(self._session)

            # Ensure storage directory
            await self._audio_storage.ensure_session_dir(self._session.id)

            # Connect mode service
            await self._mode_service.connect(
                session_id=self._session.id,
                config=config,
                system_prompt=effective_system_prompt,
            )

            # T073b: Include role names in connected response for frontend
            await self.send_message(
                WebSocketMessage(
                    type=MessageType.CONNECTED,
                    session_id=self._session.id,
                    data={
                        "status": "session_started",
                        "session_id": str(self._session.id),
                        "user_role": user_role,
                        "ai_role": ai_role,
                    },
                )
            )
            self._logger.info(f"Session {self._session.id} started")

        except Exception as e:
            self._logger.error(f"Failed to start session: {e}")
            await self.send_error("SESSION_ERROR", f"Failed to start session: {e}")

    async def _handle_audio_chunk(self, message: WebSocketMessage) -> None:
        """Handle incoming audio chunk from client.

        In lightweight mode, audio is buffered for batch upload instead of
        being stored synchronously, reducing latency for V2V interactions.
        """
        if not self._session or not self._mode_service.is_connected():
            await self.send_error("NOT_CONNECTED", "No active session")
            return

        data = message.data
        audio_b64 = data.get("audio")
        if not audio_b64:
            return

        audio_bytes = base64.b64decode(audio_b64)
        format_str = data.get("format", "pcm16")
        sample_rate = data.get("sample_rate", 16000)
        is_final = data.get("is_final", False)

        # Create turn if needed
        if not self._current_turn:
            await self._start_new_turn()

        # Lightweight mode: skip sync storage, forward immediately to Gemini
        # Audio can be uploaded later via batch REST API
        if not self._lightweight_mode and self._current_turn:
            # Standard mode: store audio synchronously
            await self._audio_storage.append_user_audio(
                session_id=self._session.id,
                turn_number=self._current_turn.turn_number,
                audio_chunk=audio_bytes,
                format="webm",
            )

        # Send to mode service immediately (minimal latency path)
        audio_chunk = AudioChunk(
            data=audio_bytes,
            format=format_str,
            sample_rate=sample_rate,
            is_final=is_final,
        )
        await self._mode_service.send_audio(audio_chunk)

    async def _handle_text_input(self, message: WebSocketMessage) -> None:
        """Handle text input from client.

        Sends a text message to the mode service as user input, allowing
        text prompts to interrupt or supplement the voice conversation.
        Useful for sending instructions during V2V sessions.
        """
        if not self._session or not self._mode_service.is_connected():
            await self.send_error("NOT_CONNECTED", "No active session")
            return

        text = message.data.get("text", "").strip()
        if not text:
            return

        # Create turn if needed
        if not self._current_turn:
            await self._start_new_turn()

        # Record text as user input in the turn
        if self._current_turn:
            self._current_turn.set_user_input(text)
            await self._repository.update_turn(self._current_turn)

        # Send text to mode service
        await self._mode_service.send_text(text)
        self._logger.debug(f"Sent text input to mode service: {text[:100]}")

    async def _handle_end_turn(self, _message: WebSocketMessage) -> None:
        """Handle explicit end of user turn."""
        if self._mode_service.is_connected():
            await self._mode_service.end_turn()

    async def _handle_interrupt(self, _message: WebSocketMessage) -> None:
        """Handle barge-in/interrupt request.

        T084: Only process interrupt if barge_in_enabled is True.
        """
        if not self._barge_in_enabled:
            self._logger.debug("Interrupt ignored: barge_in_enabled is False")
            return

        if self._mode_service.is_connected():
            if self._current_turn:
                self._latency_tracker.mark_interrupted(self._current_turn.id)
                self._current_turn.end(interrupted=True)
            await self._mode_service.interrupt()

    async def _handle_ping(self, _message: WebSocketMessage) -> None:
        """Handle ping message."""
        await self.send_message(WebSocketMessage(type=MessageType.PONG))

    async def _start_new_turn(self) -> None:
        """Start a new conversation turn."""
        if not self._session:
            return

        # Reset response_started flag for new turn
        self._response_started_sent = False

        turn_number = await self._repository.get_next_turn_number(self._session.id)
        self._current_turn = ConversationTurn(
            session_id=self._session.id,
            turn_number=turn_number,
            started_at=datetime.utcnow(),
        )
        self._current_turn = await self._repository.create_turn(self._current_turn)
        self._latency_tracker.start_turn(self._current_turn.id)
        self._logger.debug(f"Started turn {turn_number} for session {self._session.id}")

    async def _end_current_turn(self) -> LatencyMetrics | None:
        """End the current conversation turn and save metrics.

        Returns:
            LatencyMetrics if available, None otherwise.
        """
        if not self._current_turn or not self._session:
            return None

        self._current_turn.end()
        await self._repository.update_turn(self._current_turn)

        # Calculate and save latency metrics
        if self._session.mode == InteractionMode.REALTIME:
            metrics = self._latency_tracker.get_metrics_realtime(self._current_turn.id)
        else:
            metrics = self._latency_tracker.get_metrics_cascade(self._current_turn.id)

        if metrics:
            await self._repository.create_latency_metrics(metrics)

        self._latency_tracker.clear_turn(self._current_turn.id)
        self._current_turn = None

        return metrics

    async def _process_mode_events(self) -> None:
        """Process events from the mode service."""
        try:
            async for event in self._mode_service.events():
                await self._handle_mode_event(event)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self._logger.error(f"Error processing mode events: {e}")
            await self.send_error("MODE_EVENT_ERROR", str(e))

    async def _handle_mode_event(self, event: ResponseEvent) -> None:
        """Handle a single event from the mode service."""
        event_type = event.type
        data = event.data

        if event_type == "speech_started":
            if self._current_turn:
                self._latency_tracker.mark_speech_started(self._current_turn.id)
            await self.send_message(
                WebSocketMessage(
                    type=MessageType.SPEECH_STARTED,
                    session_id=self.session_id,
                    turn_id=self._current_turn.id if self._current_turn else None,
                )
            )

        elif event_type == "speech_ended":
            if self._current_turn:
                self._latency_tracker.mark_speech_ended(self._current_turn.id)
            await self.send_message(
                WebSocketMessage(
                    type=MessageType.SPEECH_ENDED,
                    session_id=self.session_id,
                    turn_id=self._current_turn.id if self._current_turn else None,
                )
            )

        elif event_type == "transcript":
            if self._current_turn:
                self._latency_tracker.mark_stt_completed(self._current_turn.id)
                self._current_turn.set_user_input(data.get("text", ""))
                await self._repository.update_turn(self._current_turn)
            # T073b: Include role name in transcript message
            transcript_data = {**data, "role": self._user_role}
            await self.send_message(
                WebSocketMessage(
                    type=MessageType.TRANSCRIPT,
                    session_id=self.session_id,
                    turn_id=self._current_turn.id if self._current_turn else None,
                    data=transcript_data,
                )
            )

        elif event_type == "response_started":
            # Send response_started to client for latency tracking
            if not self._response_started_sent:
                self._response_started_sent = True
                await self.send_message(
                    WebSocketMessage(
                        type=MessageType.RESPONSE_STARTED,
                        session_id=self.session_id,
                        turn_id=self._current_turn.id if self._current_turn else None,
                        data=data,
                    )
                )

        elif event_type == "text_delta":
            if self._current_turn and not self._current_turn.ai_response_text:
                self._latency_tracker.mark_llm_first_token(self._current_turn.id)
            # T073b: Include role name in text_delta message
            text_delta_data = {**data, "role": self._ai_role}
            await self.send_message(
                WebSocketMessage(
                    type=MessageType.TEXT_DELTA,
                    session_id=self.session_id,
                    turn_id=self._current_turn.id if self._current_turn else None,
                    data=text_delta_data,
                )
            )

        elif event_type == "audio":
            audio_data = data.get("audio")
            is_first = data.get("is_first", False)

            if self._current_turn:
                if is_first:
                    self._latency_tracker.mark_tts_first_byte(self._current_turn.id)
                    self._latency_tracker.mark_response_started(self._current_turn.id)

                    # Send response_started if not already sent (fallback for providers like Gemini)
                    if not self._response_started_sent:
                        self._response_started_sent = True
                        await self.send_message(
                            WebSocketMessage(
                                type=MessageType.RESPONSE_STARTED,
                                session_id=self.session_id,
                                turn_id=self._current_turn.id if self._current_turn else None,
                                data={"source": "first_audio"},
                            )
                        )

                # Store AI audio
                if audio_data and self._session:
                    audio_bytes = (
                        base64.b64decode(audio_data) if isinstance(audio_data, str) else audio_data
                    )
                    await self._audio_storage.append_ai_audio(
                        session_id=self._session.id,
                        turn_number=self._current_turn.turn_number,
                        audio_chunk=audio_bytes,
                    )

            # Forward audio to client
            await self.send_message(
                WebSocketMessage(
                    type=MessageType.AUDIO,
                    session_id=self.session_id,
                    turn_id=self._current_turn.id if self._current_turn else None,
                    data=data,
                )
            )

        elif event_type == "response_ended":
            metrics: LatencyMetrics | None = None
            if self._current_turn:
                self._latency_tracker.mark_response_ended(self._current_turn.id)
                # Update turn with AI response
                ai_text = data.get("text", "")
                if ai_text:
                    self._current_turn.set_ai_response(ai_text, None)
                metrics = await self._end_current_turn()

            # T061: Include latency data in response_ended message
            # T088: Include interrupt latency if turn was interrupted
            response_data = {**data}
            if metrics:
                response_data["latency"] = {
                    "total_ms": metrics.total_latency_ms,
                    "stt_ms": metrics.stt_latency_ms,
                    "llm_ttft_ms": metrics.llm_ttft_ms,
                    "tts_ttfb_ms": metrics.tts_ttfb_ms,
                    "realtime_ms": metrics.realtime_latency_ms,
                    "interrupt_ms": metrics.interrupt_latency_ms,
                }

            await self.send_message(
                WebSocketMessage(
                    type=MessageType.RESPONSE_ENDED,
                    session_id=self.session_id,
                    data=response_data,
                )
            )

        elif event_type == "interrupted":
            await self.send_message(
                WebSocketMessage(
                    type=MessageType.INTERRUPTED,
                    session_id=self.session_id,
                    turn_id=self._current_turn.id if self._current_turn else None,
                )
            )
            await self._end_current_turn()

        elif event_type == "error":
            await self.send_error(
                data.get("error_code", "MODE_ERROR"),
                data.get("message", "Unknown error"),
                data.get("details"),
            )
