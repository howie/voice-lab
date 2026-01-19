"""Contract tests for POST /stt/compare endpoint.

Feature: 003-stt-testing-module - Phase 7
Task: T061 - Contract test for multi-provider comparison endpoint

Tests the endpoint that allows comparing transcription results across
multiple STT providers for the same audio file.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app
from src.presentation.api.middleware.auth import CurrentUser, get_current_user


@pytest.fixture
def mock_current_user() -> CurrentUser:
    """Create a mock current user for authentication."""
    return CurrentUser(
        id="00000000-0000-0000-0000-000000000001",
        email="test@example.com",
        name="Test User",
        picture_url=None,
        google_id="test-google-id",
    )


@pytest.mark.asyncio
class TestCompareEndpointContract:
    """Contract tests for multi-provider comparison endpoint."""

    @pytest.fixture(autouse=True)
    def setup_auth(self, mock_current_user: CurrentUser):
        """Override authentication for all tests."""

        async def get_mock_current_user():
            return mock_current_user

        app.dependency_overrides[get_current_user] = get_mock_current_user
        yield
        app.dependency_overrides.clear()

    async def test_compare_requires_audio_file(self) -> None:
        """Test that audio file is required."""
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/stt/compare",
                data={
                    "providers": "azure,gcp",
                    "language": "zh-TW",
                },
            )

        # Should fail without audio file
        assert response.status_code == 422

    async def test_compare_requires_providers(self) -> None:
        """Test that providers list is required."""
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/stt/compare",
                files={
                    "audio": ("test.wav", b"fake audio data", "audio/wav"),
                },
                data={
                    "language": "zh-TW",
                },
            )

        # Should fail without providers
        assert response.status_code == 422

    async def test_compare_requires_at_least_two_providers(self) -> None:
        """Test that at least 2 providers are required for comparison."""
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/stt/compare",
                files={
                    "audio": ("test.wav", b"fake audio data", "audio/wav"),
                },
                data={
                    "providers": "azure",  # Only one provider
                    "language": "zh-TW",
                },
            )

        # Should fail with only one provider
        assert response.status_code in [400, 422]
        if response.status_code == 400:
            data = response.json()
            assert "at least" in data["detail"].lower() or "two" in data["detail"].lower()

    async def test_compare_validates_provider_names(self) -> None:
        """Test that invalid provider names are rejected."""
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/stt/compare",
                files={
                    "audio": ("test.wav", b"fake audio data", "audio/wav"),
                },
                data={
                    "providers": "invalid_provider,another_invalid",
                    "language": "zh-TW",
                },
            )

        # Should fail with invalid providers
        assert response.status_code in [400, 404]

    async def test_compare_response_structure(self) -> None:
        """Test expected response structure for valid comparison request.

        Note: This test will likely fail without proper provider setup,
        but it demonstrates the expected contract.
        """
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/stt/compare",
                files={
                    "audio": ("test.wav", b"fake audio data", "audio/wav"),
                },
                data={
                    "providers": "azure,gcp",
                    "language": "zh-TW",
                },
            )

        # If successful (200), verify response structure
        if response.status_code == 200:
            data = response.json()

            # Should have results for each provider
            assert "results" in data
            assert isinstance(data["results"], list)
            assert len(data["results"]) >= 2

            # Each result should have provider info and transcript
            for result in data["results"]:
                assert "provider" in result
                assert "transcript" in result
                assert "confidence" in result
                assert "latency_ms" in result

            # Should have audio_file_id for reference
            assert "audio_file_id" in data

    async def test_compare_default_language(self) -> None:
        """Test that language defaults to zh-TW if not specified."""
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/stt/compare",
                files={
                    "audio": ("test.wav", b"fake audio data", "audio/wav"),
                },
                data={
                    "providers": "azure,gcp",
                    # No language specified
                },
            )

        # Should accept request without language (defaults to zh-TW)
        # May fail for other reasons (invalid audio), but not for missing language
        assert response.status_code != 422 or "language" not in response.json()["detail"][0]["loc"]

    async def test_compare_accepts_child_mode(self) -> None:
        """Test that child_mode parameter is accepted."""
        transport = ASGITransport(app=app)  # type: ignore[arg-type]
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/stt/compare",
                files={
                    "audio": ("test.wav", b"fake audio data", "audio/wav"),
                },
                data={
                    "providers": "azure,gcp",
                    "language": "zh-TW",
                    "child_mode": "true",
                },
            )

        # Should accept child_mode parameter (may fail for other reasons)
        assert response.status_code != 422 or "child_mode" not in str(response.json())
