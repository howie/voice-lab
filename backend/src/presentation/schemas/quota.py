"""Quota and Rate Limit Status Schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class ProviderRateLimitInfo(BaseModel):
    """Known rate limit tiers for a provider (static reference data)."""

    free_rpm: int | None = Field(default=None, description="Free tier RPM")
    free_rpd: int | None = Field(default=None, description="Free tier RPD")
    tier1_rpm: int | None = Field(default=None, description="Tier 1 RPM")
    tier2_rpm: int | None = Field(default=None, description="Tier 2 RPM")
    notes: str | None = Field(default=None, description="Additional notes")


class ProviderQuotaStatus(BaseModel):
    """Quota status for a single provider."""

    provider: str = Field(description="Provider identifier")
    display_name: str = Field(description="Provider display name")
    has_credential: bool = Field(description="Whether user has credential configured")
    is_valid: bool = Field(default=False, description="Whether credential is valid")

    # Quota info (from provider API, if available)
    character_count: int | None = Field(
        default=None, description="Characters used in current period"
    )
    character_limit: int | None = Field(
        default=None, description="Character limit for current tier"
    )
    remaining_characters: int | None = Field(default=None, description="Remaining characters")
    usage_percent: float | None = Field(default=None, description="Usage percentage (0-100)")
    tier: str | None = Field(default=None, description="Subscription tier name")

    # Rate limit reference info
    rate_limits: ProviderRateLimitInfo | None = Field(
        default=None, description="Known rate limit info"
    )

    # Help info
    help_url: str | None = Field(default=None, description="URL for quota management")
    suggestions: list[str] = Field(
        default_factory=list, description="Suggestions for managing quota"
    )
    last_validated_at: datetime | None = Field(
        default=None, description="Last validation timestamp"
    )


class AppRateLimitStatus(BaseModel):
    """Application-level rate limit status for the current user."""

    general_rpm: int = Field(description="General requests per minute limit")
    general_rph: int = Field(description="General requests per hour limit")
    tts_rpm: int = Field(description="TTS requests per minute limit")
    tts_rph: int = Field(description="TTS requests per hour limit")
    general_minute_remaining: int = Field(description="Remaining general requests this minute")
    general_hour_remaining: int = Field(description="Remaining general requests this hour")
    tts_minute_remaining: int = Field(description="Remaining TTS requests this minute")
    tts_hour_remaining: int = Field(description="Remaining TTS requests this hour")


class QuotaDashboardResponse(BaseModel):
    """Full quota dashboard response."""

    providers: list[ProviderQuotaStatus] = Field(description="Per-provider quota status")
    app_rate_limits: AppRateLimitStatus = Field(description="Application-level rate limits")
    fetched_at: datetime = Field(description="Timestamp of this data fetch")
