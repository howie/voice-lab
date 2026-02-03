"""Integration tests for Gemini TTS ↔ GCP Cloud TTS provider switching.

Validates that both Google TTS providers (Gemini and GCP Cloud TTS) can:
- Coexist as independent providers in the factory and DI container
- Be selected and switched between without interference
- Maintain separate credentials and configurations
- Each produce valid synthesis results independently
- Be correctly reported in the provider summary API
"""

import base64
import os
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.domain.entities.audio import AudioFormat, OutputMode
from src.domain.entities.tts import TTSRequest
from src.infrastructure.providers.tts.factory import TTSProviderFactory
from src.infrastructure.providers.tts.gcp_tts import GCPTTSProvider
from src.infrastructure.providers.tts.gemini_tts import GeminiTTSProvider
from src.main import app
from src.presentation.api.dependencies import Container, get_container
from src.presentation.api.middleware.auth import CurrentUser, get_current_user

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def gemini_provider() -> GeminiTTSProvider:
    """Create a Gemini TTS provider."""
    return GeminiTTSProvider(api_key="test-gemini-key")


@pytest.fixture
def gcp_provider() -> GCPTTSProvider:
    """Create a GCP Cloud TTS provider."""
    return GCPTTSProvider(credentials_path="/fake/credentials.json")


@pytest.fixture
def mock_current_user() -> CurrentUser:
    """Create a mock current user for API tests."""
    return CurrentUser(
        id=str(uuid.uuid4()),
        email="test@example.com",
        name="Test User",
        picture_url=None,
        google_id="test-google-id",
    )


@pytest.fixture
def mock_gcp_voice_response() -> MagicMock:
    """Create a mock GCP list_voices response."""
    from google.cloud import texttospeech_v1 as texttospeech

    voice1 = MagicMock()
    voice1.name = "en-US-Wavenet-D"
    voice1.language_codes = ["en-US"]
    voice1.ssml_gender = texttospeech.SsmlVoiceGender.MALE

    voice2 = MagicMock()
    voice2.name = "cmn-TW-Wavenet-A"
    voice2.language_codes = ["cmn-TW"]
    voice2.ssml_gender = texttospeech.SsmlVoiceGender.FEMALE

    response = MagicMock()
    response.voices = [voice1, voice2]
    return response


# ---------------------------------------------------------------------------
# Test: Provider Identity Independence
# ---------------------------------------------------------------------------


class TestProviderIdentityIndependence:
    """Verify Gemini and GCP TTS are distinct providers."""

    def test_different_provider_names(
        self, gemini_provider: GeminiTTSProvider, gcp_provider: GCPTTSProvider
    ):
        """Providers have distinct name identifiers."""
        assert gemini_provider.name == "gemini"
        assert gcp_provider.name == "gcp"
        assert gemini_provider.name != gcp_provider.name

    def test_different_display_names(
        self, gemini_provider: GeminiTTSProvider, gcp_provider: GCPTTSProvider
    ):
        """Providers have distinct display names."""
        assert gemini_provider.display_name == "Gemini TTS"
        assert gcp_provider.display_name == "Google Cloud TTS"

    def test_different_param_ranges(
        self, gemini_provider: GeminiTTSProvider, gcp_provider: GCPTTSProvider
    ):
        """Providers have different parameter ranges."""
        gemini_params = gemini_provider.get_supported_params()
        gcp_params = gcp_provider.get_supported_params()

        # GCP has wider speed range
        assert gcp_params["speed"]["min"] == 0.25
        assert gcp_params["speed"]["max"] == 4.0
        assert gemini_params["speed"]["min"] == 0.5
        assert gemini_params["speed"]["max"] == 2.0

        # Gemini has style_prompt, GCP doesn't
        assert "style_prompt" in gemini_params
        assert "style_prompt" not in gcp_params

    def test_factory_supports_both(self):
        """Factory recognizes both as supported providers."""
        assert TTSProviderFactory.is_supported("gemini")
        assert TTSProviderFactory.is_supported("gcp")
        supported = TTSProviderFactory.get_supported_providers()
        assert "gemini" in supported
        assert "gcp" in supported


