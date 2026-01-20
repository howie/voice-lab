"""Process Audio Use Case.

Feature: 004-interaction-module
T029: Process audio chunk during an interaction session.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.domain.entities import ConversationTurn
from src.domain.repositories.interaction_repository import InteractionRepository
from src.domain.services.interaction.base import AudioChunk, InteractionModeService


@dataclass
class ProcessAudioInput:
    """Input for process audio use case."""

    session_id: UUID
    audio_data: bytes
    audio_format: str = "pcm16"
    sample_rate: int = 16000
    is_final: bool = False
    turn_id: UUID | None = None  # Optional: continue existing turn


@dataclass
class ProcessAudioOutput:
    """Output from process audio use case."""

    turn: ConversationTurn | None = None
    is_new_turn: bool = False
    processed: bool = False
    error: str | None = None


class ProcessAudioUseCase:
    """Use case for processing audio chunks during interaction.

    This use case orchestrates:
    1. Creating or retrieving the current conversation turn
    2. Sending audio to the mode service for processing
    3. Updating turn state in the repository

    Note: Response events from the mode service are handled
    separately through the event stream in the WebSocket handler.
    """

    def __init__(
        self,
        repository: InteractionRepository,
    ):
        """Initialize use case with dependencies.

        Args:
            repository: Repository for persisting turns
        """
        self._repository = repository

    async def execute(
        self,
        input_data: ProcessAudioInput,
        service: InteractionModeService,
        current_turn: ConversationTurn | None = None,
    ) -> ProcessAudioOutput:
        """Execute the process audio use case.

        Args:
            input_data: Use case input with audio data
            service: The active mode service to send audio to
            current_turn: Optional current turn to continue

        Returns:
            Use case output with turn information

        Raises:
            ValueError: If service is not connected
        """
        if not service.is_connected():
            return ProcessAudioOutput(
                turn=current_turn,
                is_new_turn=False,
                processed=False,
                error="Service not connected",
            )

        # Create new turn if needed
        is_new_turn = False
        if current_turn is None:
            turn_number = await self._repository.get_next_turn_number(input_data.session_id)
            current_turn = ConversationTurn(
                id=input_data.turn_id or uuid4(),
                session_id=input_data.session_id,
                turn_number=turn_number,
                started_at=datetime.now(UTC),
            )
            current_turn = await self._repository.create_turn(current_turn)
            is_new_turn = True

        # Create audio chunk
        audio_chunk = AudioChunk(
            data=input_data.audio_data,
            format=input_data.audio_format,
            sample_rate=input_data.sample_rate,
            is_final=input_data.is_final,
        )

        # Send audio to service
        try:
            await service.send_audio(audio_chunk)
            processed = True
            error = None
        except Exception as e:
            processed = False
            error = str(e)

        return ProcessAudioOutput(
            turn=current_turn,
            is_new_turn=is_new_turn,
            processed=processed,
            error=error,
        )
