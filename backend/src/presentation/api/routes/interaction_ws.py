"""WebSocket routes for voice interaction sessions.

T019: WebSocket endpoint for real-time voice interaction.
"""

import contextlib
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.services.interaction.base import InteractionModeService
from src.infrastructure.persistence.credential_repository import (
    SQLAlchemyProviderCredentialRepository,
)
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.interaction_repository_impl import (
    SQLAlchemyInteractionRepository,
)
from src.infrastructure.storage.audio_storage import AudioStorageService
from src.infrastructure.websocket.interaction_handler import InteractionWebSocketHandler

logger = logging.getLogger(__name__)

router = APIRouter()

# Provider name mapping: cascade provider name -> credential provider name
_STT_CREDENTIAL_MAPPING = {
    "azure": "azure",
    "gcp": "gcp",
    "whisper": "openai",
    "speechmatics": "speechmatics",
}
_LLM_CREDENTIAL_MAPPING = {
    "openai": "openai",
    "anthropic": "anthropic",
    "gemini": "gemini",
    "azure-openai": "azure",
}
_TTS_CREDENTIAL_MAPPING = {
    "azure": "azure",
    "gcp": "gcp",
    "gemini": "gemini",
    "elevenlabs": "elevenlabs",
    "voai": "voai",
}


class InteractionModeFactory:
    """Factory for creating interaction mode services."""

    @staticmethod
    async def create(
        mode: str,
        config: dict,
        user_id: UUID | None = None,
        db: AsyncSession | None = None,
    ) -> InteractionModeService:
        """Create an interaction mode service based on mode type.

        Args:
            mode: 'realtime' or 'cascade'
            config: Provider configuration containing provider settings
            user_id: Optional user ID for credential lookup
            db: Optional database session for credential lookup

        Returns:
            InteractionModeService instance

        Raises:
            ValueError: If mode is not supported
        """
        if mode == "realtime":
            from src.domain.services.interaction.realtime_mode import RealtimeModeFactory

            return RealtimeModeFactory.create(config)
        elif mode == "cascade":
            return await InteractionModeFactory._create_cascade(config, user_id, db)
        else:
            raise ValueError(f"Unsupported interaction mode: {mode}")

    @staticmethod
    async def _create_cascade(
        config: dict,
        user_id: UUID | None = None,
        db: AsyncSession | None = None,
    ) -> InteractionModeService:
        """Create cascade mode service with user credential support."""
        from src.domain.services.interaction.cascade_mode import CascadeModeService
        from src.infrastructure.providers.llm.factory import LLMProviderFactory
        from src.infrastructure.providers.stt.factory import STTProviderFactory
        from src.infrastructure.providers.tts.factory import TTSProviderFactory

        # Get provider names from config with defaults
        stt_provider_name = config.get("stt_provider", "gcp")
        llm_provider_name = config.get("llm_provider", "gemini")
        tts_provider_name = config.get("tts_provider", "gemini")

        # Look up user credentials from DB
        user_credentials: dict[str, str] = {}
        if user_id and db:
            credential_repo = SQLAlchemyProviderCredentialRepository(db)
            credentials = await credential_repo.list_by_user(user_id)
            for cred in credentials:
                if cred.is_valid and cred.api_key:
                    user_credentials[cred.provider] = cred.api_key

        # Build credentials for each provider using the mapping
        stt_cred_provider = _STT_CREDENTIAL_MAPPING.get(stt_provider_name, stt_provider_name)
        stt_api_key = user_credentials.get(stt_cred_provider)

        llm_cred_provider = _LLM_CREDENTIAL_MAPPING.get(llm_provider_name, llm_provider_name)
        llm_api_key = user_credentials.get(llm_cred_provider)

        tts_cred_provider = _TTS_CREDENTIAL_MAPPING.get(tts_provider_name, tts_provider_name)
        tts_api_key = user_credentials.get(tts_cred_provider)

        # Create STT provider
        stt_credentials: dict = {}
        if stt_api_key:
            stt_credentials["api_key"] = stt_api_key
            if stt_provider_name == "azure":
                stt_credentials["subscription_key"] = stt_api_key
        stt_provider = STTProviderFactory.create(stt_provider_name, stt_credentials)

        # Create LLM provider
        if llm_api_key:
            llm_provider = LLMProviderFactory.create(llm_provider_name, {"api_key": llm_api_key})
        else:
            llm_provider = LLMProviderFactory.create_default(llm_provider_name)

        # Create TTS provider
        if tts_api_key:
            tts_provider = TTSProviderFactory.create_with_key(tts_provider_name, tts_api_key)
        else:
            tts_provider = TTSProviderFactory.create_default(tts_provider_name)

        return CascadeModeService(
            stt_provider=stt_provider,
            llm_provider=llm_provider,
            tts_provider=tts_provider,
        )


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
    mode_service: InteractionModeService | None = None

    try:
        # Accept connection first
        await websocket.accept()

        # Wait for config message to initialize mode service
        config_data = await websocket.receive_json()
        if config_data.get("type") != "config":
            await websocket.close(code=4001, reason="First message must be 'config'")
            return

        config = config_data.get("data", {}).get("config", {})
        system_prompt = config_data.get("data", {}).get("system_prompt", "")
        # Lightweight mode: skip sync audio storage for lower latency V2V
        lightweight_mode = config_data.get("data", {}).get("lightweight_mode", False)

        # Create mode service with user credentials from DB
        mode_service = await InteractionModeFactory.create(mode, config, user_id=user_id, db=db)

        # Create handler with configured service
        handler = InteractionWebSocketHandler(
            websocket=websocket,
            user_id=user_id,
            mode_service=mode_service,
            repository=repository,
            audio_storage=audio_storage,
            logger=logger,
            lightweight_mode=lightweight_mode,
        )

        # Mark handler as connected (already accepted)
        handler._connected = True

        # Send connected message
        await handler.on_connect()

        # Process the config message to start session
        # Pass the complete data from the client, not just extracted fields
        from src.infrastructure.websocket.base_handler import MessageType, WebSocketMessage

        config_message = WebSocketMessage(
            type=MessageType.CONFIG,
            data=config_data.get("data", {}),  # Pass ALL fields from client
        )
        await handler._handle_config(config_message)

        # Run the main handler loop
        await handler.run()

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from {mode} session")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        with contextlib.suppress(Exception):
            await websocket.close(code=4002, reason=str(e))
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        with contextlib.suppress(Exception):
            await websocket.close(code=4500, reason="Internal server error")
    finally:
        if mode_service and mode_service.is_connected():
            await mode_service.disconnect()
