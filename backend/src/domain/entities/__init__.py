"""Domain Entities - Pure business objects."""

from src.domain.entities.audio import AudioData, AudioFormat
from src.domain.entities.audio_file import AudioFile, AudioFileFormat, AudioSource

# Interaction module entities (Phase 4)
from src.domain.entities.conversation_turn import ConversationTurn
from src.domain.entities.ground_truth import GroundTruth
from src.domain.entities.interaction import InteractionRequest, InteractionResult
from src.domain.entities.interaction_enums import InteractionMode, SessionStatus
from src.domain.entities.interaction_session import InteractionSession
from src.domain.entities.latency_metrics import LatencyMetrics
from src.domain.entities.stt import STTRequest, STTResult, WordTiming
from src.domain.entities.system_prompt_template import SystemPromptTemplate
from src.domain.entities.test_record import TestRecord, TestType
from src.domain.entities.tts import TTSRequest, TTSResult
from src.domain.entities.voice import VoiceProfile
from src.domain.entities.wer_analysis import (
    AlignmentItem,
    AlignmentOperation,
    ErrorType,
    WERAnalysis,
)

__all__ = [
    "AudioFormat",
    "AudioData",
    "AudioFile",
    "AudioFileFormat",
    "AudioSource",
    "GroundTruth",
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
    "WERAnalysis",
    "ErrorType",
    "AlignmentItem",
    "AlignmentOperation",
    # Interaction module
    "ConversationTurn",
    "InteractionMode",
    "InteractionSession",
    "LatencyMetrics",
    "SessionStatus",
    "SystemPromptTemplate",
]
