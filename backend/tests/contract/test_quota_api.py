"""Contract tests for the Quota Dashboard API endpoint.

Tests the GET /api/v1/quota endpoint, verifying response schema,
tracked usage integration, and provider credential detection.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.domain.services.usage_tracker import ProviderUsageTracker
from src.infrastructure.persistence.database import get_db_session
from src.main import app
from src.presentation.api.middleware.auth import CurrentUser, get_current_user


@pytest.fixture()
def mock_user_id() -> uuid.UUID:
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture()
def mock_current_user(mock_user_id: uuid.UUID) -> CurrentUser:
    return CurrentUser(
        id=str(mock_user_id),
        email="test@example.com",
        name="Test User",
        picture_url=None,
        google_id="google-123",
    )


def _make_credential(provider: str, *, is_valid: bool = True) -> MagicMock:
    """Create a mock UserProviderCredential."""
    cred = MagicMock()
    cred.provider = provider
    cred.is_valid = is_valid
    cred.api_key = "sk-test-key"
    cred.last_validated_at = datetime.now(UTC)
    return cred


class TestQuotaDashboardEndpoint:
    """Contract tests for GET /api/v1/quota."""

    @pytest.fixture(autouse=True)
    def override_dependencies(self, mock_current_user: CurrentUser):
        """Override auth and DB dependencies."""
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()

        async def get_mock_user() -> CurrentUser:
            return mock_current_user

        async def get_mock_session():
            yield mock_session

        app.dependency_overrides[get_current_user] = get_mock_user
        app.dependency_overrides[get_db_session] = get_mock_session
        yield mock_session
        app.dependency_overrides.clear()

    @pytest.mark.asyncio()
    async def test_returns_200_with_valid_schema(self) -> None:
        """Quota endpoint returns proper dashboard structure."""
        with patch(
            "src.presentation.api.routes.quota.SQLAlchemyProviderCredentialRepository"
        ) as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.list_by_user.return_value = []
            mock_repo_cls.return_value = mock_repo

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/quota")

        assert response.status_code == 200
        data = response.json()

        # Top-level fields
        assert "providers" in data
        assert "app_rate_limits" in data
        assert "fetched_at" in data

        # App rate limits structure
        limits = data["app_rate_limits"]
        assert "general_rpm" in limits
        assert "general_rph" in limits
        assert "tts_rpm" in limits
        assert "tts_rph" in limits
        assert "general_minute_remaining" in limits
        assert "tts_minute_remaining" in limits

    @pytest.mark.asyncio()
    async def test_includes_all_supported_providers(self) -> None:
        """Response should include all registered providers."""
        with patch(
            "src.presentation.api.routes.quota.SQLAlchemyProviderCredentialRepository"
        ) as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.list_by_user.return_value = []
            mock_repo_cls.return_value = mock_repo

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/quota")

        data = response.json()
        provider_ids = [p["provider"] for p in data["providers"]]

        # All registered providers should be included
        assert "gemini" in provider_ids
        assert "elevenlabs" in provider_ids
        assert "azure" in provider_ids

    @pytest.mark.asyncio()
    async def test_provider_status_schema(self) -> None:
        """Each provider status should have the required fields."""
        with patch(
            "src.presentation.api.routes.quota.SQLAlchemyProviderCredentialRepository"
        ) as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.list_by_user.return_value = []
            mock_repo_cls.return_value = mock_repo

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/quota")

        data = response.json()
        for provider_status in data["providers"]:
            assert "provider" in provider_status
            assert "display_name" in provider_status
            assert "has_credential" in provider_status
            assert "minute_requests" in provider_status
            assert "hour_requests" in provider_status
            assert "day_requests" in provider_status
            assert "quota_hits_today" in provider_status
            assert "suggestions" in provider_status

    @pytest.mark.asyncio()
    async def test_credential_detection(self) -> None:
        """Providers with stored credentials should be marked accordingly."""
        gemini_cred = _make_credential("gemini", is_valid=True)

        with patch(
            "src.presentation.api.routes.quota.SQLAlchemyProviderCredentialRepository"
        ) as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.list_by_user.return_value = [gemini_cred]
            mock_repo_cls.return_value = mock_repo

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/quota")

        data = response.json()
        providers_map = {p["provider"]: p for p in data["providers"]}

        assert providers_map["gemini"]["has_credential"] is True
        assert providers_map["gemini"]["is_valid"] is True
        # A provider without credentials
        assert providers_map["azure"]["has_credential"] is False

    @pytest.mark.asyncio()
    async def test_tracked_usage_appears_in_response(self, mock_user_id: uuid.UUID) -> None:
        """In-memory tracked usage should be reflected in provider status."""
        fresh_tracker = ProviderUsageTracker()
        uid = str(mock_user_id)

        # Simulate some usage
        for _ in range(5):
            fresh_tracker.record_request(uid, "gemini")
        fresh_tracker.record_error(uid, "gemini", is_quota_error=True, retry_after=60)

        with (
            patch(
                "src.presentation.api.routes.quota.SQLAlchemyProviderCredentialRepository"
            ) as mock_repo_cls,
            patch(
                "src.presentation.api.routes.quota.provider_usage_tracker",
                fresh_tracker,
            ),
        ):
            mock_repo = AsyncMock()
            mock_repo.list_by_user.return_value = []
            mock_repo_cls.return_value = mock_repo

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/quota")

        data = response.json()
        providers_map = {p["provider"]: p for p in data["providers"]}

        gemini = providers_map["gemini"]
        assert gemini["minute_requests"] == 5
        assert gemini["hour_requests"] == 5
        assert gemini["day_requests"] == 5
        assert gemini["quota_hits_today"] == 1

    @pytest.mark.asyncio()
    async def test_gemini_has_rate_limit_reference(self) -> None:
        """Gemini should include known rate limit reference data."""
        with patch(
            "src.presentation.api.routes.quota.SQLAlchemyProviderCredentialRepository"
        ) as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.list_by_user.return_value = []
            mock_repo_cls.return_value = mock_repo

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/quota")

        data = response.json()
        providers_map = {p["provider"]: p for p in data["providers"]}

        gemini = providers_map["gemini"]
        assert gemini["rate_limits"] is not None
        assert gemini["rate_limits"]["free_rpm"] == 10
        assert gemini["rate_limits"]["tier1_rpm"] == 300

    @pytest.mark.asyncio()
    async def test_provider_without_usage_shows_zeros(self) -> None:
        """Providers with no tracked usage should show zero counts."""
        with patch(
            "src.presentation.api.routes.quota.SQLAlchemyProviderCredentialRepository"
        ) as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.list_by_user.return_value = []
            mock_repo_cls.return_value = mock_repo

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/quota")

        data = response.json()
        providers_map = {p["provider"]: p for p in data["providers"]}

        azure = providers_map["azure"]
        assert azure["minute_requests"] == 0
        assert azure["hour_requests"] == 0
        assert azure["day_requests"] == 0
        assert azure["quota_hits_today"] == 0

    @pytest.mark.asyncio()
    async def test_elevenlabs_quota_fetched_when_credential_valid(self) -> None:
        """ElevenLabs quota should be fetched when a valid credential exists."""
        elevenlabs_cred = _make_credential("elevenlabs", is_valid=True)

        mock_quota_data = {
            "character_count": 5000,
            "character_limit": 10000,
            "tier": "starter",
        }

        with (
            patch(
                "src.presentation.api.routes.quota.SQLAlchemyProviderCredentialRepository"
            ) as mock_repo_cls,
            patch(
                "src.presentation.api.routes.quota._fetch_provider_quota",
                return_value=mock_quota_data,
            ),
        ):
            mock_repo = AsyncMock()
            mock_repo.list_by_user.return_value = [elevenlabs_cred]
            mock_repo_cls.return_value = mock_repo

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/quota")

        data = response.json()
        providers_map = {p["provider"]: p for p in data["providers"]}

        elevenlabs = providers_map["elevenlabs"]
        assert elevenlabs["character_count"] == 5000
        assert elevenlabs["character_limit"] == 10000
        assert elevenlabs["usage_percent"] == 50.0
        assert elevenlabs["remaining_characters"] == 5000
        assert elevenlabs["tier"] == "starter"

    @pytest.mark.asyncio()
    async def test_help_url_and_suggestions_present(self) -> None:
        """Providers should include help URLs and suggestions."""
        with patch(
            "src.presentation.api.routes.quota.SQLAlchemyProviderCredentialRepository"
        ) as mock_repo_cls:
            mock_repo = AsyncMock()
            mock_repo.list_by_user.return_value = []
            mock_repo_cls.return_value = mock_repo

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/quota")

        data = response.json()
        providers_map = {p["provider"]: p for p in data["providers"]}

        gemini = providers_map["gemini"]
        assert gemini["help_url"] is not None
        assert len(gemini["suggestions"]) > 0
