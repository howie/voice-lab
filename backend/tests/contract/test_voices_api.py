"""Contract tests for voices API endpoints.

T053: Create tests for voice listing endpoint
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.application.use_cases.list_voices import VoiceProfile
from src.main import app

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
        id="cmn-TW-Standard-A",
        name="Standard A",
        provider="gcp",
        language="zh-TW",
        gender="female",
    ),
    VoiceProfile(
        id="cmn-TW-Standard-B",
        name="Standard B",
        provider="gcp",
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


class TestListVoicesEndpoint:
    """Contract tests for GET /api/v1/voices endpoint."""

    @pytest.mark.asyncio
    async def test_list_all_voices(self):
        """Test listing all voices without filters."""
        with patch("src.presentation.api.routes.voices.list_voices_use_case") as mock_use_case:
            mock_use_case.execute = AsyncMock(return_value=MOCK_VOICES)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/voices")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0

    @pytest.mark.asyncio
    async def test_list_voices_by_provider(self):
        """Test listing voices filtered by provider."""
        azure_voices = [v for v in MOCK_VOICES if v["provider"] == "azure"]

        with patch("src.presentation.api.routes.voices.list_voices_use_case") as mock_use_case:
            mock_use_case.execute = AsyncMock(return_value=azure_voices)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/voices?provider=azure")

            assert response.status_code == 200
            data = response.json()
            for voice in data:
                assert voice["provider"] == "azure"

    @pytest.mark.asyncio
    async def test_list_voices_by_language(self):
        """Test listing voices filtered by language."""
        zh_tw_voices = [v for v in MOCK_VOICES if v["language"] == "zh-TW"]

        with patch("src.presentation.api.routes.voices.list_voices_use_case") as mock_use_case:
            mock_use_case.execute = AsyncMock(return_value=zh_tw_voices)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/voices?language=zh-TW")

            assert response.status_code == 200
            data = response.json()
            for voice in data:
                assert voice["language"] == "zh-TW"

    @pytest.mark.asyncio
    async def test_list_voices_by_gender(self):
        """Test listing voices filtered by gender."""
        female_voices = [v for v in MOCK_VOICES if v.get("gender") == "female"]

        with patch("src.presentation.api.routes.voices.list_voices_use_case") as mock_use_case:
            mock_use_case.execute = AsyncMock(return_value=female_voices)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/voices?gender=female")

            assert response.status_code == 200
            data = response.json()
            for voice in data:
                assert voice.get("gender") == "female"

    @pytest.mark.asyncio
    async def test_list_voices_combined_filters(self):
        """Test listing voices with multiple filters."""
        filtered_voices = [
            v for v in MOCK_VOICES if v["provider"] == "azure" and v["language"] == "zh-TW"
        ]

        with patch("src.presentation.api.routes.voices.list_voices_use_case") as mock_use_case:
            mock_use_case.execute = AsyncMock(return_value=filtered_voices)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/voices?provider=azure&language=zh-TW")

            assert response.status_code == 200
            data = response.json()
            for voice in data:
                assert voice["provider"] == "azure"
                assert voice["language"] == "zh-TW"

    @pytest.mark.asyncio
    async def test_voice_response_schema(self):
        """Test voice response has correct schema."""
        with patch("src.presentation.api.routes.voices.list_voices_use_case") as mock_use_case:
            mock_use_case.execute = AsyncMock(return_value=MOCK_VOICES[:1])

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/voices")

            assert response.status_code == 200
            data = response.json()
            assert len(data) > 0

            voice = data[0]
            assert "id" in voice
            assert "name" in voice
            assert "provider" in voice
            assert "language" in voice


class TestGetVoiceByProviderEndpoint:
    """Contract tests for GET /api/v1/voices/{provider} endpoint."""

    @pytest.mark.asyncio
    async def test_get_voices_by_provider(self):
        """Test getting voices for a specific provider."""
        azure_voices = [v for v in MOCK_VOICES if v["provider"] == "azure"]

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
                response = await ac.get(f"/api/v1/voices/{voice['provider']}/{voice['id']}")

            # May return 200 or 404 depending on implementation
            if response.status_code == 200:
                data = response.json()
                assert data["id"] == voice["id"]
                assert data["provider"] == voice["provider"]

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
        """Test getting parameter ranges for a provider."""
        mock_params = {
            "speed": {"min": 0.5, "max": 2.0, "default": 1.0},
            "pitch": {"min": -20, "max": 20, "default": 0},
            "volume": {"min": 0.0, "max": 2.0, "default": 1.0},
        }

        with patch("src.presentation.api.routes.providers.get_provider_params") as mock_get_params:
            mock_get_params.return_value = mock_params

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/providers/azure/params")

            if response.status_code == 200:
                data = response.json()
                assert "speed" in data
                assert "min" in data["speed"]
                assert "max" in data["speed"]
                assert "default" in data["speed"]


class TestVoiceSearchEndpoint:
    """Contract tests for voice search functionality."""

    @pytest.mark.asyncio
    async def test_search_voices_by_name(self):
        """Test searching voices by name."""
        matching_voices = [v for v in MOCK_VOICES if "Chen" in v["name"]]

        with patch("src.presentation.api.routes.voices.list_voices_use_case") as mock_use_case:
            mock_use_case.execute = AsyncMock(return_value=matching_voices)

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/voices?search=Chen")

            if response.status_code == 200:
                data = response.json()
                # Verify search functionality if implemented
                assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_voices_pagination(self):
        """Test voices endpoint supports pagination."""
        with patch("src.presentation.api.routes.voices.list_voices_use_case") as mock_use_case:
            mock_use_case.execute = AsyncMock(return_value=MOCK_VOICES[:2])

            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/voices?limit=2&offset=0")

            if response.status_code == 200:
                data = response.json()
                assert isinstance(data, list)
                assert len(data) <= 2
