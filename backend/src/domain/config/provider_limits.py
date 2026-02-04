"""Provider-specific limits and constraints.

Defines text length limits and other constraints for different TTS providers.
"""

from dataclasses import dataclass


@dataclass
class ProviderLimits:
    """Limits and constraints for a TTS provider."""

    provider_id: str
    max_text_length: int
    recommended_max_length: int | None = None
    warning_message: str | None = None


# Provider limits configuration
PROVIDER_LIMITS: dict[str, ProviderLimits] = {
    "azure": ProviderLimits(
        provider_id="azure",
        max_text_length=5000,
    ),
    "gcp": ProviderLimits(
        provider_id="gcp",
        max_text_length=5000,
    ),
    "elevenlabs": ProviderLimits(
        provider_id="elevenlabs",
        max_text_length=5000,
    ),
    "gemini": ProviderLimits(
        provider_id="gemini",
        max_text_length=4000,  # Gemini limit is 4000 bytes; use bytes for CJK safety
    ),
    "voai": ProviderLimits(
        provider_id="voai",
        max_text_length=500,  # VoAI API hard limit
        recommended_max_length=None,
        warning_message=None,
    ),
}

# Default limits for unknown providers
DEFAULT_LIMITS = ProviderLimits(
    provider_id="default",
    max_text_length=5000,
)


def get_provider_limits(provider_id: str) -> ProviderLimits:
    """Get limits for a specific provider.

    Args:
        provider_id: Provider identifier

    Returns:
        Provider limits configuration
    """
    return PROVIDER_LIMITS.get(provider_id, DEFAULT_LIMITS)


def validate_text_length(provider_id: str, text: str) -> tuple[bool, str | None, bool]:
    """Validate text length for a provider.

    Args:
        provider_id: Provider identifier
        text: Text to validate

    Returns:
        Tuple of (is_valid, error_message, exceeds_recommended)
        - is_valid: Whether text length is within max limit
        - error_message: Error message if invalid
        - exceeds_recommended: Whether text exceeds recommended limit (warning)
    """
    limits = get_provider_limits(provider_id)
    text_length = len(text)

    # Check hard limit
    if text_length > limits.max_text_length:
        return (
            False,
            f"Text length ({text_length}) exceeds maximum allowed ({limits.max_text_length}) for {provider_id}",
            False,
        )

    # Check recommended limit (warning)
    exceeds_recommended = False
    if limits.recommended_max_length and text_length > limits.recommended_max_length:
        exceeds_recommended = True

    return True, None, exceeds_recommended
