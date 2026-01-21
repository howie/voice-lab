"""Cascade Mode Service Factory.

Feature: 004-interaction-module
T049: Mode selection logic - factory for creating CascadeModeService.
"""

from typing import Any

from src.domain.services.interaction.base import InteractionModeService
from src.domain.services.interaction.cascade_mode import CascadeModeService
from src.infrastructure.providers.llm.factory import LLMProviderFactory
from src.infrastructure.providers.stt.factory import STTProviderFactory
from src.infrastructure.providers.tts.factory import TTSProviderFactory


class CascadeModeFactory:
    """Factory for creating CascadeModeService instances.

    Creates a cascade service with configured STT, LLM, and TTS providers
    based on the provided configuration.
    """

    # Default providers
    DEFAULT_STT_PROVIDER = "azure"
    DEFAULT_LLM_PROVIDER = "openai"
    DEFAULT_TTS_PROVIDER = "azure"

    # Default credentials (from environment variables)
    DEFAULT_STT_CREDENTIALS: dict[str, Any] = {}
    DEFAULT_LLM_CREDENTIALS: dict[str, Any] = {}
    DEFAULT_TTS_CREDENTIALS: dict[str, Any] = {}

    def __init__(
        self,
        default_stt_credentials: dict[str, Any] | None = None,
        default_llm_credentials: dict[str, Any] | None = None,
        default_tts_credentials: dict[str, Any] | None = None,
    ) -> None:
        """Initialize factory with default credentials.

        Args:
            default_stt_credentials: Default STT provider credentials
            default_llm_credentials: Default LLM provider credentials
            default_tts_credentials: Default TTS provider credentials
        """
        self._default_stt_creds = default_stt_credentials or {}
        self._default_llm_creds = default_llm_credentials or {}
        self._default_tts_creds = default_tts_credentials or {}

    def create(self, config: dict[str, Any]) -> InteractionModeService:
        """Create a CascadeModeService with providers from config.

        Args:
            config: Configuration dict with:
                - stt_provider: STT provider name (azure, gcp, whisper)
                - stt_credentials: Optional STT credentials
                - llm_provider: LLM provider name (openai, anthropic, gemini)
                - llm_credentials: Optional LLM credentials
                - tts_provider: TTS provider name (azure, gcp, elevenlabs)
                - tts_credentials: Optional TTS credentials
                - tts_voice: Voice ID for TTS
                - language: Language code (default: zh-TW)

        Returns:
            Configured CascadeModeService

        Raises:
            ValueError: If required providers are not specified or invalid
        """
        # Extract provider names
        stt_provider_name = config.get("stt_provider", self.DEFAULT_STT_PROVIDER)
        llm_provider_name = config.get("llm_provider", self.DEFAULT_LLM_PROVIDER)
        tts_provider_name = config.get("tts_provider", self.DEFAULT_TTS_PROVIDER)

        # Extract credentials (merge with defaults)
        stt_credentials = {**self._default_stt_creds, **config.get("stt_credentials", {})}
        llm_credentials = {**self._default_llm_creds, **config.get("llm_credentials", {})}
        tts_api_key = config.get("tts_api_key") or self._default_tts_creds.get("api_key")

        # Create providers
        try:
            stt_provider = STTProviderFactory.create(stt_provider_name, stt_credentials)
        except ValueError as e:
            raise ValueError(f"Invalid STT provider config: {e}") from e

        try:
            llm_provider = LLMProviderFactory.create(llm_provider_name, llm_credentials)
        except ValueError as e:
            raise ValueError(f"Invalid LLM provider config: {e}") from e

        try:
            if tts_api_key:
                tts_provider = TTSProviderFactory.create_with_key(tts_provider_name, tts_api_key)
            else:
                tts_provider = TTSProviderFactory.create_default(tts_provider_name)
        except Exception as e:
            raise ValueError(f"Invalid TTS provider config: {e}") from e

        # Create and return cascade service
        return CascadeModeService(
            stt_provider=stt_provider,
            llm_provider=llm_provider,
            tts_provider=tts_provider,
        )

    @classmethod
    def get_available_providers(cls) -> dict[str, list[str]]:
        """Get lists of available providers for each category.

        Returns:
            Dict with 'stt', 'llm', 'tts' keys mapping to provider lists
        """
        return {
            "stt": STTProviderFactory.get_supported_providers(),
            "llm": LLMProviderFactory.get_supported_providers(),
            "tts": TTSProviderFactory.get_supported_providers(),
        }

    @classmethod
    def get_provider_info(cls) -> dict[str, list[dict[str, Any]]]:
        """Get detailed info about all available providers.

        Returns:
            Dict with 'stt', 'llm', 'tts' keys mapping to provider info lists
        """
        return {
            "stt": STTProviderFactory.list_providers(),
            "llm": LLMProviderFactory.list_providers(),
            "tts": [
                {"name": p, "display_name": p.title()}
                for p in TTSProviderFactory.get_supported_providers()
            ],
        }
