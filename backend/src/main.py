"""Voice Lab API - Main application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from src.config import get_settings
from src.presentation.api import api_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    print(f"Starting {settings.app_name} in {settings.app_env} mode...")

    # Ensure storage directory exists
    storage_path = os.getenv("LOCAL_STORAGE_PATH", "./storage")
    os.makedirs(storage_path, exist_ok=True)

    # Initialize providers on startup (lazy initialization in Container)
    from src.presentation.api.dependencies import get_container

    container = get_container()
    print(f"TTS Providers: {list(container.get_tts_providers().keys())}")
    print(f"STT Providers: {list(container.get_stt_providers().keys())}")
    print(f"LLM Providers: {list(container.get_llm_providers().keys())}")

    yield

    # Shutdown
    print(f"Shutting down {settings.app_name}...")


app = FastAPI(
    title=settings.app_name,
    description="Voice Provider Testing Platform - Compare TTS, STT, and Interaction across providers",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.api_prefix)

# Mount static files for local storage
storage_path = os.getenv("LOCAL_STORAGE_PATH", "./storage")
if os.path.exists(storage_path):
    app.mount("/files", StaticFiles(directory=storage_path), name="files")
