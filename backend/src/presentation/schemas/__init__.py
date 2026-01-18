"""API Schemas - Pydantic models for request/response validation."""

from src.presentation.schemas.compare import (
    STTCompareRequest,
    STTCompareResponse,
    TTSCompareRequest,
    TTSCompareResponse,
)
from src.presentation.schemas.history import (
    StatisticsResponse,
    TestRecordListResponse,
    TestRecordResponse,
)
from src.presentation.schemas.interaction import (
    InteractionRequest,
    InteractionResponse,
)
from src.presentation.schemas.stt import (
    STTTranscribeRequest,
    STTTranscribeResponse,
)
from src.presentation.schemas.tts import (
    TTSSynthesizeRequest,
    TTSSynthesizeResponse,
    VoiceListResponse,
    VoiceResponse,
)

__all__ = [
    # TTS
    "TTSSynthesizeRequest",
    "TTSSynthesizeResponse",
    "VoiceListResponse",
    "VoiceResponse",
    # STT
    "STTTranscribeRequest",
    "STTTranscribeResponse",
    # Interaction
    "InteractionRequest",
    "InteractionResponse",
    # Compare
    "TTSCompareRequest",
    "TTSCompareResponse",
    "STTCompareRequest",
    "STTCompareResponse",
    # History
    "TestRecordResponse",
    "TestRecordListResponse",
    "StatisticsResponse",
]