# ---------------------------------------------------------------------------
# Test: Voice Listing Independence
# ---------------------------------------------------------------------------


class TestVoiceListingIndependence:
    """Verify voice listings are provider-specific."""

    @pytest.mark.asyncio
    async def test_gemini_voices_are_static(self, gemini_provider: GeminiTTSProvider):
        """Gemini returns 30 hardcoded multilingual voices."""
        voices = await gemini_provider.list_voices()

        assert len(voices) == 30
        assert all(v.provider == "gemini" for v in voices)
        assert all(v.id.startswith("gemini:") for v in voices)

    @pytest.mark.asyncio
    async def test_gcp_voices_are_dynamic(
        self, gcp_provider: GCPTTSProvider, mock_gcp_voice_response: MagicMock
    ):
        """GCP returns dynamic voices from the API."""
        mock_client = MagicMock()
        gcp_provider._client = mock_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_gcp_voice_response
            voices = await gcp_provider.list_voices()

        assert len(voices) == 2
        assert all(v.provider == "gcp" for v in voices)
        assert all(v.id.startswith("gcp:") for v in voices)

    @pytest.mark.asyncio
    async def test_voice_ids_do_not_collide(
        self,
        gemini_provider: GeminiTTSProvider,
        gcp_provider: GCPTTSProvider,
        mock_gcp_voice_response: MagicMock,
    ):
        """Voice IDs from both providers have distinct prefixes."""
        gemini_voices = await gemini_provider.list_voices()

        mock_client = MagicMock()
        gcp_provider._client = mock_client
        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_gcp_voice_response
            gcp_voices = await gcp_provider.list_voices()

        gemini_ids = {v.id for v in gemini_voices}
        gcp_ids = {v.id for v in gcp_voices}

        # No overlap in full IDs
        assert gemini_ids.isdisjoint(gcp_ids)

    @pytest.mark.asyncio
    async def test_gemini_get_voice_by_id(self, gemini_provider: GeminiTTSProvider):
        """Gemini can retrieve a specific voice by ID."""
        voice = await gemini_provider.get_voice("Kore")
        assert voice is not None
        assert voice.voice_id == "Kore"
        assert voice.provider == "gemini"

        # Also works with prefix
        voice_prefixed = await gemini_provider.get_voice("gemini:Kore")
        assert voice_prefixed is not None
        assert voice_prefixed.voice_id == "Kore"

    @pytest.mark.asyncio
    async def test_gcp_get_voice_by_id(
        self, gcp_provider: GCPTTSProvider, mock_gcp_voice_response: MagicMock
    ):
        """GCP can retrieve a specific voice by ID."""
        mock_client = MagicMock()
        gcp_provider._client = mock_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_gcp_voice_response
            voice = await gcp_provider.get_voice("en-US-Wavenet-D")

        assert voice is not None
        assert voice.voice_id == "en-US-Wavenet-D"
        assert voice.provider == "gcp"

    @pytest.mark.asyncio
    async def test_gcp_get_voice_with_prefix(
        self, gcp_provider: GCPTTSProvider, mock_gcp_voice_response: MagicMock
    ):
        """GCP can retrieve a voice with gcp: prefix."""
        mock_client = MagicMock()
        gcp_provider._client = mock_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_gcp_voice_response
            voice = await gcp_provider.get_voice("gcp:en-US-Wavenet-D")

        assert voice is not None
        assert voice.voice_id == "en-US-Wavenet-D"


# ---------------------------------------------------------------------------
# Test: Synthesis Independence
# ---------------------------------------------------------------------------


