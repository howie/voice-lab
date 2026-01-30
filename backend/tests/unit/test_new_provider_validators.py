"""Unit tests for new Provider Validators (OpenAI, Anthropic, GCP, VoAI, Speechmatics)."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.infrastructure.providers.validators.anthropic_validator import AnthropicValidator
from src.infrastructure.providers.validators.gcp import GCPValidator
from src.infrastructure.providers.validators.openai import OpenAIValidator
from src.infrastructure.providers.validators.speechmatics import SpeechmaticsValidator
from src.infrastructure.providers.validators.voai import VoAIValidator


class TestOpenAIValidator:
    """Unit tests for OpenAI API key validator."""

    @pytest.fixture
    def validator(self) -> OpenAIValidator:
        return OpenAIValidator()

    @pytest.mark.asyncio
    async def test_provider_id(self, validator: OpenAIValidator):
        assert validator.provider_id == "openai"

    @pytest.mark.asyncio
    async def test_validate_success(self, validator: OpenAIValidator):
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await validator.validate("valid-key")

        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_invalid_key(self, validator: OpenAIValidator):
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await validator.validate("invalid-key")

        assert result.is_valid is False
        assert result.error_message == "Invalid API key"

    @pytest.mark.asyncio
    async def test_validate_rate_limited(self, validator: OpenAIValidator):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "30"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await validator.validate("key")

        assert result.is_valid is False
        assert "Rate limited" in (result.error_message or "")

    @pytest.mark.asyncio
    async def test_validate_timeout(self, validator: OpenAIValidator):
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("timeout")
            )
            result = await validator.validate("key")

        assert result.is_valid is False
        assert result.error_message == "Request timed out"

    @pytest.mark.asyncio
    async def test_validate_network_error(self, validator: OpenAIValidator):
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.RequestError("connection failed", request=MagicMock())
            )
            result = await validator.validate("key")

        assert result.is_valid is False
        assert "Network error" in (result.error_message or "")

    @pytest.mark.asyncio
    async def test_get_available_models(self, validator: OpenAIValidator):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "gpt-4o", "owned_by": "openai"},
                {"id": "whisper-1", "owned_by": "openai"},
                {"id": "dall-e-3", "owned_by": "openai"},
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            models = await validator.get_available_models("valid-key")

        assert len(models) == 2  # gpt-4o and whisper-1 match filter
        assert models[0]["id"] == "gpt-4o"


class TestAnthropicValidator:
    """Unit tests for Anthropic API key validator."""

    @pytest.fixture
    def validator(self) -> AnthropicValidator:
        return AnthropicValidator()

    @pytest.mark.asyncio
    async def test_provider_id(self, validator: AnthropicValidator):
        assert validator.provider_id == "anthropic"

    @pytest.mark.asyncio
    async def test_validate_success(self, validator: AnthropicValidator):
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await validator.validate("valid-key")

        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_invalid_key(self, validator: AnthropicValidator):
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await validator.validate("invalid-key")

        assert result.is_valid is False
        assert result.error_message == "Invalid API key"

    @pytest.mark.asyncio
    async def test_validate_rate_limited(self, validator: AnthropicValidator):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await validator.validate("key")

        assert result.is_valid is False
        assert "Rate limited" in (result.error_message or "")

    @pytest.mark.asyncio
    async def test_validate_timeout(self, validator: AnthropicValidator):
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("timeout")
            )
            result = await validator.validate("key")

        assert result.is_valid is False
        assert result.error_message == "Request timed out"

    @pytest.mark.asyncio
    async def test_validate_network_error(self, validator: AnthropicValidator):
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.RequestError("connection failed", request=MagicMock())
            )
            result = await validator.validate("key")

        assert result.is_valid is False
        assert "Network error" in (result.error_message or "")

    @pytest.mark.asyncio
    async def test_get_available_models(self, validator: AnthropicValidator):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": "claude-3-5-sonnet-latest",
                    "display_name": "Claude 3.5 Sonnet",
                    "type": "model",
                },
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            models = await validator.get_available_models("valid-key")

        assert len(models) == 1
        assert models[0]["id"] == "claude-3-5-sonnet-latest"


class TestGCPValidator:
    """Unit tests for GCP API key validator."""

    @pytest.fixture
    def validator(self) -> GCPValidator:
        return GCPValidator()

    @pytest.mark.asyncio
    async def test_provider_id(self, validator: GCPValidator):
        assert validator.provider_id == "gcp"

    @pytest.mark.asyncio
    async def test_validate_success(self, validator: GCPValidator):
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await validator.validate("valid-key")

        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_invalid_key(self, validator: GCPValidator):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": {"message": "API key not valid"}}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await validator.validate("invalid-key")

        assert result.is_valid is False
        assert "API key not valid" in (result.error_message or "")

    @pytest.mark.asyncio
    async def test_validate_forbidden(self, validator: GCPValidator):
        mock_response = MagicMock()
        mock_response.status_code = 403

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await validator.validate("key")

        assert result.is_valid is False
        assert "forbidden" in (result.error_message or "").lower()

    @pytest.mark.asyncio
    async def test_validate_rate_limited(self, validator: GCPValidator):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "10"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await validator.validate("key")

        assert result.is_valid is False
        assert "Rate limited" in (result.error_message or "")

    @pytest.mark.asyncio
    async def test_validate_timeout(self, validator: GCPValidator):
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("timeout")
            )
            result = await validator.validate("key")

        assert result.is_valid is False
        assert result.error_message == "Request timed out"

    @pytest.mark.asyncio
    async def test_validate_network_error(self, validator: GCPValidator):
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.RequestError("connection failed", request=MagicMock())
            )
            result = await validator.validate("key")

        assert result.is_valid is False
        assert "Network error" in (result.error_message or "")

    @pytest.mark.asyncio
    async def test_get_available_models(self, validator: GCPValidator):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "voices": [
                {
                    "name": "en-US-Wavenet-A",
                    "languageCodes": ["en-US"],
                    "ssmlGender": "MALE",
                    "naturalSampleRateHertz": 24000,
                },
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            models = await validator.get_available_models("valid-key")

        assert len(models) == 1
        assert models[0]["id"] == "en-US-Wavenet-A"


class TestVoAIValidator:
    """Unit tests for VoAI API key validator."""

    @pytest.fixture
    def validator(self) -> VoAIValidator:
        return VoAIValidator()

    @pytest.mark.asyncio
    async def test_provider_id(self, validator: VoAIValidator):
        assert validator.provider_id == "voai"

    @pytest.mark.asyncio
    async def test_validate_success(self, validator: VoAIValidator):
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await validator.validate("valid-key")

        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_invalid_key(self, validator: VoAIValidator):
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await validator.validate("invalid-key")

        assert result.is_valid is False
        assert result.error_message == "Invalid API key"

    @pytest.mark.asyncio
    async def test_validate_rate_limited(self, validator: VoAIValidator):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "15"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await validator.validate("key")

        assert result.is_valid is False
        assert "Rate limited" in (result.error_message or "")

    @pytest.mark.asyncio
    async def test_validate_timeout(self, validator: VoAIValidator):
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("timeout")
            )
            result = await validator.validate("key")

        assert result.is_valid is False
        assert result.error_message == "Request timed out"

    @pytest.mark.asyncio
    async def test_validate_network_error(self, validator: VoAIValidator):
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.RequestError("connection failed", request=MagicMock())
            )
            result = await validator.validate("key")

        assert result.is_valid is False
        assert "Network error" in (result.error_message or "")

    @pytest.mark.asyncio
    async def test_get_available_models(self, validator: VoAIValidator):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "voices": [
                {"id": "voice-1", "name": "Voice 1", "language": "zh-TW", "gender": "female"},
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            models = await validator.get_available_models("valid-key")

        assert len(models) == 1
        assert models[0]["id"] == "voice-1"


class TestSpeechmaticsValidator:
    """Unit tests for Speechmatics API key validator."""

    @pytest.fixture
    def validator(self) -> SpeechmaticsValidator:
        return SpeechmaticsValidator()

    @pytest.mark.asyncio
    async def test_provider_id(self, validator: SpeechmaticsValidator):
        assert validator.provider_id == "speechmatics"

    @pytest.mark.asyncio
    async def test_validate_success(self, validator: SpeechmaticsValidator):
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await validator.validate("valid-key")

        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_invalid_key(self, validator: SpeechmaticsValidator):
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await validator.validate("invalid-key")

        assert result.is_valid is False
        assert result.error_message == "Invalid API key"

    @pytest.mark.asyncio
    async def test_validate_forbidden(self, validator: SpeechmaticsValidator):
        mock_response = MagicMock()
        mock_response.status_code = 403

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await validator.validate("key")

        assert result.is_valid is False
        assert "forbidden" in (result.error_message or "").lower()

    @pytest.mark.asyncio
    async def test_validate_rate_limited(self, validator: SpeechmaticsValidator):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "5"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await validator.validate("key")

        assert result.is_valid is False
        assert "Rate limited" in (result.error_message or "")

    @pytest.mark.asyncio
    async def test_validate_timeout(self, validator: SpeechmaticsValidator):
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("timeout")
            )
            result = await validator.validate("key")

        assert result.is_valid is False
        assert result.error_message == "Request timed out"

    @pytest.mark.asyncio
    async def test_validate_network_error(self, validator: SpeechmaticsValidator):
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.RequestError("connection failed", request=MagicMock())
            )
            result = await validator.validate("key")

        assert result.is_valid is False
        assert "Network error" in (result.error_message or "")

    @pytest.mark.asyncio
    async def test_get_available_models(self, validator: SpeechmaticsValidator):
        models = await validator.get_available_models("any-key")

        assert len(models) == 2
        assert models[0]["id"] == "enhanced"
        assert models[1]["id"] == "standard"
