"""Multi-Role TTS Provider Interface (Port)."""

from abc import ABC, abstractmethod

from src.domain.entities.multi_role_tts import (
    DialogueTurn,
    MultiRoleSupportType,
    MultiRoleTTSResult,
)


class IMultiRoleTTSProvider(ABC):
    """Abstract interface for multi-role TTS providers.

    This interface extends the standard TTS provider contract to support
    multi-role dialogue synthesis. Providers may support this natively
    (like ElevenLabs v3 or Azure SSML) or through segmented merging.
    """

    @property
    @abstractmethod
    def multi_role_support(self) -> MultiRoleSupportType:
        """Get the type of multi-role support this provider offers.

        Returns:
            MultiRoleSupportType indicating native, segmented, or unsupported.
        """
        pass

    @abstractmethod
    async def synthesize_multi_role(
        self,
        turns: list[DialogueTurn],
        voice_map: dict[str, str],
        language: str = "zh-TW",
        output_format: str = "mp3",
    ) -> MultiRoleTTSResult:
        """Synthesize multi-role dialogue into audio.

        Args:
            turns: List of dialogue turns to synthesize.
            voice_map: Mapping of speaker identifiers to voice IDs.
            language: Language code for synthesis.
            output_format: Desired output audio format.

        Returns:
            MultiRoleTTSResult with synthesized audio and metadata.

        Raises:
            TTSProviderError: If synthesis fails.
            ValueError: If voice_map doesn't cover all speakers in turns.
        """
        pass