class TestSynthesisIndependence:
    """Verify synthesis works independently for each provider."""

    @pytest.mark.asyncio
    async def test_gemini_synthesis(self, gemini_provider: GeminiTTSProvider):
        """Gemini synthesizes via REST API with PCM conversion."""
        request = TTSRequest(
            text="Hello from Gemini.",
            voice_id="Kore",
            provider="gemini",
            language="zh-TW",
            speed=1.0,
            pitch=0.0,
            volume=1.0,
            output_format=AudioFormat.MP3,
            output_mode=OutputMode.BATCH,
        )

        pcm_data = b"\x00\x00" * 24000
        mock_response_data = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"inlineData": {"data": base64.b64encode(pcm_data).decode()}}]
                    }
                }
            ]
        }

        mock_mp3_data = b"mock-gemini-mp3"

        with (
            patch.object(gemini_provider._client, "post", new_callable=AsyncMock) as mock_post,
            patch.object(
                gemini_provider, "_convert_pcm_to_format", new_callable=AsyncMock
            ) as mock_convert,
        ):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            mock_convert.return_value = mock_mp3_data

            result = await gemini_provider.synthesize(request)

        assert result.audio.data == mock_mp3_data
        assert result.audio.format == AudioFormat.MP3
        assert result.request.provider == "gemini"

    @pytest.mark.asyncio
    async def test_gcp_synthesis(self, gcp_provider: GCPTTSProvider):
        """GCP synthesizes via gRPC SDK with server-side encoding."""
        request = TTSRequest(
            text="Hello from GCP.",
            voice_id="en-US-Wavenet-D",
            provider="gcp",
            language="en-US",
            speed=1.0,
            pitch=0.0,
            volume=1.0,
            output_format=AudioFormat.MP3,
            output_mode=OutputMode.BATCH,
        )

        mock_audio_content = b"mock-gcp-mp3-audio"
        mock_response = MagicMock()
        mock_response.audio_content = mock_audio_content

        mock_client = MagicMock()
        gcp_provider._client = mock_client

        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_response
            result = await gcp_provider.synthesize(request)

        assert result.audio.data == mock_audio_content
        assert result.audio.format == AudioFormat.MP3
        assert result.request.provider == "gcp"

    @pytest.mark.asyncio
    async def test_sequential_switching(
        self, gemini_provider: GeminiTTSProvider, gcp_provider: GCPTTSProvider
    ):
        """Synthesize with Gemini, then GCP, then Gemini again. No state leaks."""
        providers = {"gemini": gemini_provider, "gcp": gcp_provider}

        # Prepare mocks
        pcm_data = b"\x00\x00" * 24000
        gemini_response_data = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"inlineData": {"data": base64.b64encode(pcm_data).decode()}}]
                    }
                }
            ]
        }

        gcp_audio = b"gcp-audio-bytes"
        gcp_mock_response = MagicMock()
        gcp_mock_response.audio_content = gcp_audio

        gcp_mock_client = MagicMock()
        gcp_provider._client = gcp_mock_client

        sequence = [
            ("gemini", "Kore", b"gemini-audio-1"),
            ("gcp", "en-US-Wavenet-D", gcp_audio),
            ("gemini", "Puck", b"gemini-audio-2"),
        ]

        results = []
        for provider_name, voice_id, expected_audio in sequence:
            request = TTSRequest(
                text=f"Test from {provider_name}.",
                voice_id=voice_id,
                provider=provider_name,
                language="en-US",
                speed=1.0,
                pitch=0.0,
                volume=1.0,
                output_format=AudioFormat.MP3,
                output_mode=OutputMode.BATCH,
            )

            if provider_name == "gemini":
                with (
                    patch.object(
                        gemini_provider._client, "post", new_callable=AsyncMock
                    ) as mock_post,
                    patch.object(
                        gemini_provider,
                        "_convert_pcm_to_format",
                        new_callable=AsyncMock,
                    ) as mock_convert,
                ):
                    mock_resp = MagicMock()
                    mock_resp.status_code = 200
                    mock_resp.json.return_value = gemini_response_data
                    mock_resp.raise_for_status = MagicMock()
                    mock_post.return_value = mock_resp
                    mock_convert.return_value = expected_audio

                    result = await providers[provider_name].synthesize(request)
            else:
                with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
                    mock_to_thread.return_value = gcp_mock_response
                    result = await providers[provider_name].synthesize(request)

            results.append(result)

        # All three synthesized correctly
        assert len(results) == 3
        assert results[0].request.provider == "gemini"
        assert results[0].audio.data == b"gemini-audio-1"
        assert results[1].request.provider == "gcp"
        assert results[1].audio.data == gcp_audio
        assert results[2].request.provider == "gemini"
        assert results[2].audio.data == b"gemini-audio-2"


