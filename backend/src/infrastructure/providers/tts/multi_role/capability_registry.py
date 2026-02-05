"""Provider Multi-Role Capability Registry.

This module contains the capability definitions for all supported TTS providers
regarding their multi-role dialogue synthesis capabilities.
"""

from src.domain.entities.multi_role_tts import (
    MultiRoleSupportType,
    ProviderMultiRoleCapability,
)

# Provider capability registry
PROVIDER_CAPABILITIES: dict[str, ProviderMultiRoleCapability] = {
    "elevenlabs": ProviderMultiRoleCapability(
        provider_name="elevenlabs",
        support_type=MultiRoleSupportType.NATIVE,
        max_speakers=10,
        character_limit=5000,
        advanced_features=["interrupting", "overlapping", "laughs"],
        notes="Uses v3 Audio Tags syntax: [dialogue][S1][S2]",
    ),
    "azure": ProviderMultiRoleCapability(
        provider_name="azure",
        support_type=MultiRoleSupportType.NATIVE,
        max_speakers=10,
        character_limit=10000,
        advanced_features=["express-as styles"],
        notes="Uses SSML <voice> elements for multi-speaker",
    ),
    "gemini": ProviderMultiRoleCapability(
        provider_name="gemini",
        support_type=MultiRoleSupportType.NATIVE,
        max_speakers=6,
        character_limit=1333,
        advanced_features=["style prompts", "SSML", "inline emotions", "multi-speaker"],
        notes=(
            "原生 multiSpeakerVoiceConfig 多角色模式（上限 4000 bytes / ~1333 CJK 字元），"
            "超過自動 fallback 到 SEGMENTED。支援 Style Prompt。"
        ),
    ),
    "openai": ProviderMultiRoleCapability(
        provider_name="openai",
        support_type=MultiRoleSupportType.SEGMENTED,
        max_speakers=6,
        character_limit=4096,
        advanced_features=["steerability"],
        notes="Requires segmented synthesis with audio merging",
    ),
    "cartesia": ProviderMultiRoleCapability(
        provider_name="cartesia",
        support_type=MultiRoleSupportType.SEGMENTED,
        max_speakers=6,
        character_limit=3000,
        advanced_features=[],
        notes="Requires segmented synthesis with audio merging",
    ),
    "deepgram": ProviderMultiRoleCapability(
        provider_name="deepgram",
        support_type=MultiRoleSupportType.SEGMENTED,
        max_speakers=6,
        character_limit=2000,
        advanced_features=[],
        notes="Requires segmented synthesis with audio merging",
    ),
    "voai": ProviderMultiRoleCapability(
        provider_name="voai",
        support_type=MultiRoleSupportType.SEGMENTED,
        max_speakers=6,
        character_limit=3000,
        advanced_features=["style prompts"],
        notes="VoAI 台灣語音，支援多種語氣風格，使用分段合成模式",
    ),
}


def get_provider_capability(provider_name: str) -> ProviderMultiRoleCapability | None:
    """Get the multi-role capability for a specific provider.

    Args:
        provider_name: The provider identifier (e.g., 'elevenlabs', 'azure').

    Returns:
        ProviderMultiRoleCapability if found, None otherwise.
    """
    return PROVIDER_CAPABILITIES.get(provider_name.lower())


def get_all_capabilities() -> list[ProviderMultiRoleCapability]:
    """Get all provider capabilities.

    Returns:
        List of all provider capabilities.
    """
    return list(PROVIDER_CAPABILITIES.values())


def get_native_providers() -> list[str]:
    """Get list of providers that support native multi-role synthesis.

    Returns:
        List of provider names with native support.
    """
    return [
        name
        for name, cap in PROVIDER_CAPABILITIES.items()
        if cap.support_type == MultiRoleSupportType.NATIVE
    ]


def get_segmented_providers() -> list[str]:
    """Get list of providers that require segmented synthesis.

    Returns:
        List of provider names requiring segmented synthesis.
    """
    return [
        name
        for name, cap in PROVIDER_CAPABILITIES.items()
        if cap.support_type == MultiRoleSupportType.SEGMENTED
    ]
