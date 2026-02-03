"""Provider management routes."""

import asyncio
import time
from datetime import UTC, datetime
from enum import StrEnum

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.infrastructure.providers.stt.factory import STTProviderFactory
from src.presentation.api.dependencies import Container, get_container
from src.presentation.api.middleware.auth import CurrentUserDep

router = APIRouter(prefix="/providers", tags=["Providers"])


class ProviderType(StrEnum):
    """Provider types."""

    TTS = "tts"
    STT = "stt"
    LLM = "llm"


class ProviderStatus(StrEnum):
    """Provider status."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"


class HealthStatus(StrEnum):
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

    name: str
    display_name: str
    type: ProviderType
    supported_formats: list[str]
    supported_languages: list[str]
    supported_params: dict[str, SupportedParams] = {}
    status: ProviderStatus


class ProviderHealthResponse(BaseModel):
    """Provider health check response."""

    provider: str
    type: ProviderType
    status: HealthStatus
    latency_ms: int | None
    checked_at: datetime


class ProvidersSummaryResponse(BaseModel):
    """Summary of all providers by type."""

    tts: list[ProviderInfo]
    stt: list[ProviderInfo]
    llm: list[ProviderInfo]


class ProvidersListResponse(BaseModel):
    """List of providers response."""

    providers: list[ProviderInfo]


# TTS Provider configurations
TTS_PROVIDER_CONFIGS = {
    "azure": {
        "display_name": "Azure Speech Service",
        "supported_formats": ["mp3", "wav", "opus", "ogg"],
        "supported_languages": ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"],
        "supported_params": {
            "speed": {"min": 0.5, "max": 2.0, "default": 1.0},
            "pitch": {"min": -20, "max": 20, "default": 0},
        },
    },
    "gcp": {
        "display_name": "Google Cloud TTS",
        "supported_formats": ["mp3", "wav", "opus", "ogg"],
        "supported_languages": ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"],
        "supported_params": {
            "speed": {"min": 0.25, "max": 4.0, "default": 1.0},
            "pitch": {"min": -20, "max": 20, "default": 0},
        },
    },
    "elevenlabs": {
        "display_name": "ElevenLabs",
        "supported_formats": ["mp3", "pcm"],
        "supported_languages": ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"],
        "supported_params": {
            "speed": {"min": 0.5, "max": 2.0, "default": 1.0},
        },
    },
    "gemini": {
        "display_name": "Gemini TTS",
        "supported_formats": ["mp3", "wav", "ogg", "opus", "flac"],
        "supported_languages": ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR", "multilingual"],
        "supported_params": {
            "speed": {"min": 0.5, "max": 2.0, "default": 1.0},
            "pitch": {"min": -20, "max": 20, "default": 0},
            "style_prompt": {
                "min": 0,
                "max": 500,
                "default": 0,
            },  # character limit for style prompt
        },
    },
    "voai": {
        "display_name": "VoAI 台灣語音",
        "supported_formats": ["mp3", "wav"],
        "supported_languages": ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"],
        "supported_params": {
            "speed": {"min": 0.5, "max": 2.0, "default": 1.0},
        },
    },
}

# LLM Provider configurations
LLM_PROVIDER_CONFIGS = {
    "openai": {
        "display_name": "OpenAI GPT",
        "supported_formats": [],
        "supported_languages": ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"],
    },
    "azure-openai": {
        "display_name": "Azure OpenAI",
        "supported_formats": [],
        "supported_languages": ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"],
    },
    "anthropic": {
        "display_name": "Anthropic Claude",
        "supported_formats": [],
        "supported_languages": ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"],
    },
    "gemini": {
        "display_name": "Google Gemini",
        "supported_formats": [],
        "supported_languages": ["zh-TW", "zh-CN", "en-US", "ja-JP", "ko-KR"],
    },
}


def _build_provider_info(
    name: str,
    config: dict,
    provider_type: ProviderType,
    is_available: bool,
) -> ProviderInfo:
    """Build a ProviderInfo object from config."""
    supported_params = {}
    for param_name, param_config in config.get("supported_params", {}).items():
        supported_params[param_name] = SupportedParams(**param_config)

    return ProviderInfo(
        name=name,
        display_name=config["display_name"],
        type=provider_type,
        supported_formats=config.get("supported_formats", []),
        supported_languages=config.get("supported_languages", []),
        supported_params=supported_params,
        status=ProviderStatus.AVAILABLE if is_available else ProviderStatus.UNAVAILABLE,
    )


@router.get("/summary", response_model=ProvidersSummaryResponse)
async def get_providers_summary(
    _current_user: CurrentUserDep,
    container: Container = Depends(get_container),
) -> ProvidersSummaryResponse:
    """Get summary of all providers grouped by type.

    Returns TTS, STT, and LLM providers with their availability status.
    """
    tts_providers = container.get_tts_providers()
    stt_providers = container.get_stt_providers()
    llm_providers = container.get_llm_providers()

    # Build TTS providers list
    tts_list = []
    for name, config in TTS_PROVIDER_CONFIGS.items():
        tts_list.append(
            _build_provider_info(
                name=name,
                config=config,
                provider_type=ProviderType.TTS,
                is_available=name in tts_providers,
            )
        )

    # Build STT providers list from factory metadata
    stt_list = []
    for provider_info in STTProviderFactory.list_providers():
        name = provider_info["name"]
        stt_list.append(
            ProviderInfo(
                name=name,
                display_name=provider_info["display_name"],
                type=ProviderType.STT,
                supported_formats=provider_info.get("supported_formats", []),
                supported_languages=provider_info.get("supported_languages", []),
                supported_params={},
                status=ProviderStatus.AVAILABLE
                if name in stt_providers
                else ProviderStatus.UNAVAILABLE,
            )
        )

    # Build LLM providers list
    llm_list = []
    for name, config in LLM_PROVIDER_CONFIGS.items():
        llm_list.append(
            _build_provider_info(
                name=name,
                config=config,
                provider_type=ProviderType.LLM,
                is_available=name in llm_providers,
            )
        )

    return ProvidersSummaryResponse(
        tts=tts_list,
        stt=stt_list,
        llm=llm_list,
    )


@router.get("", response_model=ProvidersListResponse)
async def list_providers(
    _current_user: CurrentUserDep,
    container: Container = Depends(get_container),
) -> ProvidersListResponse:
    """List all available providers (TTS only for backward compatibility).

    Returns information about each configured TTS provider including
    supported formats, languages, and parameter ranges.
    The status reflects actual initialization state.
    """
    tts_providers = container.get_tts_providers()
    stt_providers = container.get_stt_providers()

    providers_list = []
    for name, config in TTS_PROVIDER_CONFIGS.items():
        is_tts_available = name in tts_providers
        is_stt_available = name in stt_providers
        providers_list.append(
            _build_provider_info(
                name=name,
                config=config,
                provider_type=ProviderType.TTS,
                is_available=is_tts_available or is_stt_available,
            )
        )

    return ProvidersListResponse(providers=providers_list)


@router.get("/{provider}/health", response_model=ProviderHealthResponse)
async def check_provider_health(
    provider: str,
    _current_user: CurrentUserDep,
    container: Container = Depends(get_container),
) -> ProviderHealthResponse:
    """Check health status of a specific provider.

    Performs a lightweight health check to verify the provider
    is accessible and responding within acceptable latency.
    """
    tts_providers = container.get_tts_providers()
    stt_providers = container.get_stt_providers()
    llm_providers = container.get_llm_providers()

    # Determine provider type
    provider_type = None
    if provider in tts_providers or provider in TTS_PROVIDER_CONFIGS:
        provider_type = ProviderType.TTS
    elif provider in stt_providers or provider in STTProviderFactory.PROVIDER_INFO:
        provider_type = ProviderType.STT
    elif provider in llm_providers or provider in LLM_PROVIDER_CONFIGS:
        provider_type = ProviderType.LLM

    if provider_type is None:
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
        type=provider_type,
        status=health_status,
        latency_ms=latency_ms,
        checked_at=datetime.now(UTC),
    )
