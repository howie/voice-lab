"""Cascade mode service.

Feature: 004-interaction-module
T046: STT → LLM → TTS pipeline implementation.
T047: Integrate existing STT providers.
T048: Integrate existing TTS providers.
"""

import asyncio
import base64
import logging
from collections.abc import AsyncIterator
from io import BytesIO
from typing import Any
from uuid import UUID

from src.application.interfaces.llm_provider import ILLMProvider, LLMMessage
from src.application.interfaces.stt_provider import ISTTProvider
from src.application.interfaces.tts_provider import ITTSProvider
from src.domain.entities.audio import AudioData, AudioFormat
from src.domain.entities.stt import STTRequest
from src.domain.entities.tts import TTSRequest
from src.domain.services.interaction.base import (
    AudioChunk,
    InteractionModeService,
    ResponseEvent,
)


class CascadeModeService(InteractionModeService):
    """Cascade mode implementation.

    Provides voice interaction using a pipeline:
    STT (Speech-to-Text) → LLM → TTS (Text-to-Speech)

    This mode offers higher quality and more flexibility compared to
    direct V2V APIs, but with slightly higher latency.
    """

    def __init__(
        self,
        stt_provider: ISTTProvider,
        llm_provider: ILLMProvider,
        tts_provider: ITTSProvider,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize cascade service with providers.

        Args:
            stt_provider: Speech-to-text provider
            llm_provider: Large language model provider
            tts_provider: Text-to-speech provider
            logger: Optional logger
        """
        self._stt = stt_provider
        self._llm = llm_provider
        self._tts = tts_provider
        self._logger = logger or logging.getLogger(__name__)

        self._connected = False
        self._session_id: UUID | None = None
        self._system_prompt: str = ""
        self._config: dict[str, Any] = {}

        # Audio buffer for collecting user speech
        self._audio_buffer: BytesIO = BytesIO()
        self._sample_rate: int = 16000

        # Conversation history for context
        self._messages: list[LLMMessage] = []

        # Event queue for async iteration
        self._event_queue: asyncio.Queue[ResponseEvent] = asyncio.Queue()

        # TTS voice configuration
        self._tts_voice: str = ""
        self._tts_language: str = "zh-TW"

        # State tracking
        self._is_processing = False
        self._interrupted = False

    @property
    def mode_name(self) -> str:
        return "cascade"

    async def connect(
        self,
        session_id: UUID,
        config: dict[str, Any],
        system_prompt: str = "",
    ) -> None:
        """Initialize cascade pipeline.

        Args:
            session_id: Session identifier
            config: Configuration with stt_provider, llm_provider, tts_provider settings
            system_prompt: System prompt for LLM
        """
        self._session_id = session_id
        self._config = config
        self._system_prompt = system_prompt
        self._connected = True

        # Reset state
        self._audio_buffer = BytesIO()
        self._messages = []
        self._interrupted = False

        # Add system prompt to messages
        if system_prompt:
            self._messages.append(LLMMessage(role="system", content=system_prompt))

        # Extract TTS voice from config
        self._tts_voice = config.get("tts_voice", "zh-TW-HsiaoChenNeural")
        self._tts_language = config.get("language", "zh-TW")

        self._logger.info(
            f"Cascade mode connected for session {session_id} "
            f"(STT: {self._stt.name}, LLM: {self._llm.name}, TTS: {self._tts.name})"
        )

    async def disconnect(self) -> None:
        """Cleanup resources."""
        self._connected = False
        self._session_id = None
        self._audio_buffer = BytesIO()
        self._messages = []

        # Signal end of events
        await self._event_queue.put(ResponseEvent(type="disconnected", data={}))

    async def send_audio(self, audio: AudioChunk) -> None:
        """Collect audio chunks for batch STT processing.

        Args:
            audio: Audio chunk from user
        """
        if not self._connected:
            return

        # Append audio to buffer
        self._audio_buffer.write(audio.data)
        self._sample_rate = audio.sample_rate

        # Emit speech_started on first chunk
        if self._audio_buffer.tell() == len(audio.data):
            await self._emit_event("speech_started", {})

    async def end_turn(self, force: bool = False) -> None:
        """Process accumulated audio through STT → LLM → TTS pipeline.

        Args:
            force: Ignored in cascade mode (always processes).
        """
        _ = force  # Cascade mode always processes
        if not self._connected or self._is_processing:
            return

        self._is_processing = True
        self._interrupted = False

        try:
            # Emit speech ended
            await self._emit_event("speech_ended", {})

            # Get accumulated audio
            audio_data = self._audio_buffer.getvalue()
            self._audio_buffer = BytesIO()

            if not audio_data:
                self._is_processing = False
                return

            # Step 1: STT - Transcribe audio
            transcript = await self._process_stt(audio_data)
            if not transcript or self._interrupted:
                self._is_processing = False
                return

            # Emit transcript
            await self._emit_event("transcript", {"text": transcript, "is_final": True})

            # Add user message to history
            self._messages.append(LLMMessage(role="user", content=transcript))

            # Step 2: LLM - Generate response
            response_text = await self._process_llm()
            if not response_text or self._interrupted:
                self._is_processing = False
                return

            # Add assistant message to history
            self._messages.append(LLMMessage(role="assistant", content=response_text))

            # Step 3: TTS - Synthesize audio
            await self._process_tts(response_text)

            # Emit response ended
            await self._emit_event("response_ended", {"text": response_text})

        except Exception as e:
            self._logger.error(f"Cascade processing error: {e}")
            await self._emit_event("error", {"error_code": "CASCADE_ERROR", "message": str(e)})
        finally:
            self._is_processing = False

    async def interrupt(self) -> None:
        """Interrupt current response."""
        self._interrupted = True
        await self._emit_event("interrupted", {})
        self._logger.debug("Cascade response interrupted")

    async def events(self) -> AsyncIterator[ResponseEvent]:
        """Async iterator for response events."""
        while self._connected or not self._event_queue.empty():
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=0.1)
                if event.type == "disconnected":
                    break
                yield event
            except TimeoutError:
                continue

    def is_connected(self) -> bool:
        """Check connection status."""
        return self._connected

    async def _emit_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Emit an event to the queue."""
        await self._event_queue.put(ResponseEvent(type=event_type, data=data))

    async def _process_stt(self, audio_data: bytes) -> str:
        """Process audio through STT provider.

        Args:
            audio_data: Raw PCM audio data

        Returns:
            Transcribed text
        """
        self._logger.debug(f"Processing STT with {self._stt.name}")

        # Create AudioData entity
        audio = AudioData(
            data=audio_data,
            format=AudioFormat.PCM,
            sample_rate=self._sample_rate,
            channels=1,
        )

        # Create STT request
        request = STTRequest(
            provider=self._stt.name,
            language=self._tts_language,
            audio=audio,
            enable_word_timing=False,
        )

        # Transcribe
        result = await self._stt.transcribe(request)
        self._logger.debug(
            f"STT result: '{result.transcript}' (confidence: {result.confidence:.2f})"
        )

        return result.transcript

    async def _process_llm(self) -> str:
        """Process messages through LLM provider.

        Returns:
            Generated response text
        """
        self._logger.debug(f"Processing LLM with {self._llm.name}")

        # Stream text deltas
        full_response = ""
        is_first = True

        async for delta in self._llm.generate_stream(
            messages=self._messages,
            max_tokens=500,
            temperature=0.7,
        ):
            if self._interrupted:
                return ""

            full_response += delta

            # Emit text delta
            await self._emit_event(
                "text_delta",
                {"delta": delta, "accumulated": full_response, "is_first": is_first},
            )
            is_first = False

        self._logger.debug(f"LLM response: {full_response[:100]}...")
        return full_response

    async def _process_tts(self, text: str) -> None:
        """Process text through TTS provider and stream audio.

        Args:
            text: Text to synthesize
        """
        self._logger.debug(f"Processing TTS with {self._tts.name}")

        # Create TTS request
        request = TTSRequest(
            text=text,
            voice_id=self._tts_voice,
            provider=self._tts.name,
            language=self._tts_language,
            output_format=AudioFormat.PCM,
        )

        # Stream audio chunks
        is_first = True
        async for chunk in self._tts.synthesize_stream(request):
            if self._interrupted:
                return

            # Encode audio as base64 for WebSocket transport
            audio_b64 = base64.b64encode(chunk).decode("utf-8")

            await self._emit_event(
                "audio",
                {
                    "audio": audio_b64,
                    "format": "pcm16",
                    "is_first": is_first,
                    "is_final": False,
                },
            )
            is_first = False

        # Signal audio complete
        await self._emit_event(
            "audio", {"audio": "", "format": "pcm16", "is_first": False, "is_final": True}
        )
