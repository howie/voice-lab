"""Voice Interaction Use Case."""

import time
from dataclasses import dataclass

from src.application.interfaces.stt_provider import ISTTProvider
from src.application.interfaces.tts_provider import ITTSProvider
from src.application.interfaces.llm_provider import ILLMProvider, LLMMessage
from src.domain.entities.audio import AudioData
from src.domain.entities.interaction import InteractionConfig, InteractionResult
from src.domain.entities.stt import STTRequest
from src.domain.entities.tts import TTSRequest


@dataclass
class VoiceInteractionInput:
    """Input for voice interaction use case."""

    user_audio: AudioData
    stt_provider: str
    llm_provider: str
    tts_provider: str
    voice_id: str
    system_prompt: str = ""
    conversation_history: list[dict] = None
    language: str = "zh-TW"
    max_response_tokens: int = 150
    user_id: str = ""

    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []


@dataclass
class VoiceInteractionOutput:
    """Output from voice interaction use case."""

    user_transcript: str
    ai_response_text: str
    ai_response_audio: AudioData
    stt_latency_ms: int
    llm_latency_ms: int
    tts_latency_ms: int
    total_latency_ms: int
    updated_history: list[dict]


class VoiceInteractionUseCase:
    """Use case for complete voice interaction cycle.

    This use case orchestrates the full voice interaction pipeline:
    1. STT: Transcribe user audio to text
    2. LLM: Generate AI response
    3. TTS: Synthesize AI response to audio
    """

    def __init__(
        self,
        stt_providers: dict[str, ISTTProvider],
        llm_providers: dict[str, ILLMProvider],
        tts_providers: dict[str, ITTSProvider],
    ):
        """Initialize use case with dependencies.

        Args:
            stt_providers: Dictionary of STT providers
            llm_providers: Dictionary of LLM providers
            tts_providers: Dictionary of TTS providers
        """
        self._stt_providers = stt_providers
        self._llm_providers = llm_providers
        self._tts_providers = tts_providers

    async def execute(self, input_data: VoiceInteractionInput) -> VoiceInteractionOutput:
        """Execute the voice interaction use case.

        Args:
            input_data: Use case input

        Returns:
            Use case output with interaction results

        Raises:
            ValueError: If provider not found
            ProviderError: If any provider fails
        """
        total_start = time.perf_counter()

        # 1. STT - Transcribe user audio
        stt_provider = self._stt_providers.get(input_data.stt_provider)
        if not stt_provider:
            raise ValueError(f"STT provider '{input_data.stt_provider}' not found")

        stt_start = time.perf_counter()
        stt_request = STTRequest(
            provider=input_data.stt_provider,
            audio=input_data.user_audio,
            language=input_data.language,
        )
        stt_result = await stt_provider.transcribe(stt_request)
        stt_latency = int((time.perf_counter() - stt_start) * 1000)

        user_transcript = stt_result.transcript

        # 2. LLM - Generate response
        llm_provider = self._llm_providers.get(input_data.llm_provider)
        if not llm_provider:
            raise ValueError(f"LLM provider '{input_data.llm_provider}' not found")

        # Build messages
        messages = []
        if input_data.system_prompt:
            messages.append(LLMMessage(role="system", content=input_data.system_prompt))

        for msg in input_data.conversation_history:
            messages.append(LLMMessage(role=msg["role"], content=msg["content"]))

        messages.append(LLMMessage(role="user", content=user_transcript))

        llm_start = time.perf_counter()
        llm_response = await llm_provider.generate(
            messages=messages,
            max_tokens=input_data.max_response_tokens,
        )
        llm_latency = int((time.perf_counter() - llm_start) * 1000)

        ai_text = llm_response.content

        # 3. TTS - Synthesize response
        tts_provider = self._tts_providers.get(input_data.tts_provider)
        if not tts_provider:
            raise ValueError(f"TTS provider '{input_data.tts_provider}' not found")

        tts_start = time.perf_counter()
        tts_request = TTSRequest(
            text=ai_text,
            voice_id=input_data.voice_id,
            provider=input_data.tts_provider,
            language=input_data.language,
        )
        tts_result = await tts_provider.synthesize(tts_request)
        tts_latency = int((time.perf_counter() - tts_start) * 1000)

        total_latency = int((time.perf_counter() - total_start) * 1000)

        # Update conversation history
        updated_history = input_data.conversation_history.copy()
        updated_history.append({"role": "user", "content": user_transcript})
        updated_history.append({"role": "assistant", "content": ai_text})

        return VoiceInteractionOutput(
            user_transcript=user_transcript,
            ai_response_text=ai_text,
            ai_response_audio=tts_result.audio,
            stt_latency_ms=stt_latency,
            llm_latency_ms=llm_latency,
            tts_latency_ms=tts_latency,
            total_latency_ms=total_latency,
            updated_history=updated_history,
        )
