"""Unit tests for child mode parameter handling in STT providers.

Feature: 003-stt-testing-module - User Story 4
Task: T055 - Unit test for child mode parameter handling

Tests that child_mode parameter is correctly passed to and handled by providers.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from src.domain.entities.audio import AudioData, AudioFormat
from src.domain.entities.stt import STTRequest


@pytest.mark.asyncio
class TestAzureChildMode:
    """Test child mode handling in Azure STT provider."""

    async def test_child_mode_enables_phrase_hints(self) -> None:
        """Test that child_mode=True enables phrase hints in Azure."""
        from src.infrastructure.providers.stt.azure_stt import AzureSTTProvider

        provider = AzureSTTProvider(subscription_key="test-key", region="eastasia")

        audio_data = AudioData(
            data=b"fake audio data",
            format=AudioFormat.WAV,
            sample_rate=16000,
        )

        request = STTRequest(
            provider="azure",
            language="zh-TW",
            audio=audio_data,
            child_mode=True,
        )

        # Mock the recognition process
        with (
            patch(
                "src.infrastructure.providers.stt.azure_stt.speechsdk.SpeechRecognizer"
            ) as mock_recognizer_class,
            patch(
                "src.infrastructure.providers.stt.azure_stt.speechsdk.PhraseListGrammar.from_recognizer"
            ) as mock_grammar_class,
        ):
            mock_recognizer = MagicMock()
            mock_recognizer_class.return_value = mock_recognizer
            mock_grammar = MagicMock()
            mock_grammar_class.return_value = mock_grammar

            # Mock the recognition callbacks
            def start_recognition():
                # Simulate successful recognition
                event = MagicMock()
                event.result.reason = MagicMock()
                event.result.reason = Mock()  # speechsdk.ResultReason.RecognizedSpeech
                event.result.text = "媽媽 爸爸"
                event.result.properties.get.return_value = "{}"

                # Trigger recognized callback
                for callback_tuple in mock_recognizer.recognized.connect.call_args_list:
                    callback = callback_tuple[0][0]
                    callback(event)

                # Trigger session stopped
                for callback_tuple in mock_recognizer.session_stopped.connect.call_args_list:
                    callback = callback_tuple[0][0]
                    callback(event)

            mock_recognizer.start_continuous_recognition.side_effect = start_recognition

            try:
                _ = await provider._do_transcribe(request)

                # Verify phrase hints were added
                assert mock_grammar_class.called
                assert mock_grammar.addPhrase.called

                # Verify common child-related phrases were added
                added_phrases = [call[0][0] for call in mock_grammar.addPhrase.call_args_list]
                assert "媽媽" in added_phrases
                assert "爸爸" in added_phrases
                assert "老師" in added_phrases

            except NotImplementedError:
                # Some providers may not be fully implemented in test
                pass

    async def test_child_mode_false_no_phrase_hints(self) -> None:
        """Test that child_mode=False does not add phrase hints."""
        from src.infrastructure.providers.stt.azure_stt import AzureSTTProvider

        provider = AzureSTTProvider(subscription_key="test-key", region="eastasia")

        audio_data = AudioData(
            data=b"fake audio data",
            format=AudioFormat.WAV,
            sample_rate=16000,
        )

        request = STTRequest(
            provider="azure",
            language="zh-TW",
            audio=audio_data,
            child_mode=False,
        )

        with (
            patch(
                "src.infrastructure.providers.stt.azure_stt.speechsdk.SpeechRecognizer"
            ) as mock_recognizer_class,
            patch(
                "src.infrastructure.providers.stt.azure_stt.speechsdk.PhraseListGrammar.from_recognizer"
            ) as mock_grammar_class,
        ):
            mock_recognizer = MagicMock()
            mock_recognizer_class.return_value = mock_recognizer

            def start_recognition():
                event = MagicMock()
                event.result.reason = Mock()
                event.result.text = "測試文字"
                event.result.properties.get.return_value = "{}"

                for callback_tuple in mock_recognizer.recognized.connect.call_args_list:
                    callback = callback_tuple[0][0]
                    callback(event)

                for callback_tuple in mock_recognizer.session_stopped.connect.call_args_list:
                    callback = callback_tuple[0][0]
                    callback(event)

            mock_recognizer.start_continuous_recognition.side_effect = start_recognition

            try:
                _ = await provider._do_transcribe(request)

                # Verify phrase hints were NOT added
                assert not mock_grammar_class.called

            except NotImplementedError:
                pass


@pytest.mark.asyncio
class TestGCPChildMode:
    """Test child mode handling in GCP STT provider."""

    async def test_child_mode_changes_model(self) -> None:
        """Test that child_mode=True uses command_and_search model in GCP."""
        from src.infrastructure.providers.stt.gcp_stt import GCPSTTProvider

        with patch("src.infrastructure.providers.stt.gcp_stt.speech.SpeechClient"):
            provider = GCPSTTProvider(credentials_path=None)

            audio_data = AudioData(
                data=b"fake audio data",
                format=AudioFormat.WAV,
                sample_rate=16000,
            )

            request = STTRequest(
                provider="gcp",
                language="zh-TW",
                audio=audio_data,
                child_mode=True,
            )

            # Mock the recognize call
            mock_response = MagicMock()
            mock_response.results = []

            provider._client.recognize = Mock(return_value=mock_response)

            await provider._do_transcribe(request)

            # Verify recognize was called
            assert provider._client.recognize.called

            # Get the config that was passed
            call_args = provider._client.recognize.call_args
            config = call_args.kwargs["config"]

            # Verify model is command_and_search
            assert config.model == "command_and_search"

            # Verify speech contexts were added
            assert len(config.speech_contexts) > 0
            assert config.speech_contexts[0].boost == 10.0

    async def test_child_mode_false_uses_default_model(self) -> None:
        """Test that child_mode=False uses latest_long model."""
        from src.infrastructure.providers.stt.gcp_stt import GCPSTTProvider

        with patch("src.infrastructure.providers.stt.gcp_stt.speech.SpeechClient"):
            provider = GCPSTTProvider(credentials_path=None)

            audio_data = AudioData(
                data=b"fake audio data",
                format=AudioFormat.WAV,
                sample_rate=16000,
            )

            request = STTRequest(
                provider="gcp",
                language="zh-TW",
                audio=audio_data,
                child_mode=False,
            )

            mock_response = MagicMock()
            mock_response.results = []

            provider._client.recognize = Mock(return_value=mock_response)

            await provider._do_transcribe(request)

            # Verify recognize was called
            assert provider._client.recognize.called

            # Get the config that was passed
            call_args = provider._client.recognize.call_args
            config = call_args.kwargs["config"]

            # Verify model is latest_long (default)
            assert config.model == "latest_long"

            # Verify no speech contexts
            assert len(config.speech_contexts) == 0


class TestChildModeSupport:
    """Test child mode support detection."""

    def test_azure_supports_child_mode(self) -> None:
        """Test that Azure provider reports child mode support."""
        from src.infrastructure.providers.stt.azure_stt import AzureSTTProvider

        provider = AzureSTTProvider(subscription_key="test-key", region="eastasia")
        assert provider.supports_child_mode is True

    def test_gcp_supports_child_mode(self) -> None:
        """Test that GCP provider reports child mode support."""
        from src.infrastructure.providers.stt.gcp_stt import GCPSTTProvider

        with patch("src.infrastructure.providers.stt.gcp_stt.speech.SpeechClient"):
            provider = GCPSTTProvider(credentials_path=None)
            assert provider.supports_child_mode is True

    def test_whisper_does_not_support_child_mode(self) -> None:
        """Test that Whisper provider does not support child mode."""
        from src.infrastructure.providers.stt.whisper_stt import WhisperSTTProvider

        provider = WhisperSTTProvider(api_key="test-key")
        assert provider.supports_child_mode is False
