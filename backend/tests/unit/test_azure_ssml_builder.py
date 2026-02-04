"""Unit tests for Azure SSML Builder express-as style tag support."""

import pytest

from src.domain.entities.multi_role_tts import DialogueTurn
from src.infrastructure.providers.tts.multi_role.azure_ssml_builder import (
    KNOWN_STYLES,
    AzureSSMLBuilder,
)


@pytest.fixture
def builder() -> AzureSSMLBuilder:
    return AzureSSMLBuilder()


@pytest.fixture
def voice_map() -> dict[str, str]:
    return {"A": "zh-TW-HsiaoChenNeural", "B": "zh-TW-YunJheNeural"}


class TestParseStyleSegments:
    """Tests for _parse_style_segments()."""

    def test_no_tags(self, builder: AzureSSMLBuilder) -> None:
        segments = builder._parse_style_segments("你好世界")
        assert segments == [(None, "你好世界")]

    def test_single_known_tag(self, builder: AzureSSMLBuilder) -> None:
        segments = builder._parse_style_segments("[cheerful] 太好了")
        assert len(segments) == 1
        assert segments[0][0] == "cheerful"
        assert segments[0][1] == "太好了"

    def test_multiple_tags(self, builder: AzureSSMLBuilder) -> None:
        segments = builder._parse_style_segments("[cheerful] 好！ [sad] 嗚嗚")
        assert len(segments) == 2
        assert segments[0] == ("cheerful", "好！")
        assert segments[1] == ("sad", "嗚嗚")

    def test_unknown_tag_kept_as_text(self, builder: AzureSSMLBuilder) -> None:
        segments = builder._parse_style_segments("[fakestyle] hello")
        # Unknown tag should be treated as literal text
        found_texts = [t for _, t in segments]
        combined = " ".join(found_texts)
        assert "fakestyle" in combined
        assert "hello" in combined

    def test_text_before_tag(self, builder: AzureSSMLBuilder) -> None:
        segments = builder._parse_style_segments("你好 [cheerful] 太好了")
        assert len(segments) == 2
        assert segments[0] == (None, "你好")
        assert segments[1] == ("cheerful", "太好了")

    def test_case_insensitive(self, builder: AzureSSMLBuilder) -> None:
        segments = builder._parse_style_segments("[Cheerful] 太好了")
        assert segments[0][0] == "cheerful"

    def test_mixed_case(self, builder: AzureSSMLBuilder) -> None:
        segments = builder._parse_style_segments("[CHEERFUL] 太好了")
        assert segments[0][0] == "cheerful"

    def test_hyphenated_style(self, builder: AzureSSMLBuilder) -> None:
        segments = builder._parse_style_segments("[narration-relaxed] 今天天氣真好")
        assert segments[0][0] == "narration-relaxed"

    def test_underscored_style(self, builder: AzureSSMLBuilder) -> None:
        segments = builder._parse_style_segments("[sports_commentary] 球進了！")
        assert segments[0][0] == "sports_commentary"


class TestBuildTurnSsml:
    """Tests for _build_turn_ssml()."""

    def test_no_tags_backward_compatible(self, builder: AzureSSMLBuilder) -> None:
        lines = builder._build_turn_ssml("你好世界")
        assert len(lines) == 1
        assert "<prosody" in lines[0]
        assert "你好世界" in lines[0]
        assert "express-as" not in lines[0]

    def test_single_style(self, builder: AzureSSMLBuilder) -> None:
        lines = builder._build_turn_ssml("[cheerful] 太好了")
        combined = "\n".join(lines)
        assert 'style="cheerful"' in combined
        assert "<prosody" in combined
        assert "太好了" in combined

    def test_multiple_styles(self, builder: AzureSSMLBuilder) -> None:
        lines = builder._build_turn_ssml("[cheerful] 好！ [sad] 嗚嗚")
        combined = "\n".join(lines)
        assert 'style="cheerful"' in combined
        assert 'style="sad"' in combined
        assert "好！" in combined
        assert "嗚嗚" in combined

    def test_xml_escaping_in_style(self, builder: AzureSSMLBuilder) -> None:
        lines = builder._build_turn_ssml("[cheerful] Tom & Jerry <3")
        combined = "\n".join(lines)
        assert "Tom &amp; Jerry &lt;3" in combined

    def test_text_before_and_after_style(self, builder: AzureSSMLBuilder) -> None:
        lines = builder._build_turn_ssml("你好 [cheerful] 太好了")
        combined = "\n".join(lines)
        # Should have unstyled segment and styled segment
        assert 'style="cheerful"' in combined
        assert "你好" in combined
        assert "太好了" in combined