# ---------------------------------------------------------------------------
# Test: Credential Independence
# ---------------------------------------------------------------------------


class TestCredentialIndependence:
    """Verify providers use separate credentials."""

    def test_gemini_uses_api_key(self):
        """Gemini uses GOOGLE_AI_API_KEY or GEMINI_API_KEY."""
        provider = GeminiTTSProvider(api_key="test-gemini-key")
        assert provider._api_key == "test-gemini-key"

    def test_gcp_uses_service_account(self):
        """GCP uses GOOGLE_APPLICATION_CREDENTIALS path."""
        provider = GCPTTSProvider(credentials_path="/path/to/sa.json")
        assert provider._credentials_path == "/path/to/sa.json"

    def test_credentials_do_not_interfere(self):
        """Creating one provider doesn't affect the other's credentials."""
        gemini = GeminiTTSProvider(api_key="gemini-key-123")
        gcp = GCPTTSProvider(credentials_path="/gcp/creds.json")

        assert gemini._api_key == "gemini-key-123"
        assert gcp._credentials_path == "/gcp/creds.json"
        # Gemini has no credentials_path attribute concept
        assert not hasattr(gemini, "_credentials_path")
        # GCP has no api_key attribute concept
        assert not hasattr(gcp, "_api_key")


# ---------------------------------------------------------------------------
# Test: DI Container Coexistence
# ---------------------------------------------------------------------------


class TestDIContainerCoexistence:
    """Verify both providers can be registered in the DI container simultaneously."""

    def test_container_registers_both_when_credentials_available(self):
        """Both providers appear in container when credentials are set."""
        env = {
            "GOOGLE_AI_API_KEY": "test-gemini-key",
            "GOOGLE_APPLICATION_CREDENTIALS": "/fake/credentials.json",
        }

        with patch.dict(os.environ, env, clear=False):
            container = Container()
            # Bypass lazy cache
            container._tts_providers = None

            # Mock GCP client creation to avoid real credential loading
            with patch("src.infrastructure.providers.tts.gcp_tts.texttospeech.TextToSpeechClient"):
                providers = container._create_tts_providers()

        assert "gemini" in providers
        assert "gcp" in providers
        assert isinstance(providers["gemini"], GeminiTTSProvider)
        assert isinstance(providers["gcp"], GCPTTSProvider)

    def test_container_registers_only_gemini_without_gcp_creds(self):
        """Only Gemini appears when GCP credentials are missing."""
        env = {
            "GOOGLE_AI_API_KEY": "test-gemini-key",
        }
        # Remove GCP-related env vars
        env_clear = {
            "GOOGLE_APPLICATION_CREDENTIALS": "",
            "K_SERVICE": "",
            "GCP_PROJECT": "",
            "ENABLE_GCP_PROVIDERS": "",
            "GCP_CREDENTIALS_PATH": "",
        }

        with patch.dict(os.environ, {**env, **env_clear}, clear=False):
            # Ensure the env vars we want absent are actually empty
            os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
            os.environ.pop("K_SERVICE", None)
            os.environ.pop("GCP_PROJECT", None)
            os.environ.pop("ENABLE_GCP_PROVIDERS", None)
            os.environ.pop("GCP_CREDENTIALS_PATH", None)

            container = Container()
            container._tts_providers = None
            providers = container._create_tts_providers()

        assert "gemini" in providers
        assert "gcp" not in providers

    def test_container_registers_only_gcp_without_gemini_key(self):
        """Only GCP appears when Gemini API key is missing."""
        env = {
            "GOOGLE_APPLICATION_CREDENTIALS": "/fake/credentials.json",
        }
        env_clear = {
            "GOOGLE_AI_API_KEY": "",
            "GEMINI_API_KEY": "",
        }

        with patch.dict(os.environ, {**env, **env_clear}, clear=False):
            os.environ.pop("GOOGLE_AI_API_KEY", None)
            os.environ.pop("GEMINI_API_KEY", None)

            container = Container()
            container._tts_providers = None

            with patch("src.infrastructure.providers.tts.gcp_tts.texttospeech.TextToSpeechClient"):
                providers = container._create_tts_providers()

        assert "gcp" in providers
        assert "gemini" not in providers


