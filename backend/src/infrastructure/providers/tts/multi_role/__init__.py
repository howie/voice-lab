"""Multi-Role TTS Provider implementations."""

from src.infrastructure.providers.tts.multi_role.capability_registry import (
    PROVIDER_CAPABILITIES,
    get_provider_capability,
)
from src.infrastructure.providers.tts.multi_role.segmented_merger import (
    MergeConfig,
    SegmentedMergerService,
)

__all__ = [
    "PROVIDER_CAPABILITIES",
    "get_provider_capability",
    "MergeConfig",
    "SegmentedMergerService",
]
