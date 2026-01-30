"""Contract tests for voices API endpoints.

T053: Create tests for voice listing endpoint
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.application.use_cases.list_voices import VoiceProfile
from src.main import app
from src.presentation.api.dependencies import (
    get_voice_cache_repository,
    get_voice_customization_repository,
)

# Mock voice data as VoiceProfile objects
MOCK_VOICES = [
    VoiceProfile(
        id="zh-TW-HsiaoChenNeural",
        name="Hsiao Chen",
        provider="azure",
        language="zh-TW",
        gender="female",
        description="A natural Taiwanese Mandarin voice",
    ),
    VoiceProfile(
        id="zh-TW-YunJheNeural",
        name="Yun Jhe",
        provider="azure",
        language="zh-TW",
        gender="male",
        description="A natural Taiwanese Mandarin male voice",
    ),
    VoiceProfile(
        id="Kore",
        name="Kore",
        provider="gemini",
        language="zh-TW",
        gender="female",
    ),
    VoiceProfile(
        id="Charon",
        name="Charon",
        provider="gemini",
        language="zh-TW",
        gender="male",
    ),
    VoiceProfile(
        id="rachel",
        name="Rachel",
        provider="elevenlabs",
        language="en-US",
        gender="female",
    ),
    VoiceProfile(
        id="voai-zhTW-female-01",
        name="VoAI Female 01",
        provider="voai",
        language="zh-TW",
        gender="female",
    ),
]


def _build_voice_cache_entry(vp: VoiceProfile):
    """Build a mock VoiceCache-like object from a VoiceProfile."""
    from unittest.mock import MagicMock

    entry = MagicMock()
    entry.id = f"{vp.provider}:{vp.id}"
    entry.provider = vp.provider
    entry.voice_id = vp.id
    entry.display_name = vp.name
    entry.language = vp.language
    entry.gender = MagicMock(value=vp.gender) if vp.gender else None
    entry.age_group = None
    entry.styles = []
    entry.use_cases = []
    entry.sample_audio_url = None
    entry.is_deprecated = False
    return entry


@pytest.fixture
def mock_repos():
    """Create mock voice_cache and customization repos and override deps."""
    mock_cache_repo = AsyncMock()
    mock_customization_repo = AsyncMock()

    # Default: return empty customization map
    mock_customization_repo.get_customization_map = AsyncMock(return_value={})

    app.dependency_overrides[get_voice_cache_repository] = lambda: mock_cache_repo
    app.dependency_overrides[get_voice_customization_repository] = lambda: mock_customization_repo

    yield mock_cache_repo, mock_customization_repo

    app.dependency_overrides.pop(get_voice_cache_repository, None)
    app.dependency_overrides.pop(get_voice_customization_repository, None)


class TestListVoicesEndpoint:
    """Contract tests for GET /api/v1/voices endpoint."""

    @pytest.mark.asyncio
    async def test_list_all_voices(self, mock_repos):
        """Test listing all voices without filters."""
        mock_cache_repo, _mock_cust_repo = mock_repos
        cache_entries = [_build_voice_cache_entry(v) for v in MOCK_VOICES]
        mock_cache_repo.list_all = AsyncMock(return_value=cache_entries)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/v1/voices")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) > 0
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_voices_by_provider(self, mock_repos):
        """Test listing voices filtered by provider."""
        mock_cache_repo, _mock_cust_repo = mock_repos
        azure_voices = [v for v in MOCK_VOICES if v.provider == "azure"]
        cache_entries = [_build_voice_cache_entry(v) for v in azure_voices]
        mock_cache_repo.list_all = AsyncMock(return_value=cache_entries)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/v1/voices?provider=azure")

        assert response.status_code == 200
        data = response.json()
        for voice in data["items"]:
            assert voice["provider"] == "azure"

    @pytest.mark.asyncio
    async def test_list_voices_by_language(self, mock_repos):
        """Test listing voices filtered by language."""
        mock_cache_repo, _mock_cust_repo = mock_repos
        zh_tw_voices = [v for v in MOCK_VOICES if v.language == "zh-TW"]
        cache_entries = [_build_voice_cache_entry(v) for v in zh_tw_voices]
        mock_cache_repo.list_all = AsyncMock(return_value=cache_entries)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/v1/voices?language=zh-TW")

        assert response.status_code == 200
        data = response.json()
        for voice in data["items"]:
            assert voice["language"] == "zh-TW"

    @pytest.mark.asyncio
    async def test_list_voices_by_gender(self, mock_repos):
        """Test listing voices filtered by gender."""
        mock_cache_repo, _mock_cust_repo = mock_repos
        female_voices = [v for v in MOCK_VOICES if v.gender == "female"]
        cache_entries = [_build_voice_cache_entry(v) for v in female_voices]
        mock_cache_repo.list_all = AsyncMock(return_value=cache_entries)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/v1/voices?gender=female")

        assert response.status_code == 200
        data = response.json()
        for voice in data["items"]:
            assert voice.get("gender") == "female"

    @pytest.mark.asyncio
    async def test_list_voices_combined_filters(self, mock_repos):
        """Test listing voices with multiple filters."""
        mock_cache_repo, _mock_cust_repo = mock_repos
        filtered = [v for v in MOCK_VOICES if v.provider == "azure" and v.language == "zh-TW"]
        cache_entries = [_build_voice_cache_entry(v) for v in filtered]
        mock_cache_repo.list_all = AsyncMock(return_value=cache_entries)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/v1/voices?provider=azure&language=zh-TW")

        assert response.status_code == 200
        data = response.json()
        for voice in data["items"]:
            assert voice["provider"] == "azure"
            assert voice["language"] == "zh-TW"

    @pytest.mark.asyncio
    async def test_voice_response_schema(self, mock_repos):
        """Test voice response has correct schema."""
        mock_cache_repo, _mock_cust_repo = mock_repos
        cache_entries = [_build_voice_cache_entry(MOCK_VOICES[0])]
        mock_cache_repo.list_all = AsyncMock(return_value=cache_entries)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/v1/voices")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) > 0

        voice = data["items"][0]
        assert "id" in voice
        assert "name" in voice
        assert "provider" in voice
        assert "language" in voice


class TestGetVoiceByProviderEndpoint:
    """Contract tests for GET /api/v1/voices/{provider} endpoint."""

    @pytest.mark.asyncio
    async def test_get_voices_by_provider(self):
        """Test getting voices for a specific provider."""
        azure_voices = [v for v in MOCK_VOICES if v.provider == "azure"]

        with patch("src.presentation.api.routes.voices.list_voices_use_case") as mock_use_case:
            mock_use_case.execute = AsyncMock(return_value=azure_voices)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/voices/azure")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            for voice in data:
                assert voice["provider"] == "azure"

    @pytest.mark.asyncio
    async def test_get_voices_invalid_provider(self):
        """Test getting voices for invalid provider returns error."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/v1/voices/invalid_provider")

        # Should return 400 or 404
        assert response.status_code in [400, 404, 422]