# ---------------------------------------------------------------------------
# Test: Factory Provider Creation
# ---------------------------------------------------------------------------


class TestFactoryProviderCreation:
    """Verify TTSProviderFactory creates correct provider types."""

    @pytest.mark.asyncio
    async def test_factory_creates_gemini(self):
        """Factory creates GeminiTTSProvider for 'gemini'."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            provider = await TTSProviderFactory.create("gemini")

        assert isinstance(provider, GeminiTTSProvider)
        assert provider.name == "gemini"

    @pytest.mark.asyncio
    async def test_factory_creates_gcp(self):
        """Factory creates GCPTTSProvider for 'gcp'."""
        with patch.dict(os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": "/fake.json"}):
            provider = await TTSProviderFactory.create("gcp")

        assert isinstance(provider, GCPTTSProvider)
        assert provider.name == "gcp"

    @pytest.mark.asyncio
    async def test_factory_gemini_and_gcp_are_different_classes(self):
        """Factory returns different classes for 'gemini' vs 'gcp'."""
        with patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "key", "GOOGLE_APPLICATION_CREDENTIALS": "/fake.json"},
        ):
            gemini = await TTSProviderFactory.create("gemini")
            gcp = await TTSProviderFactory.create("gcp")

        assert type(gemini) is not type(gcp)
        assert isinstance(gemini, GeminiTTSProvider)
        assert isinstance(gcp, GCPTTSProvider)


# ---------------------------------------------------------------------------
# Test: Provider Summary API
# ---------------------------------------------------------------------------


class TestProviderSummaryAPI:
    """Verify provider summary API reports both providers correctly."""

    @pytest.mark.asyncio
    async def test_summary_shows_both_available(self, mock_current_user: CurrentUser):
        """Both providers show as available when credentials are set."""
        mock_gemini = MagicMock(spec=GeminiTTSProvider)
        mock_gemini.name = "gemini"
        mock_gcp = MagicMock(spec=GCPTTSProvider)
        mock_gcp.name = "gcp"

        mock_container = MagicMock(spec=Container)
        mock_container.get_tts_providers.return_value = {
            "gemini": mock_gemini,
            "gcp": mock_gcp,
        }
        mock_container.get_stt_providers.return_value = {}
        mock_container.get_llm_providers.return_value = {}

        async def override_get_current_user():
            return mock_current_user

        def override_get_container():
            return mock_container

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_container] = override_get_container

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/providers/summary")

            assert response.status_code == 200
            data = response.json()

            tts_providers = {p["name"]: p for p in data["tts"]}

            assert "gemini" in tts_providers
            assert "gcp" in tts_providers
            assert tts_providers["gemini"]["status"] == "available"
            assert tts_providers["gcp"]["status"] == "available"
            assert tts_providers["gemini"]["display_name"] == "Gemini TTS"
            assert tts_providers["gcp"]["display_name"] == "Google Cloud TTS"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_summary_shows_mixed_availability(self, mock_current_user: CurrentUser):
        """Only Gemini available when GCP credentials are missing."""
        mock_gemini = MagicMock(spec=GeminiTTSProvider)
        mock_gemini.name = "gemini"

        mock_container = MagicMock(spec=Container)
        mock_container.get_tts_providers.return_value = {"gemini": mock_gemini}
        mock_container.get_stt_providers.return_value = {}
        mock_container.get_llm_providers.return_value = {}

        async def override_get_current_user():
            return mock_current_user

        def override_get_container():
            return mock_container

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_container] = override_get_container

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/providers/summary")

            assert response.status_code == 200
            data = response.json()

            tts_providers = {p["name"]: p for p in data["tts"]}

            assert tts_providers["gemini"]["status"] == "available"
            assert tts_providers["gcp"]["status"] == "unavailable"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_summary_provider_configs_are_distinct(self, mock_current_user: CurrentUser):
        """Provider configs in summary have distinct parameters."""
        mock_container = MagicMock(spec=Container)
        mock_container.get_tts_providers.return_value = {}
        mock_container.get_stt_providers.return_value = {}
        mock_container.get_llm_providers.return_value = {}

        async def override_get_current_user():
            return mock_current_user

        def override_get_container():
            return mock_container

        app.dependency_overrides[get_current_user] = override_get_current_user
        app.dependency_overrides[get_container] = override_get_container

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/providers/summary")

            assert response.status_code == 200
            data = response.json()
            tts_providers = {p["name"]: p for p in data["tts"]}

            gemini_config = tts_providers["gemini"]
            gcp_config = tts_providers["gcp"]

            # Gemini supports style_prompt, GCP doesn't
            assert "style_prompt" in gemini_config["supported_params"]
            assert "style_prompt" not in gcp_config["supported_params"]

            # GCP has wider speed range (0.25-4.0)
            assert gcp_config["supported_params"]["speed"]["min"] == 0.25
            assert gcp_config["supported_params"]["speed"]["max"] == 4.0

            # Gemini speed range (0.5-2.0)
            assert gemini_config["supported_params"]["speed"]["min"] == 0.5
            assert gemini_config["supported_params"]["speed"]["max"] == 2.0

            # Both support mp3 and wav
            assert "mp3" in gemini_config["supported_formats"]
            assert "mp3" in gcp_config["supported_formats"]
            assert "wav" in gemini_config["supported_formats"]
            assert "wav" in gcp_config["supported_formats"]

            # Gemini supports flac, GCP does not
            assert "flac" in gemini_config["supported_formats"]
            assert "flac" not in gcp_config["supported_formats"]
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Test: Health Check Independence
# ---------------------------------------------------------------------------


class TestHealthCheckIndependence:
    """Verify health checks are independent per provider."""

    @pytest.mark.asyncio
    async def test_gemini_healthy_gcp_unhealthy(
        self, gemini_provider: GeminiTTSProvider, gcp_provider: GCPTTSProvider
    ):
        """Gemini can be healthy while GCP is unhealthy."""
        # Gemini healthy
        with patch.object(gemini_provider._client, "get", new_callable=AsyncMock) as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_get.return_value = mock_resp
            gemini_healthy = await gemini_provider.health_check()

        # GCP unhealthy
        mock_client = MagicMock()
        gcp_provider._client = mock_client
        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.side_effect = Exception("Connection refused")
            gcp_healthy = await gcp_provider.health_check()

        assert gemini_healthy is True
        assert gcp_healthy is False

    @pytest.mark.asyncio
    async def test_gcp_healthy_gemini_unhealthy(
        self,
        gcp_provider: GCPTTSProvider,
    ):
        """GCP can be healthy while Gemini is unhealthy."""
        # Gemini unhealthy (no API key)
        gemini_no_key = GeminiTTSProvider(api_key="")
        gemini_healthy = await gemini_no_key.health_check()

        # GCP healthy
        mock_client = MagicMock()
        gcp_provider._client = mock_client
        mock_response = MagicMock()
        mock_response.voices = []
        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_response
            gcp_healthy = await gcp_provider.health_check()

        assert gemini_healthy is False
        assert gcp_healthy is True