class TestBuildMultiVoiceSsml:
    """Tests for full SSML generation with style tags."""

    def test_no_tags_backward_compatible(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        turns = [
            DialogueTurn(speaker="A", text="你好", index=0),
            DialogueTurn(speaker="B", text="嗨", index=1),
        ]
        ssml = builder.build_multi_voice_ssml(turns, voice_map)
        assert "express-as" not in ssml
        assert "<prosody" in ssml
        assert "你好" in ssml
        assert "嗨" in ssml

    def test_with_style_tag(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        turns = [
            DialogueTurn(speaker="A", text="[cheerful] 太好了！", index=0),
        ]
        ssml = builder.build_multi_voice_ssml(turns, voice_map)
        assert 'style="cheerful"' in ssml
        assert "太好了！" in ssml
        assert "<mstts:express-as" in ssml

    def test_mixed_styled_and_unstyled(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        turns = [
            DialogueTurn(speaker="A", text="[cheerful] 太好了！", index=0),
            DialogueTurn(speaker="B", text="普通的回應", index=1),
        ]
        ssml = builder.build_multi_voice_ssml(turns, voice_map)
        assert 'style="cheerful"' in ssml
        assert "普通的回應" in ssml

    def test_multi_segment_in_one_turn(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        turns = [
            DialogueTurn(
                speaker="A",
                text="[cheerful] 太好了！ [sad] 可惜...",
                index=0,
            ),
        ]
        ssml = builder.build_multi_voice_ssml(turns, voice_map)
        assert 'style="cheerful"' in ssml
        assert 'style="sad"' in ssml

    def test_ssml_has_mstts_namespace(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        turns = [
            DialogueTurn(speaker="A", text="[cheerful] 好的", index=0),
        ]
        ssml = builder.build_multi_voice_ssml(turns, voice_map)
        assert "xmlns:mstts=" in ssml

    def test_xml_special_chars_escaped(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        turns = [
            DialogueTurn(speaker="A", text='[cheerful] A & B "引號"', index=0),
        ]
        ssml = builder.build_multi_voice_ssml(turns, voice_map)
        assert "&amp;" in ssml
        assert "&quot;" in ssml

    def test_unknown_tag_preserved_as_text(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        turns = [
            DialogueTurn(speaker="A", text="[notastyle] hello", index=0),
        ]
        ssml = builder.build_multi_voice_ssml(turns, voice_map)
        assert "notastyle" in ssml
        assert "hello" in ssml
        # Unknown tag should not produce express-as
        assert 'style="notastyle"' not in ssml


class TestEstimateSsmlSize:
    """Tests for estimate_ssml_size with style tags."""

    def test_no_tags_estimation(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        turns = [DialogueTurn(speaker="A", text="你好", index=0)]
        size = builder.estimate_ssml_size(turns, voice_map)
        assert size > 0

    def test_style_tags_increase_estimation(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        turns_no_style = [DialogueTurn(speaker="A", text="你好", index=0)]
        turns_with_style = [DialogueTurn(speaker="A", text="[cheerful] 你好", index=0)]
        size_no = builder.estimate_ssml_size(turns_no_style, voice_map)
        size_with = builder.estimate_ssml_size(turns_with_style, voice_map)
        assert size_with > size_no


class TestKnownStyles:
    """Tests for KNOWN_STYLES constant."""

    def test_contains_common_styles(self) -> None:
        for style in [
            "cheerful",
            "sad",
            "angry",
            "calm",
            "excited",
            "friendly",
            "whispering",
            "shouting",
        ]:
            assert style in KNOWN_STYLES

    def test_contains_hyphenated_styles(self) -> None:
        for style in [
            "narration-professional",
            "narration-relaxed",
            "newscast-casual",
            "newscast-formal",
            "documentary-narration",
            "poetry-reading",
        ]:
            assert style in KNOWN_STYLES

    def test_contains_underscored_styles(self) -> None:
        for style in [
            "sports_commentary",
            "sports_commentary_excited",
            "advertisement_upbeat",
        ]:
            assert style in KNOWN_STYLES
