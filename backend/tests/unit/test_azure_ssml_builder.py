"""Unit tests for Azure SSML Builder express-as style tag support."""

import re
import xml.etree.ElementTree as ET

import pytest

from src.domain.entities.multi_role_tts import DialogueTurn
from src.infrastructure.providers.tts.multi_role.azure_ssml_builder import (
    KNOWN_STYLES,
    AzureSSMLBuilder,
    strip_style_tags,
)

# Azure SSML namespaces
NS = {
    "s": "http://www.w3.org/2001/10/synthesis",
    "mstts": "https://www.w3.org/2001/mstts",
}


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


class TestBreakTagPlacement:
    """Tests that <break> tags are correctly placed inside <voice> elements."""

    def test_break_inside_voice_not_speak(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        """Break tags must be inside <voice>, not directly under <speak>."""
        turns = [
            DialogueTurn(speaker="A", text="你好", index=0),
            DialogueTurn(speaker="B", text="嗨", index=1),
        ]
        ssml = builder.build_multi_voice_ssml(turns, voice_map)
        # Break should NOT appear between </voice> and <voice> at the same level as <speak>
        assert "</voice>\n    <break" not in ssml
        # Break should appear inside the second <voice> block
        assert "<voice" in ssml
        assert "<break time=" in ssml

    def test_break_inside_second_voice_block(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        """Break should be the first child of non-first <voice> elements."""
        turns = [
            DialogueTurn(speaker="A", text="你好", index=0),
            DialogueTurn(speaker="B", text="嗨", index=1),
        ]
        ssml = builder.build_multi_voice_ssml(turns, voice_map)
        lines = ssml.split("\n")
        # Find lines with <voice> and <break>
        voice_indices = [i for i, line in enumerate(lines) if "<voice name=" in line]
        break_indices = [i for i, line in enumerate(lines) if "<break time=" in line]

        assert len(voice_indices) == 2
        assert len(break_indices) == 1
        # Break should come after the second <voice> tag, before its prosody
        assert break_indices[0] > voice_indices[1]

    def test_no_break_before_first_voice(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        """No break tag should appear before the first voice element."""
        turns = [
            DialogueTurn(speaker="A", text="你好", index=0),
            DialogueTurn(speaker="B", text="嗨", index=1),
        ]
        ssml = builder.build_multi_voice_ssml(turns, voice_map)
        lines = ssml.split("\n")
        first_voice = next(i for i, line in enumerate(lines) if "<voice name=" in line)
        # No break should appear before the first voice
        for i in range(first_voice):
            assert "<break" not in lines[i]

    def test_no_break_with_single_turn(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        """Single turn should have no break tags at all."""
        turns = [DialogueTurn(speaker="A", text="你好", index=0)]
        ssml = builder.build_multi_voice_ssml(turns, voice_map)
        assert "<break" not in ssml

    def test_no_break_when_gap_is_zero(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        """When gap_ms=0, no break tags should be generated."""
        turns = [
            DialogueTurn(speaker="A", text="你好", index=0),
            DialogueTurn(speaker="B", text="嗨", index=1),
        ]
        ssml = builder.build_multi_voice_ssml(turns, voice_map, gap_ms=0)
        assert "<break" not in ssml

    def test_three_turns_have_two_breaks(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        """Three turns should produce exactly two break tags."""
        voice_map_3 = {**voice_map, "C": "zh-TW-HsiaoYuNeural"}
        turns = [
            DialogueTurn(speaker="A", text="一", index=0),
            DialogueTurn(speaker="B", text="二", index=1),
            DialogueTurn(speaker="C", text="三", index=2),
        ]
        ssml = builder.build_multi_voice_ssml(turns, voice_map_3)
        break_count = ssml.count("<break time=")
        assert break_count == 2

    def test_break_with_style_tags(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        """Break and style tags should coexist correctly within <voice>."""
        turns = [
            DialogueTurn(speaker="A", text="你好", index=0),
            DialogueTurn(speaker="B", text="[cheerful] 太好了！", index=1),
        ]
        ssml = builder.build_multi_voice_ssml(turns, voice_map)
        # Both break and express-as should be inside the second <voice>
        assert "<break time=" in ssml
        assert 'style="cheerful"' in ssml
        # Validate structure: voice > break > express-as
        lines = ssml.split("\n")
        second_voice = None
        break_line = None
        express_line = None
        for i, line in enumerate(lines):
            if "<voice name=" in line and second_voice is None and i > 0:
                second_voice = i
                continue
            if second_voice and "<break" in line and break_line is None:
                break_line = i
            if second_voice and "express-as" in line and express_line is None:
                express_line = i
        assert break_line is not None
        assert express_line is not None
        assert break_line < express_line


class TestStripStyleTags:
    """Tests for the strip_style_tags() utility function."""

    def test_strip_known_tag(self) -> None:
        assert strip_style_tags("[cheerful] 太好了") == "太好了"

    def test_strip_multiple_known_tags(self) -> None:
        result = strip_style_tags("[cheerful] 好！ [sad] 嗚嗚")
        assert "cheerful" not in result
        assert "sad" not in result
        assert "好！" in result
        assert "嗚嗚" in result

    def test_preserve_unknown_tag(self) -> None:
        result = strip_style_tags("[fakestyle] hello")
        assert "[fakestyle]" in result
        assert "hello" in result

    def test_case_insensitive_stripping(self) -> None:
        assert strip_style_tags("[Cheerful] 太好了") == "太好了"
        assert strip_style_tags("[CHEERFUL] 太好了") == "太好了"

    def test_strip_hyphenated_style(self) -> None:
        assert strip_style_tags("[narration-relaxed] 今天天氣真好") == "今天天氣真好"

    def test_strip_underscored_style(self) -> None:
        assert strip_style_tags("[sports_commentary] 球進了！") == "球進了！"

    def test_no_tags_returns_same(self) -> None:
        assert strip_style_tags("普通的文字") == "普通的文字"

    def test_empty_string(self) -> None:
        assert strip_style_tags("") == ""

    def test_only_tag_returns_empty(self) -> None:
        assert strip_style_tags("[cheerful]") == ""

    def test_mixed_known_and_unknown(self) -> None:
        result = strip_style_tags("[cheerful] 好！ [notreal] 測試")
        assert "cheerful" not in result
        assert "[notreal]" in result
        assert "好！" in result
        assert "測試" in result

    def test_tag_in_middle_of_text(self) -> None:
        result = strip_style_tags("你好 [cheerful] 太好了 再見")
        assert result == "你好  太好了 再見"

    def test_all_known_styles_stripped(self) -> None:
        """Verify every style in KNOWN_STYLES is properly stripped."""
        for style in KNOWN_STYLES:
            text = f"[{style}] test text"
            result = strip_style_tags(text)
            assert style not in result, f"Style '{style}' was not stripped"
            assert "test text" in result


class TestSsmlStructureValidity:
    """Tests that generated SSML has valid XML structure for Azure."""

    def test_speak_root_has_required_attributes(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        turns = [DialogueTurn(speaker="A", text="你好", index=0)]
        ssml = builder.build_multi_voice_ssml(turns, voice_map)
        assert 'version="1.0"' in ssml
        assert "xmlns=" in ssml
        assert "xmlns:mstts=" in ssml
        assert "xml:lang=" in ssml

    def test_voice_tags_properly_nested(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        """Every <voice> must have a matching </voice>."""
        turns = [
            DialogueTurn(speaker="A", text="[cheerful] 好", index=0),
            DialogueTurn(speaker="B", text="[sad] 嗚", index=1),
        ]
        ssml = builder.build_multi_voice_ssml(turns, voice_map)
        open_count = ssml.count("<voice name=")
        close_count = ssml.count("</voice>")
        assert open_count == close_count == 2

    def test_express_as_properly_nested(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        """Every <mstts:express-as> must have a matching close tag."""
        turns = [
            DialogueTurn(
                speaker="A",
                text="[cheerful] 好 [sad] 嗚",
                index=0,
            ),
        ]
        ssml = builder.build_multi_voice_ssml(turns, voice_map)
        open_count = ssml.count("<mstts:express-as")
        close_count = ssml.count("</mstts:express-as>")
        assert open_count == close_count == 2

    def test_no_break_as_direct_child_of_speak(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        """Validate <break> never appears between </voice> and next <voice>."""
        voice_map_3 = {**voice_map, "C": "zh-TW-HsiaoYuNeural"}
        turns = [
            DialogueTurn(speaker="A", text="一", index=0),
            DialogueTurn(speaker="B", text="二", index=1),
            DialogueTurn(speaker="C", text="三", index=2),
        ]
        ssml = builder.build_multi_voice_ssml(turns, voice_map_3)
        # Use regex to check no <break> appears between </voice> and <voice>
        between_voices = re.findall(r"</voice>(.*?)<voice", ssml, re.DOTALL)
        for segment in between_voices:
            assert "<break" not in segment, f"Found <break> between </voice> and <voice>: {segment}"

    def test_custom_gap_value(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        turns = [
            DialogueTurn(speaker="A", text="一", index=0),
            DialogueTurn(speaker="B", text="二", index=1),
        ]
        ssml = builder.build_multi_voice_ssml(turns, voice_map, gap_ms=500)
        assert '<break time="500ms"/>' in ssml


class TestStyleTagToAzureSsmlConversion:
    """Verify [style] tags are converted to valid Azure SSML via XML parsing.

    Azure expects:
      <voice name="...">
        <mstts:express-as style="cheerful">
          <prosody rate="..." pitch="...">text</prosody>
        </mstts:express-as>
      </voice>
    """

    def _parse_ssml(self, ssml: str) -> ET.Element:
        """Parse SSML string into an XML element tree."""
        return ET.fromstring(ssml)

    def test_single_style_produces_valid_xml(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        """[cheerful] text -> valid XML with express-as wrapping prosody."""
        turns = [DialogueTurn(speaker="A", text="[cheerful] 太好了！", index=0)]
        ssml = builder.build_multi_voice_ssml(turns, voice_map)
        root = self._parse_ssml(ssml)

        # Root is <speak>
        assert root.tag == "{http://www.w3.org/2001/10/synthesis}speak"

        # First child is <voice>
        voice = root.find("s:voice", NS)
        assert voice is not None
        assert voice.get("name") == "zh-TW-HsiaoChenNeural"

        # Inside <voice>: <mstts:express-as style="cheerful">
        express_as = voice.find("mstts:express-as", NS)
        assert express_as is not None
        assert express_as.get("style") == "cheerful"

        # Inside <express-as>: <prosody> with text
        prosody = express_as.find("s:prosody", NS)
        assert prosody is not None
        assert prosody.text is not None
        assert "太好了！" in prosody.text

    def test_multiple_styles_in_one_turn(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        """[cheerful] text [sad] text -> two express-as blocks in one voice."""
        turns = [
            DialogueTurn(
                speaker="A",
                text="[cheerful] 好開心！ [sad] 好難過...",
                index=0,
            )
        ]
        ssml = builder.build_multi_voice_ssml(turns, voice_map)
        root = self._parse_ssml(ssml)

        voice = root.find("s:voice", NS)
        assert voice is not None

        express_as_list = voice.findall("mstts:express-as", NS)
        assert len(express_as_list) == 2

        assert express_as_list[0].get("style") == "cheerful"
        prosody_0 = express_as_list[0].find("s:prosody", NS)
        assert prosody_0 is not None
        assert prosody_0.text is not None
        assert "好開心！" in prosody_0.text

        assert express_as_list[1].get("style") == "sad"
        prosody_1 = express_as_list[1].find("s:prosody", NS)
        assert prosody_1 is not None
        assert prosody_1.text is not None
        assert "好難過..." in prosody_1.text

    def test_unstyled_text_uses_plain_prosody(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        """Plain text without [style] -> <prosody> directly in <voice>, no express-as."""
        turns = [DialogueTurn(speaker="A", text="普通文字", index=0)]
        ssml = builder.build_multi_voice_ssml(turns, voice_map)
        root = self._parse_ssml(ssml)

        voice = root.find("s:voice", NS)
        assert voice is not None

        # No express-as
        assert voice.find("mstts:express-as", NS) is None

        # Direct prosody child
        prosody = voice.find("s:prosody", NS)
        assert prosody is not None
        assert prosody.text is not None
        assert "普通文字" in prosody.text

    def test_mixed_styled_and_unstyled_in_one_turn(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        """Prefix text [cheerful] styled text -> prosody + express-as>prosody."""
        turns = [DialogueTurn(speaker="A", text="你好 [cheerful] 太好了", index=0)]
        ssml = builder.build_multi_voice_ssml(turns, voice_map)
        root = self._parse_ssml(ssml)

        voice = root.find("s:voice", NS)
        assert voice is not None

        children = list(voice)
        # First child: plain <prosody> for "你好"
        assert children[0].tag == "{http://www.w3.org/2001/10/synthesis}prosody"
        assert children[0].text is not None
        assert "你好" in children[0].text

        # Second child: <mstts:express-as> for "太好了"
        assert children[1].tag == "{https://www.w3.org/2001/mstts}express-as"
        assert children[1].get("style") == "cheerful"
        inner_prosody = children[1].find("s:prosody", NS)
        assert inner_prosody is not None
        assert inner_prosody.text is not None
        assert "太好了" in inner_prosody.text

    def test_multi_voice_with_styles_and_break(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        """Multi-turn dialogue with styles -> correct voice/break/express-as nesting."""
        turns = [
            DialogueTurn(speaker="A", text="[excited] 歡迎！", index=0),
            DialogueTurn(speaker="B", text="[calm] 謝謝邀請", index=1),
        ]
        ssml = builder.build_multi_voice_ssml(turns, voice_map, gap_ms=300)
        root = self._parse_ssml(ssml)

        voices = root.findall("s:voice", NS)
        assert len(voices) == 2

        # Voice A: express-as style="excited"
        ea_a = voices[0].find("mstts:express-as", NS)
        assert ea_a is not None
        assert ea_a.get("style") == "excited"

        # Voice B: should have <break> then <express-as style="calm">
        children_b = list(voices[1])
        # First child is <break>
        assert children_b[0].tag == "{http://www.w3.org/2001/10/synthesis}break"
        assert children_b[0].get("time") == "300ms"
        # Second child is <mstts:express-as>
        assert children_b[1].tag == "{https://www.w3.org/2001/mstts}express-as"
        assert children_b[1].get("style") == "calm"

    def test_all_common_styles_produce_valid_express_as(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        """Every common Azure style should produce parseable express-as XML."""
        common_styles = [
            "cheerful",
            "sad",
            "angry",
            "calm",
            "excited",
            "friendly",
            "narration-relaxed",
            "narration-professional",
            "newscast",
            "newscast-casual",
            "whispering",
            "shouting",
            "sports_commentary",
            "documentary-narration",
        ]
        for style in common_styles:
            turns = [DialogueTurn(speaker="A", text=f"[{style}] 測試文字", index=0)]
            ssml = builder.build_multi_voice_ssml(turns, voice_map)

            # Must be valid XML
            root = self._parse_ssml(ssml)
            voice = root.find("s:voice", NS)
            assert voice is not None, f"No <voice> found for style '{style}'"

            ea = voice.find("mstts:express-as", NS)
            assert ea is not None, f"No <express-as> for style '{style}'"
            assert ea.get("style") == style, f"Expected style='{style}', got '{ea.get('style')}'"

            prosody = ea.find("s:prosody", NS)
            assert prosody is not None, f"No <prosody> inside express-as for '{style}'"
            assert prosody.text is not None and "測試文字" in prosody.text

    def test_unknown_tag_not_converted_to_express_as(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        """[unknowntag] should remain as literal text, not become express-as."""
        turns = [DialogueTurn(speaker="A", text="[fakestyle] 測試", index=0)]
        ssml = builder.build_multi_voice_ssml(turns, voice_map)
        root = self._parse_ssml(ssml)

        voice = root.find("s:voice", NS)
        assert voice is not None

        # Should NOT have express-as
        assert voice.find("mstts:express-as", NS) is None

        # Should have prosody with the tag preserved as text
        prosody = voice.find("s:prosody", NS)
        assert prosody is not None
        assert prosody.text is not None
        assert "[fakestyle]" in prosody.text

    def test_prosody_rate_and_pitch_attributes(
        self,
        builder: AzureSSMLBuilder,
        voice_map: dict[str, str],
    ) -> None:
        """Verify prosody has correct rate and pitch attributes."""
        turns = [DialogueTurn(speaker="A", text="[cheerful] 你好", index=0)]
        ssml = builder.build_multi_voice_ssml(turns, voice_map)
        root = self._parse_ssml(ssml)

        voice = root.find("s:voice", NS)
        ea = voice.find("mstts:express-as", NS)
        prosody = ea.find("s:prosody", NS)

        assert prosody.get("rate") == "+0%"
        assert prosody.get("pitch") == "+0Hz"
