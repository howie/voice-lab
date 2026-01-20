"""End Session Use Case.

Feature: 004-interaction-module
T030: End an interaction session and cleanup resources.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from src.domain.entities import InteractionSession, SessionStatus
from src.domain.repositories.interaction_repository import InteractionRepository
from src.domain.services.interaction.base import InteractionModeService


@dataclass
class EndSessionInput:
    """Input for end session use case."""

    session_id: UUID
    reason: str = "user_disconnect"  # "user_disconnect", "error", "timeout"


@dataclass
class EndSessionOutput:
    """Output from end session use case."""

    session: InteractionSession | None = None
    disconnected: bool = False
    total_turns: int = 0
    error: str | None = None


class EndSessionUseCase:
    """Use case for ending an interaction session.

    This use case orchestrates:
    1. Disconnecting from the mode service
    2. Updating session status in the repository
    3. Calculating session statistics
    """

    def __init__(
        self,
        repository: InteractionRepository,
    ):
        """Initialize use case with dependencies.

        Args:
            repository: Repository for persisting sessions
        """
        self._repository = repository

    async def execute(
        self,
        input_data: EndSessionInput,
        service: InteractionModeService | None = None,
    ) -> EndSessionOutput:
        """Execute the end session use case.

        Args:
            input_data: Use case input with session ID
            service: The active mode service to disconnect (optional)

        Returns:
            Use case output with final session state
        """
        # Get session
        session = await self._repository.get_session(input_data.session_id)
        if not session:
            return EndSessionOutput(
                session=None,
                disconnected=False,
                error=f"Session not found: {input_data.session_id}",
            )

        # Disconnect service if provided
        disconnected = False
        if service and service.is_connected():
            try:
                await service.disconnect()
                disconnected = True
            except Exception:
                # Log but don't fail the use case
                pass

        # Determine final status
        if input_data.reason == "error":
            final_status = SessionStatus.ERROR
        elif input_data.reason == "timeout":
            final_status = SessionStatus.DISCONNECTED
        else:
            final_status = SessionStatus.COMPLETED

        # Update session
        session.status = final_status
        session.ended_at = datetime.now(UTC)
        session = await self._repository.update_session(session)

        # Get turn count
        turns = await self._repository.list_turns(input_data.session_id)
        total_turns = len(turns)

        return EndSessionOutput(
            session=session,
            disconnected=disconnected,
            total_turns=total_turns,
            error=None,
        )
