"""Integration tests for Multi-Role TTS API.

TDD-Red: These tests are written FIRST and should FAIL until implementation.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.fixture
async def client() -> AsyncClient:
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestCapabilitiesEndpoint:
    """Test GET /api/v1/tts/multi-role/capabilities."""

    @pytest.mark.asyncio
    async def test_get_capabilities_returns_all_providers(self, client: AsyncClient) -> None:
        """Should return capabilities for all supported providers."""
        response = await client.get("/api/v1/tts/multi-role/capabilities")

        assert response.status_code == 200
        data = response.json()
        assert "providers" in data

        providers = data["providers"]
        assert len(providers) >= 6

        # Check required fields for each provider
        for provider in providers:
            assert "provider_name" in provider
            assert "support_type" in provider
            assert "max_speakers" in provider
            assert "character_limit" in provider

    @pytest.mark.asyncio
    async def test_get_capabilities_includes_native_providers(self, client: AsyncClient) -> None:
        """Should include native support providers."""
        response = await client.get("/api/v1/tts/multi-role/capabilities")

        data = response.json()
        provider_names = [p["provider_name"] for p in data["providers"]]

        assert "elevenlabs" in provider_names
        assert "azure" in provider_names
        assert "gcp" in provider_names

    @pytest.mark.asyncio
    async def test_get_capabilities_includes_segmented_providers(self, client: AsyncClient) -> None:
        """Should include segmented support providers."""
        response = await client.get("/api/v1/tts/multi-role/capabilities")

        data = response.json()
        providers_by_name = {p["provider_name"]: p for p in data["providers"]}

        assert providers_by_name["openai"]["support_type"] == "segmented"
        assert providers_by_name["cartesia"]["support_type"] == "segmented"
        assert providers_by_name["deepgram"]["support_type"] == "segmented"


class TestParseEndpoint:
    """Test POST /api/v1/tts/multi-role/parse."""

    @pytest.mark.asyncio
    async def test_parse_valid_dialogue(self, client: AsyncClient) -> None:
        """Should parse valid dialogue text."""
        response = await client.post(
            "/api/v1/tts/multi-role/parse",
            json={"text": "A: 你好 B: 嗨"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "turns" in data
        assert "speakers" in data
        assert "total_characters" in data

        assert len(data["turns"]) == 2
        assert data["speakers"] == ["A", "B"]

    @pytest.mark.asyncio
    async def test_parse_bracket_format(self, client: AsyncClient) -> None:
        """Should parse bracket format speaker names."""
        response = await client.post(
            "/api/v1/tts/multi-role/parse",
            json={"text": "[Host]: 歡迎 [Guest]: 謝謝"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["speakers"] == ["Host", "Guest"]

    @pytest.mark.asyncio
    async def test_parse_empty_input_returns_422(self, client: AsyncClient) -> None:
        """Should return 422 for empty input (Pydantic validation)."""
        response = await client.post(
            "/api/v1/tts/multi-role/parse",
            json={"text": ""},
        )

        # Pydantic's min_length validation returns 422
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_parse_invalid_format_returns_400(self, client: AsyncClient) -> None:
        """Should return 400 for invalid format."""
        response = await client.post(
            "/api/v1/tts/multi-role/parse",
            json={"text": "沒有說話者格式的文字"},
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_parse_too_many_speakers_returns_400(self, client: AsyncClient) -> None:
        """Should return 400 when more than 6 speakers."""
        response = await client.post(
            "/api/v1/tts/multi-role/parse",
            json={"text": "A: 1 B: 2 C: 3 D: 4 E: 5 F: 6 G: 7"},
        )

        assert response.status_code == 400
        data = response.json()
        assert "6" in str(data["detail"])


class TestSynthesizeEndpoint:
    """Test POST /api/v1/tts/multi-role/synthesize."""

    @pytest.mark.asyncio
    async def test_synthesize_returns_result(self, client: AsyncClient) -> None:
        """Should return synthesis result with mocked provider."""
        response = await client.post(
            "/api/v1/tts/multi-role/synthesize",
            json={
                "provider": "elevenlabs",
                "turns": [
                    {"speaker": "A", "text": "你好", "index": 0},
                    {"speaker": "B", "text": "嗨", "index": 1},
                ],
                "voice_assignments": [
                    {"speaker": "A", "voice_id": "voice_a"},
                    {"speaker": "B", "voice_id": "voice_b"},
                ],
                "language": "zh-TW",
            },
        )

        # May return 200 (success) or 503 (provider unavailable) in test env
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert "audio_url" in data
            assert "duration_ms" in data
            assert "latency_ms" in data
            assert "provider" in data
            assert "synthesis_mode" in data

    @pytest.mark.asyncio
    async def test_synthesize_missing_voice_assignment_returns_400(
        self, client: AsyncClient
    ) -> None:
        """Should return 400 when voice assignment is missing for a speaker."""
        response = await client.post(
            "/api/v1/tts/multi-role/synthesize",
            json={
                "provider": "elevenlabs",
                "turns": [
                    {"speaker": "A", "text": "你好", "index": 0},
                    {"speaker": "B", "text": "嗨", "index": 1},
                ],
                "voice_assignments": [
                    {"speaker": "A", "voice_id": "voice_a"},
                    # Missing assignment for B
                ],
                "language": "zh-TW",
            },
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_synthesize_invalid_provider_returns_400(self, client: AsyncClient) -> None:
        """Should return 400 for unsupported provider."""
        response = await client.post(
            "/api/v1/tts/multi-role/synthesize",
            json={
                "provider": "invalid_provider",
                "turns": [{"speaker": "A", "text": "test", "index": 0}],
                "voice_assignments": [{"speaker": "A", "voice_id": "voice_a"}],
            },
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_synthesize_empty_turns_returns_400(self, client: AsyncClient) -> None:
        """Should return 400 for empty turns."""
        response = await client.post(
            "/api/v1/tts/multi-role/synthesize",
            json={
                "provider": "elevenlabs",
                "turns": [],
                "voice_assignments": [],
            },
        )

        assert response.status_code == 400


class TestSynthesizeBinaryEndpoint:
    """Test POST /api/v1/tts/multi-role/synthesize/binary."""

    @pytest.mark.asyncio
    async def test_synthesize_binary_returns_audio(self, client: AsyncClient) -> None:
        """Should return binary audio content."""
        response = await client.post(
            "/api/v1/tts/multi-role/synthesize/binary",
            json={
                "provider": "elevenlabs",
                "turns": [
                    {"speaker": "A", "text": "你好", "index": 0},
                ],
                "voice_assignments": [
                    {"speaker": "A", "voice_id": "voice_a"},
                ],
            },
        )

        # May return 200 (success) or 503 (provider unavailable) in test env
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            assert response.headers["content-type"].startswith("audio/")


class TestMultiRoleTTSFullFlow:
    """E2E-like integration tests for complete multi-role TTS flow."""

    @pytest.mark.asyncio
    async def test_complete_flow_capabilities_to_synthesize(self, client: AsyncClient) -> None:
        """Test complete flow: get capabilities -> parse -> synthesize."""
        # Step 1: Get capabilities
        cap_response = await client.get("/api/v1/tts/multi-role/capabilities")
        assert cap_response.status_code == 200
        capabilities = cap_response.json()

        # Get ElevenLabs capability
        elevenlabs_cap = next(
            (p for p in capabilities["providers"] if p["provider_name"] == "elevenlabs"),
            None,
        )
        assert elevenlabs_cap is not None
        assert elevenlabs_cap["support_type"] == "native"
        assert elevenlabs_cap["max_speakers"] >= 6  # ElevenLabs supports up to 10

        # Step 2: Parse dialogue
        dialogue_text = "A: 你好，歡迎來到節目 B: 謝謝邀請，很高興在這裡"
        parse_response = await client.post(
            "/api/v1/tts/multi-role/parse",
            json={"text": dialogue_text},
        )
        assert parse_response.status_code == 200
        parse_result = parse_response.json()

        assert len(parse_result["turns"]) == 2
        assert parse_result["speakers"] == ["A", "B"]
        assert parse_result["total_characters"] > 0

        # Step 3: Synthesize (may return 503 in test env without real API keys)
        synth_response = await client.post(
            "/api/v1/tts/multi-role/synthesize",
            json={
                "provider": "elevenlabs",
                "turns": parse_result["turns"],
                "voice_assignments": [
                    {"speaker": "A", "voice_id": "voice_host"},
                    {"speaker": "B", "voice_id": "voice_guest"},
                ],
                "language": "zh-TW",
                "output_format": "mp3",
            },
        )

        # Verify response structure (even if provider unavailable)
        assert synth_response.status_code in [200, 503]
        if synth_response.status_code == 200:
            result = synth_response.json()
            assert "audio_content" in result or "audio_url" in result
            assert result["provider"] == "elevenlabs"
            assert result["synthesis_mode"] in ["native", "segmented"]

    @pytest.mark.asyncio
    async def test_flow_with_bracket_format_speakers(self, client: AsyncClient) -> None:
        """Test flow with bracket format speaker names."""
        # Parse with bracket format
        parse_response = await client.post(
            "/api/v1/tts/multi-role/parse",
            json={"text": "[主持人]: 開始節目 [來賓A]: 大家好 [來賓B]: 嗨"},
        )
        assert parse_response.status_code == 200
        parse_result = parse_response.json()

        assert len(parse_result["turns"]) == 3
        assert "主持人" in parse_result["speakers"]
        assert "來賓A" in parse_result["speakers"]
        assert "來賓B" in parse_result["speakers"]

    @pytest.mark.asyncio
    async def test_flow_with_mixed_format(self, client: AsyncClient) -> None:
        """Test parsing mixed letter and bracket formats."""
        parse_response = await client.post(
            "/api/v1/tts/multi-role/parse",
            json={"text": "A: 簡單說話者 [Host]: 命名說話者"},
        )
        assert parse_response.status_code == 200
        parse_result = parse_response.json()

        assert len(parse_result["turns"]) == 2
        assert "A" in parse_result["speakers"]
        assert "Host" in parse_result["speakers"]

    @pytest.mark.asyncio
    async def test_flow_handles_character_limit(self, client: AsyncClient) -> None:
        """Test that flow respects character limits."""
        # Create text that exceeds most provider limits
        long_text = "A: " + "這是一段很長的文字。" * 1000 + " B: 回應"

        parse_response = await client.post(
            "/api/v1/tts/multi-role/parse",
            json={"text": long_text},
        )

        # Should parse successfully
        assert parse_response.status_code == 200
        parse_result = parse_response.json()

        # Verify character count is reported
        assert parse_result["total_characters"] > 10000

    @pytest.mark.asyncio
    async def test_flow_validates_speaker_count(self, client: AsyncClient) -> None:
        """Test that flow validates maximum speaker count."""
        # Create dialogue with too many speakers (>6)
        many_speakers = "A: 1 B: 2 C: 3 D: 4 E: 5 F: 6 G: 7 H: 8"

        parse_response = await client.post(
            "/api/v1/tts/multi-role/parse",
            json={"text": many_speakers},
        )

        # Should fail with 400
        assert parse_response.status_code == 400
        error = parse_response.json()
        assert "6" in str(error["detail"])  # Should mention the limit
