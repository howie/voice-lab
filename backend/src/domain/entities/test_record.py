"""Test record domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class TestType(Enum):
    """Type of test performed."""

    TTS = "tts"
    STT = "stt"
    INTERACTION = "interaction"


@dataclass
class TestRecord:
    """Test record entity for tracking test history."""

    id: UUID = field(default_factory=uuid4)
    user_id: str = ""
    test_type: TestType = TestType.TTS
    provider: str = ""
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    latency_ms: int = 0
    cost_estimate: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_tts_result(cls, user_id: str, result: Any) -> "TestRecord":
        """Create test record from TTS result."""
        from src.domain.entities.tts import TTSResult

        if not isinstance(result, TTSResult):
            raise TypeError("Expected TTSResult")

        return cls(
            user_id=user_id,
            test_type=TestType.TTS,
            provider=result.provider,
            input_data={
                "text": result.request.text,
                "voice_id": result.request.voice_id,
                "language": result.request.language,
                "speed": result.request.speed,
                "pitch": result.request.pitch,
            },
            output_data={
                "duration_ms": result.duration_ms,
                "audio_size_bytes": result.audio.size_bytes,
                "format": result.audio.format.value,
            },
            latency_ms=result.latency_ms,
            cost_estimate=result.cost_estimate,
            created_at=result.created_at,
        )

    @classmethod
    def from_stt_result(cls, user_id: str, result: Any) -> "TestRecord":
        """Create test record from STT result."""
        from src.domain.entities.stt import STTResult

        if not isinstance(result, STTResult):
            raise TypeError("Expected STTResult")

        return cls(
            user_id=user_id,
            test_type=TestType.STT,
            provider=result.provider,
            input_data={
                "language": result.request.language,
                "child_mode": result.request.child_mode,
            },
            output_data={
                "transcript": result.transcript,
                "confidence": result.confidence,
                "word_count": result.word_count,
            },
            latency_ms=result.latency_ms,
            created_at=result.created_at,
        )
