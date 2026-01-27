"""Contract tests for STT Providers API endpoint.

Feature: 003-stt-testing-module
T024: Contract test for GET /stt/providers endpoint

Tests the provider listing endpoint returns correct schema and data.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from src.infrastructure.persistence.database import get_db_session
from src.main import app
from src.presentation.api.dependencies import get_stt_providers
from src.presentation.api.middleware.auth import CurrentUser, get_current_user


# Test user for authentication
TEST_USER_ID = uuid.UUID("12345678-1234-5678-1234-567812345678")
TEST_USER = CurrentUser(
    id=str(TEST_USER_ID),
    email="test@example.com",
    name="Test User",
    picture_url=None,
    google_id="google-test-id-12345",
)


class TestListProvidersEndpoint:
    """Contract tests for GET /api/v1/stt/providers endpoint."""

    @pytest.fixture(autouse=True)
    def setup_dependencies(self):
        """Override database, auth, and provider dependencies."""
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.flush = AsyncMock()

        # Mock the execute result to return empty credentials
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute = AsyncMock(return_value=mock_result)

        async def get_mock_session():
            yield mock_session

        async def get_mock_user():
            return TEST_USER

        app.dependency_overrides[get_db_session] = get_mock_session
        app.dependency_overrides[get_current_user] = get_mock_user
        yield
        app.dependency_overrides.clear()

    @pytest.fixture
    def mock_stt_provider(self):
        """Create a mock STT provider."""
        provider = MagicMock()
        provider.name = "azure"
        provider.supports_streaming = True
        return provider

    @pytest.mark.asyncio
    async def test_list_providers_success(self, mock_stt_provider):
        """T024: Test successful provider listing with all required fields."""
        # Mock providers dictionary
        mock_providers = {
            "azure": mock_stt_provider,
        }

        app.dependency_overrides[get_stt_providers] = lambda: mock_providers

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/stt/providers")

            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert "providers" in data
            assert isinstance(data["providers"], list)
            assert len(data["providers"]) >= 1

            # Verify provider schema for azure
            azure_provider = next((p for p in data["providers"] if p["name"] == "azure"), None)
            assert azure_provider is not None

            # Required fields per frontend STTProvider type
            assert "name" in azure_provider
            assert "display_name" in azure_provider
            assert "supports_streaming" in azure_provider
            assert "supports_child_mode" in azure_provider
            assert "max_duration_sec" in azure_provider
            assert "max_file_size_mb" in azure_provider
            assert "supported_formats" in azure_provider
            assert "supported_languages" in azure_provider

            # Verify types
            assert isinstance(azure_provider["name"], str)
            assert isinstance(azure_provider["display_name"], str)
            assert isinstance(azure_provider["supports_streaming"], bool)
            assert isinstance(azure_provider["supports_child_mode"], bool)
            assert isinstance(azure_provider["max_duration_sec"], int)
            assert isinstance(azure_provider["max_file_size_mb"], int)
            assert isinstance(azure_provider["supported_formats"], list)
            assert isinstance(azure_provider["supported_languages"], list)
        finally:
            app.dependency_overrides.pop(get_stt_providers, None)

    @pytest.mark.asyncio
    async def test_list_providers_multiple(self):
        """T024: Test listing multiple providers."""
        # Create mock providers
        mock_azure = MagicMock()
        mock_azure.name = "azure"
        mock_azure.supports_streaming = True

        mock_gcp = MagicMock()
        mock_gcp.name = "gcp"
        mock_gcp.supports_streaming = True

        mock_whisper = MagicMock()
        mock_whisper.name = "whisper"
        mock_whisper.supports_streaming = False

        mock_providers = {
            "azure": mock_azure,
            "gcp": mock_gcp,
            "whisper": mock_whisper,
        }

        app.dependency_overrides[get_stt_providers] = lambda: mock_providers

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/stt/providers")

            assert response.status_code == 200
            data = response.json()

            assert len(data["providers"]) == 3

            provider_names = [p["name"] for p in data["providers"]]
            assert "azure" in provider_names
            assert "gcp" in provider_names
            assert "whisper" in provider_names
        finally:
            app.dependency_overrides.pop(get_stt_providers, None)

    @pytest.mark.asyncio
    async def test_list_providers_empty(self):
        """T024: Test listing when no providers are configured."""
        app.dependency_overrides[get_stt_providers] = lambda: {}

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/stt/providers")

            assert response.status_code == 200
            data = response.json()

            assert "providers" in data
            assert data["providers"] == []
        finally:
            app.dependency_overrides.pop(get_stt_providers, None)

    @pytest.mark.asyncio
    async def test_list_providers_azure_capabilities(self, mock_stt_provider):
        """T024: Verify Azure provider has correct capabilities."""
        mock_providers = {"azure": mock_stt_provider}
        app.dependency_overrides[get_stt_providers] = lambda: mock_providers

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/stt/providers")

            assert response.status_code == 200
            data = response.json()

            azure = data["providers"][0]
            assert azure["name"] == "azure"
            assert azure["display_name"] == "Azure Speech Services"
            assert azure["supports_streaming"] is True
            assert azure["supports_child_mode"] is True
            assert azure["max_file_size_mb"] == 200
            assert "mp3" in azure["supported_formats"]
            assert "wav" in azure["supported_formats"]
            assert "zh-TW" in azure["supported_languages"]
        finally:
            app.dependency_overrides.pop(get_stt_providers, None)

    @pytest.mark.asyncio
    async def test_list_providers_whisper_capabilities(self):
        """T024: Verify Whisper provider has correct capabilities (batch only)."""
        mock_whisper = MagicMock()
        mock_whisper.name = "whisper"
        mock_whisper.supports_streaming = False

        mock_providers = {"whisper": mock_whisper}
        app.dependency_overrides[get_stt_providers] = lambda: mock_providers

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/stt/providers")

            assert response.status_code == 200
            data = response.json()

            whisper = data["providers"][0]
            assert whisper["name"] == "whisper"
            assert whisper["display_name"] == "OpenAI Whisper"
            assert whisper["supports_streaming"] is False
            assert whisper["supports_child_mode"] is False
            assert whisper["max_file_size_mb"] == 25  # Whisper limit
        finally:
            app.dependency_overrides.pop(get_stt_providers, None)
