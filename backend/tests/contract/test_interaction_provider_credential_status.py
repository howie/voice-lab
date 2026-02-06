"""Contract tests for interaction provider credential status logic.

Regression tests ensuring that providers initialized via system env vars
default to has_credentials=True, is_valid=True in the interaction module's
GET /api/v1/interaction/providers endpoint.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from src.domain.entities.provider_credential import UserProviderCredential
from src.infrastructure.persistence.database import get_db_session
from src.main import app
from src.presentation.api.dependencies import Container, get_container
from src.presentation.api.middleware.auth import CurrentUser, get_current_user

TEST_USER_ID = uuid.UUID("12345678-1234-5678-1234-567812345678")
TEST_USER = CurrentUser(
    id=str(TEST_USER_ID),
    email="test@example.com",
    name="Test User",
    picture_url=None,
    google_id="google-test-id-12345",
)


def _make_mock_session(credentials: list[UserProviderCredential] | None = None):
    """Create a mock DB session that returns the given credentials."""
    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.flush = AsyncMock()

    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = credentials or []
    mock_result.scalars.return_value = mock_scalars
    mock_session.execute = AsyncMock(return_value=mock_result)
    return mock_session


def _make_mock_container(
    stt_names: list[str] | None = None,
    llm_names: list[str] | None = None,
    tts_names: list[str] | None = None,
):
    """Create a mock Container that returns providers with the given names."""
    container = MagicMock(spec=Container)

    def _providers(names):
        result = {}
        for name in names or []:
            p = MagicMock()
            p.name = name
            result[name] = p
        return result

    container.get_stt_providers.return_value = _providers(stt_names)
    container.get_llm_providers.return_value = _providers(llm_names)
    container.get_tts_providers.return_value = _providers(tts_names)
    return container


class TestInteractionProviderCredentialStatus:
    """Tests for credential status on GET /api/v1/interaction/providers."""

    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Override auth dependency."""

        async def get_mock_user():
            return TEST_USER

        app.dependency_overrides[get_current_user] = get_mock_user
        yield
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_providers_without_user_creds_default_to_valid(self):
        """All system-initialized providers should default to
        has_credentials=True, is_valid=True when no user DB credentials exist."""
        mock_session = _make_mock_session(credentials=[])
        mock_container = _make_mock_container(
            stt_names=["azure", "whisper"],
            llm_names=["openai"],
            tts_names=["azure", "elevenlabs"],
        )

        async def get_mock_session():
            yield mock_session

        app.dependency_overrides[get_db_session] = get_mock_session
        app.dependency_overrides[get_container] = lambda: mock_container

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/interaction/providers")

            assert response.status_code == 200
            data = response.json()

            # Check all STT providers
            for provider in data["stt_providers"]:
                assert provider["has_credentials"] is True, (
                    f"STT provider {provider['name']} should have has_credentials=True"
                )
                assert provider["is_valid"] is True, (
                    f"STT provider {provider['name']} should have is_valid=True"
                )

            # Check all LLM providers
            for provider in data["llm_providers"]:
                assert provider["has_credentials"] is True, (
                    f"LLM provider {provider['name']} should have has_credentials=True"
                )
                assert provider["is_valid"] is True, (
                    f"LLM provider {provider['name']} should have is_valid=True"
                )

            # Check all TTS providers
            for provider in data["tts_providers"]:
                assert provider["has_credentials"] is True, (
                    f"TTS provider {provider['name']} should have has_credentials=True"
                )
                assert provider["is_valid"] is True, (
                    f"TTS provider {provider['name']} should have is_valid=True"
                )
        finally:
            app.dependency_overrides.pop(get_db_session, None)
            app.dependency_overrides.pop(get_container, None)

    @pytest.mark.asyncio
    async def test_invalid_user_creds_override_defaults(self):
        """When user has invalid credentials in DB, the response should
        reflect has_credentials=True, is_valid=False for that provider."""
        invalid_cred = UserProviderCredential(
            id=uuid.uuid4(),
            user_id=TEST_USER_ID,
            provider="openai",
            api_key="expired-key",
            is_valid=False,
        )
        mock_session = _make_mock_session(credentials=[invalid_cred])
        mock_container = _make_mock_container(
            stt_names=["whisper"],
            llm_names=["openai"],
            tts_names=[],
        )

        async def get_mock_session():
            yield mock_session

        app.dependency_overrides[get_db_session] = get_mock_session
        app.dependency_overrides[get_container] = lambda: mock_container

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/interaction/providers")

            assert response.status_code == 200
            data = response.json()

            # Whisper maps to openai, so it should pick up the invalid cred
            whisper = next(p for p in data["stt_providers"] if p["name"] == "whisper")
            assert whisper["has_credentials"] is True
            assert whisper["is_valid"] is False

            # OpenAI LLM should also reflect the invalid cred
            openai_llm = next(p for p in data["llm_providers"] if p["name"] == "openai")
            assert openai_llm["has_credentials"] is True
            assert openai_llm["is_valid"] is False
        finally:
            app.dependency_overrides.pop(get_db_session, None)
            app.dependency_overrides.pop(get_container, None)

    @pytest.mark.asyncio
    async def test_mixed_cred_status(self):
        """Some providers with user creds, some without — verify correct
        default behavior for each case."""
        azure_cred = UserProviderCredential(
            id=uuid.uuid4(),
            user_id=TEST_USER_ID,
            provider="azure",
            api_key="valid-azure-key",
            is_valid=True,
        )
        mock_session = _make_mock_session(credentials=[azure_cred])
        mock_container = _make_mock_container(
            stt_names=["azure", "gcp"],
            llm_names=[],
            tts_names=[],
        )

        async def get_mock_session():
            yield mock_session

        app.dependency_overrides[get_db_session] = get_mock_session
        app.dependency_overrides[get_container] = lambda: mock_container

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/interaction/providers")

            assert response.status_code == 200
            data = response.json()

            # Azure has user creds -> should use those
            azure = next(p for p in data["stt_providers"] if p["name"] == "azure")
            assert azure["has_credentials"] is True
            assert azure["is_valid"] is True

            # GCP has no user creds -> should default to system valid
            gcp = next(p for p in data["stt_providers"] if p["name"] == "gcp")
            assert gcp["has_credentials"] is True
            assert gcp["is_valid"] is True
        finally:
            app.dependency_overrides.pop(get_db_session, None)
            app.dependency_overrides.pop(get_container, None)