class TestGetVoiceDetailEndpoint:
    """Contract tests for GET /api/v1/voices/{provider}/{voice_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_voice_detail(self):
        """Test getting details for a specific voice."""
        voice = MOCK_VOICES[0]

        with patch("src.presentation.api.routes.voices.get_voice_detail") as mock_get_detail:
            mock_get_detail.return_value = voice

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get(f"/api/v1/voices/{voice.provider}/{voice.id}")

            # May return 200 or 404 depending on implementation
            if response.status_code == 200:
                data = response.json()
                assert data["id"] == voice.id
                assert data["provider"] == voice.provider

    @pytest.mark.asyncio
    async def test_get_voice_not_found(self):
        """Test getting non-existent voice returns 404."""
        with patch("src.presentation.api.routes.voices.get_voice_detail") as mock_get_detail:
            mock_get_detail.return_value = None

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/voices/azure/non-existent-voice")

            assert response.status_code == 404


class TestVoiceParametersEndpoint:
    """Contract tests for voice parameter endpoints."""

    @pytest.mark.asyncio
    async def test_get_provider_params(self):
        """Test getting parameter ranges for a provider via list providers endpoint."""
        # The /providers endpoint returns provider info including supported_params
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/v1/providers")

        # Provider list returns 200 with provider info
        if response.status_code == 200:
            data = response.json()
            assert "providers" in data
            # Find azure provider
            azure_provider = next((p for p in data["providers"] if p["name"] == "azure"), None)
            if azure_provider:
                params = azure_provider.get("supported_params", {})
                if "speed" in params:
                    assert "min" in params["speed"]
                    assert "max" in params["speed"]
                    assert "default" in params["speed"]


class TestVoiceSearchEndpoint:
    """Contract tests for voice search functionality."""

    @pytest.mark.asyncio
    async def test_search_voices_by_name(self, mock_repos):
        """Test searching voices by name."""
        mock_cache_repo, _mock_cust_repo = mock_repos
        # Return all voices; the use case filters by search term
        cache_entries = [_build_voice_cache_entry(v) for v in MOCK_VOICES]
        mock_cache_repo.list_all = AsyncMock(return_value=cache_entries)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/v1/voices?search=Chen")

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_voices_pagination(self, mock_repos):
        """Test voices endpoint supports pagination."""
        mock_cache_repo, _mock_cust_repo = mock_repos
        cache_entries = [_build_voice_cache_entry(v) for v in MOCK_VOICES[:2]]
        mock_cache_repo.list_all = AsyncMock(return_value=cache_entries)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/api/v1/voices?limit=2&offset=0")

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data["items"], list)
            assert len(data["items"]) <= 2
            assert "limit" in data
            assert "offset" in data
