"""StoryPal WebSocket route.

Feature: StoryPal — AI Interactive Story Companion

WebSocket endpoint for real-time interactive story sessions.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Query, WebSocket

from src.infrastructure.auth.jwt import verify_access_token
from src.infrastructure.websocket.story_handler import StoryWebSocketHandler
from src.presentation.api.dependencies import get_llm_providers
from src.presentation.api.middleware.auth import APP_ENV, DEV_USER, DISABLE_AUTH

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def story_websocket(
    websocket: WebSocket,
    token: str = Query(default=""),
) -> None:
    """WebSocket endpoint for interactive story sessions.

    Protocol:
    1. Client connects with auth token
    2. Client sends story_configure message with template/language
    3. Server generates story segments and sends them as story_segment messages
    4. At decision points, server sends choice_prompt message
    5. Client sends story_choice with selected option
    6. Server continues story based on choice
    7. Client can send text_input for questions/free responses
    8. Client can send interrupt to pause/stop
    """
    # Authenticate via JWT token
    user_id: uuid.UUID | None = None

    if DISABLE_AUTH and APP_ENV != "production":
        user_id = uuid.UUID(DEV_USER.id)
    elif token:
        try:
            payload = verify_access_token(token)
            if payload:
                user_id = uuid.UUID(payload.sub)
        except Exception:
            pass

    if not user_id:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    # Get LLM providers
    llm_providers = get_llm_providers()
    if not llm_providers:
        await websocket.accept()
        await websocket.send_json(
            {
                "type": "error",
                "data": {"message": "No LLM providers configured"},
            }
        )
        await websocket.close()
        return

    # Pick default LLM (prefer openai > gemini > anthropic)
    llm_provider = None
    for name in ("openai", "gemini", "anthropic", "azure-openai"):
        if name in llm_providers:
            llm_provider = llm_providers[name]
            break

    if not llm_provider:
        llm_provider = next(iter(llm_providers.values()))

    handler = StoryWebSocketHandler(
        websocket=websocket,
        user_id=user_id,
        llm_provider=llm_provider,
    )

    await handler.handle()
