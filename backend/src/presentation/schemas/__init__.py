"""API Schemas - Pydantic models for request/response validation."""

from src.presentation.schemas.tts import (
    TTSSynthesizeRequest,
    TTSSynthesizeResponse,
    VoiceListResponse,
    VoiceResponse,
)
from src.presentation.schemas.stt import (
    STTTranscribeRequest,
    STTTranscribeResponse,
)
from src.presentation.schemas.interaction import (
    InteractionRequest,
    InteractionResponse,
)
from src.presentation.schemas.compare import (
    TTSCompareRequest,
    TTSCompareResponse,
    STTCompareRequest,
    STTCompareResponse,
)
from src.presentation.schemas.history import (
    TestRecordResponse,
    TestRecordListResponse,
    StatisticsResponse,
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
