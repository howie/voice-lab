"""Unit tests for TextSplitter.

Tests the text segmentation algorithm with various boundary types,
character/byte modes, and edge cases.
"""

import pytest

from src.domain.entities.long_text_tts import SplitConfig, TextSegment
from src.domain.services.text_splitter import TextSplitter


class TestTextSplitterNeedsSplitting:
    """Tests for needs_splitting() quick check."""

    def test_short_text_does_not_need_splitting_chars(self) -> None:
        splitter = TextSplitter(SplitConfig(max_chars=5000))
        assert splitter.needs_splitting("短文字") is False

    def test_long_text_needs_splitting_chars(self) -> None:
        splitter = TextSplitter(SplitConfig(max_chars=10))
        assert splitter.needs_splitting("這是一段超過十個字元的中文文字") is True

    def test_short_text_does_not_need_splitting_bytes(self) -> None:
        splitter = TextSplitter(SplitConfig(max_bytes=4000))
        assert splitter.needs_splitting("短文字") is False

    def test_long_cjk_text_needs_splitting_bytes(self) -> None:
        # Each CJK char = 3 bytes. 1400 chars = 4200 bytes > 4000
        splitter = TextSplitter(SplitConfig(max_bytes=4000))
        text = "中" * 1400
        assert splitter.needs_splitting(text) is True

    def test_exact_limit_does_not_need_splitting(self) -> None:
        splitter = TextSplitter(SplitConfig(max_chars=5))
        assert splitter.needs_splitting("12345") is False


class TestTextSplitterSingleSegment:
    """Tests for text that fits in a single segment."""

    def test_short_text_returns_single_segment(self) -> None:
        splitter = TextSplitter(SplitConfig(max_chars=5000))
        segments = splitter.split("你好世界")
        assert len(segments) == 1
        assert segments[0].text == "你好世界"
        assert segments[0].index == 0
        assert segments[0].boundary_type == "none"

    def test_single_segment_has_correct_lengths(self) -> None:
        splitter = TextSplitter(SplitConfig(max_chars=5000))
        segments = splitter.split("Hello世界")
        seg = segments[0]
        assert seg.char_length == 7
        assert seg.byte_length == len("Hello世界".encode())


class TestTextSplitterChineseSentenceBoundary:
    """Tests for splitting at Chinese sentence boundaries."""

    def test_splits_at_chinese_period(self) -> None:
        splitter = TextSplitter(SplitConfig(max_chars=15))
        text = "第一句話結束了。第二句話也結束了。"
        segments = splitter.split(text)
        assert len(segments) >= 2
        assert segments[0].text.endswith("。")
        assert segments[0].boundary_type == "sentence"

    def test_splits_at_chinese_exclamation(self) -> None:
        splitter = TextSplitter(SplitConfig(max_chars=8))
        text = "太棒了！這真的很好啊！"
        segments = splitter.split(text)
        assert len(segments) >= 2
        assert "！" in segments[0].text

    def test_splits_at_chinese_question(self) -> None:
        splitter = TextSplitter(SplitConfig(max_chars=8))
        text = "你好嗎？我很好的哦。"
        segments = splitter.split(text)
        assert len(segments) >= 2
        assert "？" in segments[0].text


class TestTextSplitterEnglishSentenceBoundary:
    """Tests for splitting at English sentence boundaries."""

    def test_splits_at_english_period(self) -> None:
        splitter = TextSplitter(SplitConfig(max_chars=30))
        text = "This is the first sentence. This is the second sentence."
        segments = splitter.split(text)
        assert len(segments) >= 2
        assert segments[0].text.strip().endswith(".")
        assert segments[0].boundary_type == "sentence"

    def test_splits_at_english_exclamation(self) -> None:
        splitter = TextSplitter(SplitConfig(max_chars=25))
        text = "What a great day! I love programming in Python."
        segments = splitter.split(text)
        assert len(segments) >= 2

    def test_splits_at_english_question(self) -> None:
        splitter = TextSplitter(SplitConfig(max_chars=25))
        text = "How are you doing today? I am doing quite well thanks."
        segments = splitter.split(text)
        assert len(segments) >= 2


class TestTextSplitterParagraphBoundary:
    """Tests for splitting at paragraph boundaries."""

    def test_splits_at_paragraph(self) -> None:
        splitter = TextSplitter(SplitConfig(max_chars=15))
        text = "第一段的內容在這裡。\n\n第二段的內容在這裡。"
        segments = splitter.split(text)
        assert len(segments) >= 2
        assert segments[0].boundary_type == "paragraph"


