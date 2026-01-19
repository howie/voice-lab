"""Interaction Repository Interface.

T012: Abstract repository for interaction session persistence.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from src.domain.entities import (
    ConversationTurn,
    InteractionMode,
    InteractionSession,
    LatencyMetrics,
    SessionStatus,
)


class InteractionRepository(ABC):
    """Abstract repository for interaction sessions and related entities."""

    # Session operations
    @abstractmethod
    async def create_session(self, session: InteractionSession) -> InteractionSession:
        """Create a new interaction session."""
        ...

    @abstractmethod
    async def get_session(self, session_id: UUID) -> InteractionSession | None:
        """Get session by ID."""
        ...

    @abstractmethod
    async def update_session(self, session: InteractionSession) -> InteractionSession:
        """Update an existing session."""
        ...

    @abstractmethod
    async def delete_session(self, session_id: UUID) -> bool:
        """Delete a session and all related data."""
        ...

    @abstractmethod
    async def list_sessions(
        self,
        user_id: UUID,
        mode: InteractionMode | None = None,
        status: SessionStatus | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[InteractionSession], int]:
        """List sessions with filters and pagination. Returns (sessions, total_count)."""
        ...

    # Turn operations
    @abstractmethod
    async def create_turn(self, turn: ConversationTurn) -> ConversationTurn:
        """Create a new conversation turn."""
        ...

    @abstractmethod
    async def get_turn(self, turn_id: UUID) -> ConversationTurn | None:
        """Get turn by ID."""
        ...

    @abstractmethod
    async def update_turn(self, turn: ConversationTurn) -> ConversationTurn:
        """Update an existing turn."""
        ...

    @abstractmethod
    async def list_turns(self, session_id: UUID) -> Sequence[ConversationTurn]:
        """List all turns in a session ordered by turn_number."""
        ...

    @abstractmethod
    async def get_next_turn_number(self, session_id: UUID) -> int:
        """Get the next turn number for a session."""
        ...

    # Latency operations
    @abstractmethod
    async def create_latency_metrics(self, metrics: LatencyMetrics) -> LatencyMetrics:
        """Create latency metrics for a turn."""
        ...

    @abstractmethod
    async def get_latency_metrics(self, turn_id: UUID) -> LatencyMetrics | None:
        """Get latency metrics for a turn."""
        ...

    @abstractmethod
    async def get_session_latency_stats(self, session_id: UUID) -> dict[str, float | int | None]:
        """Get aggregated latency statistics for a session.

        Returns dict with keys:
        - total_turns: int
        - avg_total_ms: float
        - min_total_ms: int
        - max_total_ms: int
        - p95_total_ms: int
        - avg_stt_ms: float | None (cascade only)
        - avg_llm_ttft_ms: float | None (cascade only)
        - avg_tts_ttfb_ms: float | None (cascade only)
        """
        ...
