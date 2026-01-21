"""API Routes - FastAPI route handlers."""

from fastapi import APIRouter

from src.presentation.api.routes import (
    auth,
    compare,
    credentials,
    health,
    history,
    interaction,
    interaction_ws,
    jobs,
    multi_role_tts,
    providers,
    stt,
    tts,
    voices,
)

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router)  # Auth routes have their own prefix
api_router.include_router(providers.router)  # Providers routes have their own prefix
api_router.include_router(voices.router)  # Voices routes have their own prefix
api_router.include_router(tts.router)
api_router.include_router(multi_role_tts.router)  # Multi-role TTS has its own prefix
api_router.include_router(stt.router, prefix="/stt", tags=["STT"])
api_router.include_router(interaction.router, prefix="/interaction", tags=["Interaction"])
api_router.include_router(
    interaction_ws.router, prefix="/interaction", tags=["Interaction WebSocket"]
)
api_router.include_router(compare.router, prefix="/compare", tags=["Compare"])
api_router.include_router(history.router, prefix="/history", tags=["History"])
api_router.include_router(credentials.providers_router)  # Providers (credential management) routes
api_router.include_router(credentials.router)  # Credentials routes have their own prefix
api_router.include_router(jobs.router)  # Jobs routes (async job management)

__all__ = ["api_router"]
