"""Contract tests for interaction providers mapping completeness."""

from src.infrastructure.providers.llm.factory import LLMProviderFactory
from src.infrastructure.providers.tts.factory import TTSProviderFactory
from src.presentation.api.routes.interaction_ws import (
    _LLM_CREDENTIAL_MAPPING,
    _STT_CREDENTIAL_MAPPING,
    _TTS_CREDENTIAL_MAPPING,
)


class TestInteractionProvidersMapping:
    """Contract tests ensuring all cascade providers are mapped."""

    def test_tts_mapping_includes_gcp(self):
        """tts_mapping should include gcp."""
        assert "gcp" in _TTS_CREDENTIAL_MAPPING
        assert _TTS_CREDENTIAL_MAPPING["gcp"] == "gcp"

    def test_stt_mapping_includes_speechmatics(self):
        """stt_mapping should include speechmatics."""
        assert "speechmatics" in _STT_CREDENTIAL_MAPPING
        assert _STT_CREDENTIAL_MAPPING["speechmatics"] == "speechmatics"

    def test_all_stt_providers_mapped(self):
        """All STT factory supported providers should be in mapping."""
        # These are the providers supported by the cascade mode
        cascade_stt_providers = ["azure", "gcp", "whisper", "speechmatics"]
        for provider in cascade_stt_providers:
            assert provider in _STT_CREDENTIAL_MAPPING, (
                f"STT provider '{provider}' missing from credential mapping"
            )

    def test_all_llm_providers_mapped(self):
        """All LLM factory supported providers should be in mapping."""
        llm_providers = LLMProviderFactory.get_supported_providers()
        for provider in llm_providers:
            assert provider in _LLM_CREDENTIAL_MAPPING, (
                f"LLM provider '{provider}' missing from credential mapping"
            )

    def test_all_tts_providers_mapped(self):
        """All TTS factory supported providers should be in mapping."""
        tts_providers = TTSProviderFactory.get_supported_providers()
        for provider in tts_providers:
            assert provider in _TTS_CREDENTIAL_MAPPING, (
                f"TTS provider '{provider}' missing from credential mapping"
            )

    def test_stt_mapping_values_are_valid_provider_ids(self):
        """All mapped credential provider names should be valid provider IDs."""
        valid_ids = {"azure", "gcp", "openai", "speechmatics"}
        for cascade_name, cred_name in _STT_CREDENTIAL_MAPPING.items():
            assert cred_name in valid_ids, (
                f"STT mapping '{cascade_name}' -> '{cred_name}' is not a valid provider ID"
            )

    def test_llm_mapping_values_are_valid_provider_ids(self):
        """All mapped credential provider names should be valid provider IDs."""
        valid_ids = {"openai", "anthropic", "gemini", "azure"}
        for cascade_name, cred_name in _LLM_CREDENTIAL_MAPPING.items():
            assert cred_name in valid_ids, (
                f"LLM mapping '{cascade_name}' -> '{cred_name}' is not a valid provider ID"
            )

    def test_tts_mapping_values_are_valid_provider_ids(self):
        """All mapped credential provider names should be valid provider IDs."""
        valid_ids = {"azure", "gcp", "gemini", "elevenlabs", "voai"}
        for cascade_name, cred_name in _TTS_CREDENTIAL_MAPPING.items():
            assert cred_name in valid_ids, (
                f"TTS mapping '{cascade_name}' -> '{cred_name}' is not a valid provider ID"
            )
