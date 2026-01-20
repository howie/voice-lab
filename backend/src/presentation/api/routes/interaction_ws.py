"""WebSocket routes for voice interaction sessions.

T019: WebSocket endpoint for real-time voice interaction.
"""

import contextlib
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.services.interaction.base import InteractionModeService
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.interaction_repository_impl import (
    SQLAlchemyInteractionRepository,
)
from src.infrastructure.storage.audio_storage import AudioStorageService
from src.infrastructure.websocket.interaction_handler import InteractionWebSocketHandler

logger = logging.getLogger(__name__)

router = APIRouter()


class InteractionModeFactory:
    """Factory for creating interaction mode services."""

    @staticmethod
    def create(mode: str, config: dict) -> InteractionModeService:
        """Create an interaction mode service based on mode type.

        Args:
            mode: 'realtime' or 'cascade'
            config: Provider configuration

        Returns:
            InteractionModeService instance

        Raises:
            ValueError: If mode is not supported
        """
        if mode == "realtime":
            # Determine provider from config
            provider = config.get("provider", "openai")
            if provider == "openai":
                from src.domain.services.interaction.realtime_mode import (
                    OpenAIRealtimeService,
                )

                return OpenAIRealtimeService()
            elif provider == "gemini":
                from src.domain.services.interaction.realtime_mode import (
                    GeminiRealtimeService,
                )

                return GeminiRealtimeService()
            else:
                raise ValueError(f"Unsupported realtime provider: {provider}")
        elif mode == "cascade":
            from src.domain.services.interaction.cascade_mode import CascadeModeService

            return CascadeModeService()
        else:
            raise ValueError(f"Unsupported interaction mode: {mode}")


@router.websocket("/ws/{mode}")
async def interaction_websocket(
    websocket: WebSocket,
    mode: str,
    user_id: UUID = Query(..., description="User ID for the session"),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """WebSocket endpoint for voice interaction sessions.

    Path Parameters:
        mode: Interaction mode ('realtime' or 'cascade')

    Query Parameters:
        user_id: UUID of the authenticated user

    Protocol:
        1. Client connects and receives 'connected' message
        2. Client sends 'config' message with provider_config and system_prompt
        3. Client sends 'audio_chunk' messages with base64 audio data
        4. Server sends events: speech_started, speech_ended, transcript, audio, text_delta, response_ended
        5. Client can send 'interrupt' to stop AI response
        6. Client can send 'end_turn' to explicitly end user turn
    """
    if mode not in ("realtime", "cascade"):
        await websocket.close(code=4000, reason="Invalid mode. Use 'realtime' or 'cascade'")
        return

    repository = SQLAlchemyInteractionRepository(db)
    audio_storage = AudioStorageService()

    # Mode service will be configured via CONFIG message
    # Use a placeholder that will be replaced
    mode_service: InteractionModeService | None = None

    try:
        await websocket.accept()

        # Wait for config message to initialize mode service
        config_data = await websocket.receive_json()
        if config_data.get("type") != "config":
            await websocket.close(code=4001, reason="First message must be 'config'")
            return

        config = config_data.get("data", {}).get("config", {})
        mode_service = InteractionModeFactory.create(mode, config)

        # Create handler with configured service
        handler = InteractionWebSocketHandler(
            websocket=websocket,
            user_id=user_id,
            mode_service=mode_service,
            repository=repository,
            audio_storage=audio_storage,
            logger=logger,
        )

        # Handler will process the config message internally
        # Re-inject the config message for proper handling
        handler._websocket = websocket

        # Run the handler (it will re-accept but that's handled)
        await handler.handle()

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from {mode} session")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        await websocket.close(code=4002, reason=str(e))
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        with contextlib.suppress(Exception):
            await websocket.close(code=4500, reason="Internal server error")
    finally:
        if mode_service and mode_service.is_connected():
            await mode_service.disconnect()
