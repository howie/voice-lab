"""Quota and Rate Limit Status API Routes."""

import asyncio
import logging
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.errors import ProviderQuotaInfo
from src.infrastructure.persistence.credential_repository import (
    SQLAlchemyProviderCredentialRepository,
)
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.providers.validators import ProviderValidatorRegistry
from src.presentation.api.middleware.auth import CurrentUserDep
from src.presentation.api.middleware.rate_limit import default_rate_limiter
from src.presentation.schemas.quota import (
    AppRateLimitStatus,
    ProviderQuotaStatus,
    ProviderRateLimitInfo,
    QuotaDashboardResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quota", tags=["Quota"])

# Static rate limit reference data per provider
# Based on public documentation as of 2026-01
PROVIDER_RATE_LIMITS: dict[str, ProviderRateLimitInfo] = {
    "gemini": ProviderRateLimitInfo(
        free_rpm=10,
        free_rpd=250,
        tier1_rpm=300,
        tier2_rpm=1000,
        notes="TTS models (Preview) 可能有更嚴格限制。Flash ~10 RPM / Pro ~5 RPM (Free)",
    ),
    "elevenlabs": ProviderRateLimitInfo(
        notes="依訂閱方案計算字元配額，無固定 RPM 限制",
    ),
    "azure": ProviderRateLimitInfo(
        free_rpm=20,
        tier1_rpm=200,
        notes="免費層 F0: 20 req/min; 標準層 S0: 200 req/min",
    ),
    "gcp": ProviderRateLimitInfo(
        notes="依 GCP 專案配額，可在 Console 申請增加",
    ),
    "openai": ProviderRateLimitInfo(
        free_rpm=3,
        tier1_rpm=50,
        tier2_rpm=100,
        notes="Whisper STT: Free 3 RPM, Tier 1: 50 RPM",
    ),
    "deepgram": ProviderRateLimitInfo(
        notes="依方案限制併發連線數和分鐘數",
    ),
    "voai": ProviderRateLimitInfo(
        notes="依方案限制，單次最大 500 字元",
    ),
    "anthropic": ProviderRateLimitInfo(
        free_rpm=5,
        tier1_rpm=50,
        tier2_rpm=1000,
        notes="Tier 1: 50 RPM / 40K TPM; Tier 2: 1000 RPM / 80K TPM",
    ),
    "speechmatics": ProviderRateLimitInfo(
        notes="依方案限制，企業方案可自訂",
    ),
}

# Providers that support quota querying via API
QUOTA_QUERYABLE_PROVIDERS = {"elevenlabs"}


async def _fetch_provider_quota(
    provider_id: str,
    api_key: str,
) -> dict | None:
    """Fetch quota info from a provider's API.

    Currently only ElevenLabs supports direct quota querying.
    Other providers return None (no API-queryable quota).
    """
    if provider_id not in QUOTA_QUERYABLE_PROVIDERS:
        return None

    try:
        validator = ProviderValidatorRegistry.get_validator(provider_id)
        result = await validator.validate(api_key)
        if result.is_valid and result.quota_info:
            return result.quota_info
    except Exception:
        logger.warning("Failed to fetch quota for %s", provider_id, exc_info=True)

    return None


@router.get("", response_model=QuotaDashboardResponse)
async def get_quota_dashboard(
    request: Request,
    current_user: CurrentUserDep,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> QuotaDashboardResponse:
    """Get quota and rate limit status for all providers.

    Returns per-provider quota information and application-level rate limits.
    For providers that support API-based quota querying (e.g., ElevenLabs),
    real-time usage data is fetched. For others, static reference data
    about known rate limits is returned.
    """
    user_id = uuid.UUID(current_user.id)
    repo = SQLAlchemyProviderCredentialRepository(session)

    # Get user's credentials
    credentials = await repo.list_by_user(user_id)
    cred_by_provider = {c.provider: c for c in credentials}

    # Build provider status list
    all_providers = ProviderValidatorRegistry.list_supported_providers()

    # Fetch quota for providers that support it (in parallel)
    quota_tasks: dict[str, asyncio.Task] = {}  # type: ignore[type-arg]
    async with asyncio.TaskGroup() as tg:
        for provider_id in all_providers:
            cred = cred_by_provider.get(provider_id)
            if cred and cred.is_valid and provider_id in QUOTA_QUERYABLE_PROVIDERS:
                quota_tasks[provider_id] = tg.create_task(
                    _fetch_provider_quota(provider_id, cred.api_key)
                )

    # Build response
    provider_statuses: list[ProviderQuotaStatus] = []
    for provider_id in all_providers:
        cred = cred_by_provider.get(provider_id)
        quota_info = ProviderQuotaInfo.get(provider_id)

        # Get quota data if available
        quota_data: dict | None = None
        if provider_id in quota_tasks:
            quota_data = quota_tasks[provider_id].result()

        # Calculate usage percent
        usage_percent: float | None = None
        character_count: int | None = None
        character_limit: int | None = None
        remaining_characters: int | None = None
        tier: str | None = None

        if quota_data:
            character_count = quota_data.get("character_count")
            character_limit = quota_data.get("character_limit")
            if character_count is not None and character_limit and character_limit > 0:
                usage_percent = round((character_count / character_limit) * 100, 1)
                remaining_characters = character_limit - character_count
            tier = quota_data.get("tier")

        provider_statuses.append(
            ProviderQuotaStatus(
                provider=provider_id,
                display_name=quota_info.get("display_name", provider_id.title()),
                has_credential=cred is not None,
                is_valid=cred.is_valid if cred else False,
                character_count=character_count,
                character_limit=character_limit,
                remaining_characters=remaining_characters,
                usage_percent=usage_percent,
                tier=tier,
                rate_limits=PROVIDER_RATE_LIMITS.get(provider_id),
                help_url=quota_info.get("help_url"),
                suggestions=quota_info.get("suggestions", []),
                last_validated_at=cred.last_validated_at if cred else None,
            )
        )

    # Get app-level rate limits
    config = default_rate_limiter.config

    # Simulate request for remaining count
    general_remaining = default_rate_limiter.get_remaining(request)

    app_rate_limits = AppRateLimitStatus(
        general_rpm=config.requests_per_minute,
        general_rph=config.requests_per_hour,
        tts_rpm=config.tts_requests_per_minute,
        tts_rph=config.tts_requests_per_hour,
        general_minute_remaining=general_remaining["minute_remaining"],
        general_hour_remaining=general_remaining["hour_remaining"],
        tts_minute_remaining=config.tts_requests_per_minute,
        tts_hour_remaining=config.tts_requests_per_hour,
    )

    return QuotaDashboardResponse(
        providers=provider_statuses,
        app_rate_limits=app_rate_limits,
        fetched_at=datetime.now(UTC),
    )
