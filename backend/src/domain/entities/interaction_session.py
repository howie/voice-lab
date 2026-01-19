"""InteractionSession entity.

T008: Represents a complete voice interaction session.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from .interaction_enums import InteractionMode, SessionStatus


@dataclass
class InteractionSession:
    """Represents a complete voice interaction session."""

    user_id: UUID
    mode: InteractionMode
    provider_config: dict[str, Any]
    started_at: datetime
    id: UUID = field(default_factory=uuid4)
    system_prompt: str = ""
    ended_at: datetime | None = None
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def end(self, status: SessionStatus = SessionStatus.COMPLETED) -> None:
        """End the session with given status."""
        self.ended_at = datetime.utcnow()
        self.status = status
        self.updated_at = datetime.utcnow()

    def is_active(self) -> bool:
        """Check if session is still active."""
        return self.status == SessionStatus.ACTIVE

    def validate_provider_config(self) -> bool:
        """Validate that provider_config matches the mode."""
        if self.mode == InteractionMode.REALTIME:
            return "realtime_provider" in self.provider_config
        elif self.mode == InteractionMode.CASCADE:
            required_keys = ["stt_provider", "llm_provider", "tts_provider"]
            return all(key in self.provider_config for key in required_keys)
        return False