class TestTextSplitterClauseBoundary:
    """Tests for falling back to clause boundaries."""

    def test_splits_at_chinese_comma_when_no_sentence_boundary(self) -> None:
        splitter = TextSplitter(SplitConfig(max_chars=10))
        # No sentence-ending punctuation, only commas
        text = "第一部分，第二部分，第三部分"
        segments = splitter.split(text)
        assert len(segments) >= 2
        assert segments[0].boundary_type == "clause"

    def test_splits_at_chinese_semicolon(self) -> None:
        splitter = TextSplitter(SplitConfig(max_chars=10))
        text = "前半段；後半段再加一些"
        segments = splitter.split(text)
        assert len(segments) >= 2


class TestTextSplitterHardCut:
    """Tests for hard cut fallback when no boundary is found."""

    def test_hard_cut_on_continuous_text(self) -> None:
        splitter = TextSplitter(SplitConfig(max_chars=10))
        # No punctuation at all
        text = "一二三四五六七八九十壹貳參肆伍"
        segments = splitter.split(text)
        assert len(segments) >= 2
        assert segments[0].boundary_type == "hard"
        assert segments[0].char_length <= 10


class TestTextSplitterByteBased:
    """Tests for byte-based splitting (Gemini scenario)."""

    def test_byte_splitting_cjk(self) -> None:
        # Each CJK char = 3 bytes. With max_bytes=30, max ~10 CJK chars
        splitter = TextSplitter(SplitConfig(max_bytes=30))
        text = "一二三四五六七八九十壹貳參肆伍陸柒捌玖廿"  # 20 chars = 60 bytes
        segments = splitter.split(text)
        assert len(segments) >= 2
        for seg in segments:
            assert seg.byte_length <= 30

    def test_byte_splitting_mixed_ascii_cjk(self) -> None:
        # ASCII = 1 byte, CJK = 3 bytes
        splitter = TextSplitter(SplitConfig(max_bytes=20))
        text = "Hello世界你好World再見"
        segments = splitter.split(text)
        assert len(segments) >= 2
        for seg in segments:
            assert seg.byte_length <= 20

    def test_byte_splitting_gemini_scenario(self) -> None:
        """Simulate Gemini's 4000 byte limit with CJK text."""
        splitter = TextSplitter(SplitConfig(max_bytes=4000))
        # 2000 CJK chars = 6000 bytes, should split into 2+ segments
        text = "。".join(["這是一段測試用的句子"] * 200)
        segments = splitter.split(text)
        assert len(segments) >= 2
        for seg in segments:
            assert seg.byte_length <= 4000


class TestTextSplitterCharBased:
    """Tests for character-based splitting (Azure/ElevenLabs scenario)."""

    def test_char_splitting(self) -> None:
        splitter = TextSplitter(SplitConfig(max_chars=50))
        text = "。".join(["這是一段句子"] * 20)
        segments = splitter.split(text)
        assert len(segments) >= 2
        for seg in segments:
            assert seg.char_length <= 50


class TestTextSplitterEdgeCases:
    """Tests for edge cases."""

    def test_empty_text_raises_error(self) -> None:
        splitter = TextSplitter(SplitConfig(max_chars=5000))
        with pytest.raises(ValueError, match="Text cannot be empty"):
            splitter.split("")

    def test_whitespace_only_raises_error(self) -> None:
        splitter = TextSplitter(SplitConfig(max_chars=5000))
        with pytest.raises(ValueError, match="Text cannot be empty"):
            splitter.split("   ")

    def test_segments_cover_entire_text(self) -> None:
        """Verify no text is lost during splitting."""
        splitter = TextSplitter(SplitConfig(max_chars=20))
        text = "第一句話。第二句話。第三句話。第四句話。"
        segments = splitter.split(text)
        reconstructed = "".join(seg.text for seg in segments)
        assert reconstructed == text

    def test_segment_indices_are_sequential(self) -> None:
        splitter = TextSplitter(SplitConfig(max_chars=10))
        text = "第一段。第二段。第三段。第四段。"
        segments = splitter.split(text)
        for i, seg in enumerate(segments):
            assert seg.index == i

    def test_all_segments_are_valid_text_segments(self) -> None:
        splitter = TextSplitter(SplitConfig(max_chars=15))
        text = "第一句話。第二句話。第三句話。"
        segments = splitter.split(text)
        for seg in segments:
            assert isinstance(seg, TextSegment)
            assert seg.text
            assert seg.byte_length == len(seg.text.encode("utf-8"))
            assert seg.char_length == len(seg.text)
