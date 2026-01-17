"""Provider management routes."""

import asyncio
import time
from datetime import UTC, datetime
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.presentation.api.dependencies import Container, get_container
from src.presentation.api.middleware.auth import CurrentUserDep

router = APIRouter(prefix="/providers", tags=["Providers"])


class ProviderName(str, Enum):
    """Available TTS providers."""

    AZURE = "azure"
    GCP = "gcp"
    ELEVENLABS = "elevenlabs"
    VOAI = "voai"


class ProviderStatus(str, Enum):
    """Provider status."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"


class HealthStatus(str, Enum):
    """Health check status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class SupportedParams(BaseModel):
    """Supported parameter ranges."""

    min: float
    max: float
    default: float


class ProviderInfo(BaseModel):
    """Provider information."""

    name: ProviderName
    display_name: str
    supported_formats: list[str]
    supported_languages: list[str]
    supported_params: dict[str, SupportedParams]
    status: ProviderStatus


class ProviderHealthResponse(BaseModel):
    """Provider health check response."""

    provider: ProviderName
    status: HealthStatus
    latency_ms: int | None
    checked_at: datetime


class ProvidersListResponse(BaseModel):
    """List of providers response."""

    providers: list[ProviderInfo]


# Provider configurations
PROVIDER_CONFIGS: dict[ProviderName, ProviderInfo] = {
    ProviderName.AZURE: ProviderInfo(
        name=ProviderName.AZURE,
        display_name="Azure Speech Service",
        supported_formats=["mp3", "wav", "opus", "ogg"],
        supported_languages=["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"],
        supported_params={
            "speed": SupportedParams(min=0.5, max=2.0, default=1.0),
            "pitch": SupportedParams(min=-20, max=20, default=0),
        },
        status=ProviderStatus.AVAILABLE,
    ),
    ProviderName.GCP: ProviderInfo(
        name=ProviderName.GCP,
        display_name="Google Cloud TTS",
        supported_formats=["mp3", "wav", "opus", "ogg"],
        supported_languages=["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"],
        supported_params={
            "speed": SupportedParams(min=0.25, max=4.0, default=1.0),
            "pitch": SupportedParams(min=-20, max=20, default=0),
        },
        status=ProviderStatus.AVAILABLE,
    ),
    ProviderName.ELEVENLABS: ProviderInfo(
        name=ProviderName.ELEVENLABS,
        display_name="ElevenLabs",
        supported_formats=["mp3", "pcm"],
        supported_languages=["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"],
        supported_params={
            "speed": SupportedParams(min=0.5, max=2.0, default=1.0),
        },
        status=ProviderStatus.AVAILABLE,
    ),
    ProviderName.VOAI: ProviderInfo(
        name=ProviderName.VOAI,
        display_name="VoAI 台灣語音",
        supported_formats=["mp3", "wav"],
        supported_languages=["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"],
        supported_params={
            "speed": SupportedParams(min=0.5, max=2.0, default=1.0),
        },
        status=ProviderStatus.AVAILABLE,
    ),
}


@router.get("", response_model=ProvidersListResponse)
async def list_providers(
    _current_user: CurrentUserDep,
    container: Container = Depends(get_container),
) -> ProvidersListResponse:
    """List all available TTS providers.

    Returns information about each configured provider including
    supported formats, languages, and parameter ranges.
    The status reflects actual initialization state.
    """
    # Get actually initialized providers
    tts_providers = container.get_tts_providers()
    stt_providers = container.get_stt_providers()

    # Update status based on actual initialization
    providers_list = []
    for provider_name, provider_config in PROVIDER_CONFIGS.items():
        # Create a copy of the config
        provider_info = provider_config.model_copy()

        # Check if provider is actually initialized
        provider_key = provider_name.value
        is_tts_available = provider_key in tts_providers
        is_stt_available = provider_key in stt_providers

        # Set status based on availability
        if is_tts_available or is_stt_available:
            provider_info.status = ProviderStatus.AVAILABLE
        else:
            provider_info.status = ProviderStatus.UNAVAILABLE

        providers_list.append(provider_info)

    return ProvidersListResponse(providers=providers_list)


@router.get("/{provider}/health", response_model=ProviderHealthResponse)
async def check_provider_health(
    provider: ProviderName,
    _current_user: CurrentUserDep,
) -> ProviderHealthResponse:
    """Check health status of a specific provider.

    Performs a lightweight health check to verify the provider
    is accessible and responding within acceptable latency.
    """
    if provider not in PROVIDER_CONFIGS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{provider}' not found",
        )

    # Simulate health check (in production, this would actually test the provider)
    start_time = time.time()

    # TODO: Implement actual provider health checks
    # For now, return healthy status with simulated latency
    await asyncio.sleep(0.01)  # Simulate network latency

    latency_ms = int((time.time() - start_time) * 1000)

    # Determine health based on latency
    if latency_ms < 100:
        health_status = HealthStatus.HEALTHY
    elif latency_ms < 500:
        health_status = HealthStatus.DEGRADED
    else:
        health_status = HealthStatus.UNHEALTHY

    return ProviderHealthResponse(
        provider=provider,
        status=health_status,
        latency_ms=latency_ms,
        checked_at=datetime.now(UTC),
    )
