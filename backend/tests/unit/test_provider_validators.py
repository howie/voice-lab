"""Unit tests for Provider Validators.

T024: Unit tests for provider API key validators.
Tests validation logic, error handling, and model listing.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.infrastructure.providers.validators.azure import AzureValidator
from src.infrastructure.providers.validators.base import ValidationResult
from src.infrastructure.providers.validators.elevenlabs import ElevenLabsValidator
from src.infrastructure.providers.validators.gemini import GeminiValidator


class TestElevenLabsValidator:
    """Unit tests for ElevenLabs API key validator."""

    @pytest.fixture
    def validator(self) -> ElevenLabsValidator:
        """Create an ElevenLabs validator instance."""
        return ElevenLabsValidator()

    @pytest.mark.asyncio
    async def test_provider_id(self, validator: ElevenLabsValidator):
        """Test that provider_id returns correct value."""
        assert validator.provider_id == "elevenlabs"

    @pytest.mark.asyncio
    async def test_validate_success(self, validator: ElevenLabsValidator):
        """Test successful API key validation."""
        # Use MagicMock for response since .json() is sync in httpx
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "subscription": {
                "character_count": 1000,
                "character_limit": 10000,
            }
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await validator.validate("valid-api-key")

        assert result.is_valid is True
        assert result.error_message is None
        assert result.quota_info is not None
        assert result.quota_info["character_count"] == 1000
        assert result.quota_info["character_limit"] == 10000

    @pytest.mark.asyncio
    async def test_validate_invalid_key(self, validator: ElevenLabsValidator):
        """Test validation with invalid API key."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await validator.validate("invalid-api-key")

        assert result.is_valid is False
        assert result.error_message == "Invalid API key"

    @pytest.mark.asyncio
    async def test_validate_timeout(self, validator: ElevenLabsValidator):
        """Test validation when request times out."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("Connection timed out")
            )
            result = await validator.validate("api-key")

        assert result.is_valid is False
        assert "timed out" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_validate_network_error(self, validator: ElevenLabsValidator):
        """Test validation when network error occurs."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.RequestError("Network error")
            )
            result = await validator.validate("api-key")

        assert result.is_valid is False
        assert "network" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_get_available_models_success(self, validator: ElevenLabsValidator):
        """Test getting available voices."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "voices": [
                {
                    "voice_id": "voice1",
                    "name": "Rachel",
                    "labels": {"language": "en", "gender": "female"},
                    "description": "Warm voice",
                },
                {
                    "voice_id": "voice2",
                    "name": "Adam",
                    "labels": {"language": "en", "gender": "male"},
                    "description": "Deep voice",
                },
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            models = await validator.get_available_models("valid-api-key")

        assert len(models) == 2
        assert models[0]["id"] == "voice1"
        assert models[0]["name"] == "Rachel"
        assert models[0]["gender"] == "female"
        assert models[1]["id"] == "voice2"
        assert models[1]["name"] == "Adam"

    @pytest.mark.asyncio
    async def test_get_available_models_error(self, validator: ElevenLabsValidator):
        """Test getting models when API fails."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.RequestError("Network error")
            )
            models = await validator.get_available_models("api-key")

        assert models == []


class TestAzureValidator:
    """Unit tests for Azure Cognitive Services API key validator."""

    @pytest.fixture
    def validator(self) -> AzureValidator:
        """Create an Azure validator instance."""
        return AzureValidator()

    @pytest.mark.asyncio
    async def test_provider_id(self, validator: AzureValidator):
        """Test that provider_id returns correct value."""
        assert validator.provider_id == "azure"

    @pytest.mark.asyncio
    async def test_validate_success(self, validator: AzureValidator):
        """Test successful API key validation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"Name": "en-US-JennyNeural", "Gender": "Female"}]

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await validator.validate("valid-azure-key")

        assert result.is_valid is True
        assert result.error_message is None

    @pytest.mark.asyncio
    async def test_validate_invalid_key(self, validator: AzureValidator):
        """Test validation with invalid API key."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await validator.validate("invalid-azure-key")

        assert result.is_valid is False
        assert "invalid" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_get_available_models_success(self, validator: AzureValidator):
        """Test getting available voices from Azure."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "ShortName": "en-US-JennyNeural",
                "DisplayName": "Jenny",
                "LocaleName": "English (United States)",
                "Gender": "Female",
            },
            {
                "ShortName": "zh-TW-HsiaoChenNeural",
                "DisplayName": "HsiaoChen",
                "LocaleName": "Chinese (Traditional, Taiwan)",
                "Gender": "Female",
            },
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            models = await validator.get_available_models("valid-azure-key")

        assert len(models) == 2
        assert models[0]["id"] == "en-US-JennyNeural"
        assert models[0]["name"] == "Jenny"
        assert models[1]["id"] == "zh-TW-HsiaoChenNeural"


class TestGeminiValidator:
    """Unit tests for Google Gemini API key validator."""

    @pytest.fixture
    def validator(self) -> GeminiValidator:
        """Create a Gemini validator instance."""
        return GeminiValidator()

    @pytest.mark.asyncio
    async def test_provider_id(self, validator: GeminiValidator):
        """Test that provider_id returns correct value."""
        assert validator.provider_id == "gemini"

    @pytest.mark.asyncio
    async def test_validate_success(self, validator: GeminiValidator):
        """Test successful API key validation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"models": [{"name": "gemini-pro"}]}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await validator.validate("valid-gemini-key")

        assert result.is_valid is True
        assert result.error_message is None

    @pytest.mark.asyncio
    async def test_validate_invalid_key(self, validator: GeminiValidator):
        """Test validation with invalid API key."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": {"message": "Invalid API key"}}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            result = await validator.validate("invalid-gemini-key")

        assert result.is_valid is False


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_valid_result(self):
        """Test creating a valid result."""
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        assert result.error_message is None
        assert result.quota_info is None

    def test_invalid_result_with_error(self):
        """Test creating an invalid result with error message."""
        result = ValidationResult(
            is_valid=False,
            error_message="API key expired",
        )
        assert result.is_valid is False
        assert result.error_message == "API key expired"

    def test_valid_result_with_quota(self):
        """Test creating a valid result with quota info."""
        quota = {"used": 100, "limit": 1000}
        result = ValidationResult(
            is_valid=True,
            quota_info=quota,
        )
        assert result.is_valid is True
        assert result.quota_info == quota
