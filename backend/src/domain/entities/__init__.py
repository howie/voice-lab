"""Domain Entities - Pure business objects."""

from src.domain.entities.audio import AudioFormat, AudioData
from src.domain.entities.tts import TTSRequest, TTSResult
from src.domain.entities.stt import STTRequest, STTResult, WordTiming
from src.domain.entities.interaction import InteractionRequest, InteractionResult
from src.domain.entities.voice import VoiceProfile
from src.domain.entities.test_record import TestRecord, TestType

__all__ = [
    "AudioFormat",
    "AudioData",
    "TTSRequest",
    "TTSResult",
    "STTRequest",
    "STTResult",
    "WordTiming",
    "InteractionRequest",
    "InteractionResult",
    "VoiceProfile",
    "TestRecord",
    "TestType",
]
