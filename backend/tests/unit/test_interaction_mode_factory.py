"""Unit tests for InteractionModeFactory with user credential support."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.presentation.api.routes.interaction_ws import InteractionModeFactory


class TestInteractionModeFactory:
    """Tests for InteractionModeFactory credential injection."""

    @pytest.mark.asyncio
    async def test_create_is_async(self):
        """Confirm create() is a coroutine."""
        assert asyncio.iscoroutinefunction(InteractionModeFactory.create)

    @pytest.mark.asyncio
    async def test_create_unsupported_mode(self):
        """Unsupported mode should raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported interaction mode"):
            await InteractionModeFactory.create("unknown", {})

    @pytest.mark.asyncio
    async def test_create_cascade_with_user_credentials(self):
        """When DB has user credentials, factories should receive the api_key."""
        user_id = uuid4()
        mock_db = MagicMock()

        # Mock credential with openai provider
        mock_cred = MagicMock()
        mock_cred.provider = "openai"
        mock_cred.api_key = "user-openai-key"
        mock_cred.is_valid = True

        mock_credential_repo = MagicMock()
        mock_credential_repo.list_by_user = AsyncMock(return_value=[mock_cred])

        config = {
            "stt_provider": "whisper",  # maps to openai
            "llm_provider": "openai",
            "tts_provider": "elevenlabs",
        }

        with (
            patch(
                "src.presentation.api.routes.interaction_ws.SQLAlchemyProviderCredentialRepository",
                return_value=mock_credential_repo,
            ),
            patch(
                "src.infrastructure.providers.stt.factory.STTProviderFactory.create"
            ) as mock_stt_create,
            patch(
                "src.infrastructure.providers.llm.factory.LLMProviderFactory.create"
            ) as mock_llm_create,
            patch(
                "src.infrastructure.providers.tts.factory.TTSProviderFactory.create_default"
            ) as mock_tts_default,
        ):
            mock_stt_create.return_value = MagicMock()
            mock_llm_create.return_value = MagicMock()
            mock_tts_default.return_value = MagicMock()

            await InteractionModeFactory.create("cascade", config, user_id=user_id, db=mock_db)

            # STT should get openai key (whisper -> openai mapping)
            mock_stt_create.assert_called_once()
            stt_call_args = mock_stt_create.call_args
            assert stt_call_args[0][0] == "whisper"
            assert stt_call_args[0][1].get("api_key") == "user-openai-key"

            # LLM should get openai key
            mock_llm_create.assert_called_once()
            llm_call_args = mock_llm_create.call_args
            assert llm_call_args[0][0] == "openai"
            assert llm_call_args[0][1].get("api_key") == "user-openai-key"

            # TTS has no elevenlabs credential, should fallback to default
            mock_tts_default.assert_called_once_with("elevenlabs")

    @pytest.mark.asyncio
    async def test_create_cascade_fallback_to_env(self):
        """When DB has no credentials, factories should use create_default."""
        user_id = uuid4()
        mock_db = MagicMock()

        mock_credential_repo = MagicMock()
        mock_credential_repo.list_by_user = AsyncMock(return_value=[])

        config = {
            "stt_provider": "gcp",
            "llm_provider": "gemini",
            "tts_provider": "gemini",
        }

        with (
            patch(
                "src.presentation.api.routes.interaction_ws.SQLAlchemyProviderCredentialRepository",
                return_value=mock_credential_repo,
            ),
            patch(
                "src.infrastructure.providers.stt.factory.STTProviderFactory.create_default"
            ) as mock_stt_default,
            patch(
                "src.infrastructure.providers.llm.factory.LLMProviderFactory.create_default"
            ) as mock_llm_default,
            patch(
                "src.infrastructure.providers.tts.factory.TTSProviderFactory.create_default"
            ) as mock_tts_default,
        ):
            mock_stt_default.return_value = MagicMock()
            mock_llm_default.return_value = MagicMock()
            mock_tts_default.return_value = MagicMock()

            await InteractionModeFactory.create("cascade", config, user_id=user_id, db=mock_db)

            # No credentials → all providers fall back to create_default
            mock_stt_default.assert_called_once_with("gcp")
            mock_llm_default.assert_called_once_with("gemini")
            mock_tts_default.assert_called_once_with("gemini")

    @pytest.mark.asyncio
    async def test_create_cascade_without_db(self):
        """Without db parameter, should not query DB and use env vars."""
        config = {
            "stt_provider": "gcp",
            "llm_provider": "gemini",
            "tts_provider": "gemini",
        }

        with (
            patch(
                "src.infrastructure.providers.stt.factory.STTProviderFactory.create_default"
            ) as mock_stt_default,
            patch(
                "src.infrastructure.providers.llm.factory.LLMProviderFactory.create_default"
            ) as mock_llm_default,
            patch(
                "src.infrastructure.providers.tts.factory.TTSProviderFactory.create_default"
            ) as mock_tts_default,
        ):
            mock_stt_default.return_value = MagicMock()
            mock_llm_default.return_value = MagicMock()
            mock_tts_default.return_value = MagicMock()

            # No user_id and no db
            await InteractionModeFactory.create("cascade", config)

            # All should use create_default (no user credential lookup)
            mock_stt_default.assert_called_once_with("gcp")
            mock_llm_default.assert_called_once_with("gemini")
            mock_tts_default.assert_called_once_with("gemini")

    @pytest.mark.asyncio
    async def test_create_realtime_mode(self):
        """Realtime mode should delegate to RealtimeModeFactory."""
        config = {"provider": "openai"}

        with patch(
            "src.domain.services.interaction.realtime_mode.RealtimeModeFactory.create"
        ) as mock_realtime:
            mock_realtime.return_value = MagicMock()
            result = await InteractionModeFactory.create("realtime", config)

            mock_realtime.assert_called_once_with(config)
            assert result is not None
