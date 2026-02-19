"""Provider-specific limits and constraints.

Defines text length limits and other constraints for different TTS providers.
"""

from dataclasses import dataclass

from src.domain.entities.long_text_tts import SplitConfig


@dataclass
class ProviderLimits:
    """Limits and constraints for a TTS provider."""

    provider_id: str
    max_text_length: int
    recommended_max_length: int | None = None
    warning_message: str | None = None
    limit_type: str = "chars"  # "chars" or "bytes"


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
        max_text_length=4000,  # Gemini API limit is 4000 bytes
        limit_type="bytes",
        recommended_max_length=2400,  # ~800 CJK chars in bytes
        warning_message="較長的中文文本可能導致 Gemini TTS 處理時間增加",
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


def get_split_config(provider_id: str) -> SplitConfig:
    """Get a SplitConfig for automatic text segmentation based on provider limits.

    Args:
        provider_id: Provider identifier

    Returns:
        SplitConfig with appropriate max_bytes or max_chars set
    """
    limits = get_provider_limits(provider_id)
    if limits.limit_type == "bytes":
        return SplitConfig(max_bytes=limits.max_text_length)
    return SplitConfig(max_chars=limits.max_text_length)


def validate_text_length(provider_id: str, text: str) -> tuple[bool, str | None, bool]:
    """Validate text length for a provider.

    Supports both character-based and byte-based limits depending on the provider.

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

    # Measure in the appropriate unit
    if limits.limit_type == "bytes":
        text_length = len(text.encode("utf-8"))
        unit = "bytes"
    else:
        text_length = len(text)
        unit = "characters"

    # Check hard limit
    if text_length > limits.max_text_length:
        return (
            False,
            f"Text length ({text_length} {unit}) exceeds maximum allowed "
            f"({limits.max_text_length} {unit}) for {provider_id}",
            False,
        )

    # Check recommended limit (warning) — always in same unit
    exceeds_recommended = False
    if limits.recommended_max_length and text_length > limits.recommended_max_length:
        exceeds_recommended = True

    return True, None, exceeds_recommended
