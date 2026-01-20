"""ConversationTurn entity.

T009: Represents a single turn in a conversation (user speech + AI response).
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class ConversationTurn:
    """Represents a single conversation turn (user input + AI response)."""

    session_id: UUID
    turn_number: int
    started_at: datetime
    id: UUID = field(default_factory=uuid4)
    user_audio_path: str | None = None
    user_transcript: str | None = None
    ai_response_text: str | None = None
    ai_audio_path: str | None = None
    interrupted: bool = False
    ended_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def end(self, interrupted: bool = False) -> None:
        """Mark the turn as ended."""
        self.ended_at = datetime.utcnow()
        self.interrupted = interrupted

    def set_user_input(self, transcript: str, audio_path: str | None = None) -> None:
        """Set user input data."""
        self.user_transcript = transcript
        self.user_audio_path = audio_path

    def set_ai_response(self, text: str, audio_path: str | None = None) -> None:
        """Set AI response data."""
        self.ai_response_text = text
        self.ai_audio_path = audio_path

    def duration_ms(self) -> int | None:
        """Calculate turn duration in milliseconds."""
        if self.ended_at is None:
            return None
        delta = self.ended_at - self.started_at
        return int(delta.total_seconds() * 1000)
