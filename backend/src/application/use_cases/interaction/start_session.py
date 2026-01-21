"""Start Session Use Case.

Feature: 004-interaction-module
T028: Create and initialize a new interaction session.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from src.domain.entities import (
    InteractionMode,
    InteractionSession,
    SessionStatus,
)
from src.domain.repositories.interaction_repository import InteractionRepository
from src.domain.services.interaction.base import InteractionModeService


@dataclass
class StartSessionInput:
    """Input for start session use case."""

    user_id: UUID
    mode: InteractionMode
    provider_config: dict[str, Any]
    system_prompt: str = ""
    user_role: str = "使用者"  # US4: User role name
    ai_role: str = "AI 助理"  # US4: AI role name
    scenario_context: str = ""  # US4: Scenario context
    session_id: UUID | None = None  # Optional: provide your own session ID


@dataclass
class StartSessionOutput:
    """Output from start session use case."""

    session: InteractionSession
    service: InteractionModeService
    connected: bool = False
    error: str | None = None


class StartSessionUseCase:
    """Use case for starting a new interaction session.

    This use case orchestrates:
    1. Creating a new InteractionSession entity
    2. Persisting the session to the repository
    3. Creating the appropriate mode service (Realtime or Cascade)
    4. Connecting the service to the provider
    """

    def __init__(
        self,
        repository: InteractionRepository,
        mode_service_factory: Any,  # RealtimeModeFactory or CascadeModeFactory
    ):
        """Initialize use case with dependencies.

        Args:
            repository: Repository for persisting sessions
            mode_service_factory: Factory for creating mode services
        """
        self._repository = repository
        self._factory = mode_service_factory

    async def execute(self, input_data: StartSessionInput) -> StartSessionOutput:
        """Execute the start session use case.

        Args:
            input_data: Use case input with session configuration

        Returns:
            Use case output with session and connected service

        Raises:
            ValueError: If provider configuration is invalid
        """
        # Generate session ID if not provided
        session_id = input_data.session_id or uuid4()

        # T073a: Generate system prompt from ai_role + scenario_context if not provided
        system_prompt = input_data.system_prompt
        if not system_prompt and input_data.scenario_context:
            system_prompt = f"你是{input_data.ai_role}。{input_data.scenario_context}"

        # Create session entity
        session = InteractionSession(
            id=session_id,
            user_id=input_data.user_id,
            mode=input_data.mode,
            provider_config=input_data.provider_config,
            system_prompt=system_prompt,
            user_role=input_data.user_role,
            ai_role=input_data.ai_role,
            scenario_context=input_data.scenario_context,
            status=SessionStatus.ACTIVE,
            started_at=datetime.now(UTC),
            ended_at=None,
        )

        # Persist session
        session = await self._repository.create_session(session)

        # Create mode service
        try:
            service = self._factory.create(input_data.provider_config)
        except ValueError as e:
            # Update session status to error
            session.status = SessionStatus.ERROR
            session = await self._repository.update_session(session)
            return StartSessionOutput(
                session=session,
                service=None,  # type: ignore
                connected=False,
                error=str(e),
            )

        # Connect to provider
        try:
            await service.connect(
                session_id=session.id,
                config=input_data.provider_config,
                system_prompt=input_data.system_prompt,
            )
            connected = True
            error = None
        except Exception as e:
            # Update session status to error
            session.status = SessionStatus.ERROR
            session = await self._repository.update_session(session)
            connected = False
            error = str(e)

        return StartSessionOutput(
            session=session,
            service=service,
            connected=connected,
            error=error,
        )
