"""API Routes - FastAPI route handlers."""

from fastapi import APIRouter

from src.presentation.api.routes import tts, stt, interaction, compare, history, health

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(tts.router, prefix="/tts", tags=["TTS"])
api_router.include_router(stt.router, prefix="/stt", tags=["STT"])
api_router.include_router(interaction.router, prefix="/interaction", tags=["Interaction"])
api_router.include_router(compare.router, prefix="/compare", tags=["Compare"])
api_router.include_router(history.router, prefix="/history", tags=["History"])

__all__ = ["api_router"]
