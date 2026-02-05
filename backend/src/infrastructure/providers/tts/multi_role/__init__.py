"""Multi-Role TTS Provider implementations."""

from src.infrastructure.providers.tts.multi_role.azure_ssml_builder import (
    AzureSSMLBuilder,
    AzureSSMLConfig,
)
from src.infrastructure.providers.tts.multi_role.capability_registry import (
    PROVIDER_CAPABILITIES,
    get_provider_capability,
)
from src.infrastructure.providers.tts.multi_role.elevenlabs_dialogue_builder import (
    ElevenLabsDialogueBuilder,
    ElevenLabsDialogueConfig,
    ElevenLabsDialogueRequest,
)
from src.infrastructure.providers.tts.multi_role.gemini_dialogue_builder import (
    GeminiDialogueBuilder,
    GeminiDialogueConfig,
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
    "AzureSSMLBuilder",
    "AzureSSMLConfig",
    "ElevenLabsDialogueBuilder",
    "ElevenLabsDialogueConfig",
    "ElevenLabsDialogueRequest",
    "GeminiDialogueBuilder",
    "GeminiDialogueConfig",
]
