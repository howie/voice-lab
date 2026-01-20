"""Unit tests for dialogue parser.

TDD-Red: These tests are written FIRST and should FAIL until implementation.
"""

import pytest

from src.domain.services.dialogue_parser import parse_dialogue


class TestParseDialogueLetterFormat:
    """Test parsing dialogue with letter format (A: text)."""

    def test_parse_simple_two_speakers(self) -> None:
        """Parse simple A/B dialogue."""
        text = "A: 你好 B: 嗨，你好嗎？"
        turns, speakers = parse_dialogue(text)

        assert len(turns) == 2
        assert turns[0].speaker == "A"
        assert turns[0].text == "你好"
        assert turns[0].index == 0
        assert turns[1].speaker == "B"
        assert turns[1].text == "嗨，你好嗎？"
        assert turns[1].index == 1
        assert speakers == ["A", "B"]

    def test_parse_three_speakers(self) -> None:
        """Parse dialogue with three speakers."""
        text = "A: 早安 B: 早 C: 大家好"
        turns, speakers = parse_dialogue(text)

        assert len(turns) == 3
        assert set(speakers) == {"A", "B", "C"}

    def test_parse_alternating_speakers(self) -> None:
        """Parse dialogue with alternating speakers."""
        text = "A: 第一句 B: 第二句 A: 第三句 B: 第四句"
        turns, speakers = parse_dialogue(text)

        assert len(turns) == 4
        assert turns[0].speaker == "A"
        assert turns[2].speaker == "A"
        assert speakers == ["A", "B"]  # Unique speakers only

    def test_parse_multiline_format(self) -> None:
        """Parse dialogue in multiline format."""
        text = """A: 這是第一行
B: 這是第二行
A: 這是第三行"""
        turns, speakers = parse_dialogue(text)

        assert len(turns) == 3
        assert turns[0].text == "這是第一行"
        assert turns[1].text == "這是第二行"


class TestParseDialogueBracketFormat:
    """Test parsing dialogue with bracket format ([Host]: text)."""

    def test_parse_bracket_format(self) -> None:
        """Parse dialogue with bracket speaker names."""
        text = "[Host]: 歡迎收聽 [Guest]: 謝謝邀請"
        turns, speakers = parse_dialogue(text)

        assert len(turns) == 2
        assert turns[0].speaker == "Host"
        assert turns[1].speaker == "Guest"
        assert speakers == ["Host", "Guest"]

    def test_parse_chinese_speaker_names(self) -> None:
        """Parse dialogue with Chinese speaker names."""
        text = "[主持人]: 今天的話題 [來賓]: 很有趣"
        turns, speakers = parse_dialogue(text)

        assert len(turns) == 2
        assert turns[0].speaker == "主持人"
        assert turns[1].speaker == "來賓"


class TestParseDialogueMixedFormat:
    """Test parsing dialogue with mixed formats."""

    def test_parse_mixed_letter_and_bracket(self) -> None:
        """Parse dialogue mixing letter and bracket formats."""
        text = "A: 你好 [Host]: 歡迎 B: 謝謝"
        turns, speakers = parse_dialogue(text)

        assert len(turns) == 3
        assert turns[0].speaker == "A"
        assert turns[1].speaker == "Host"
        assert turns[2].speaker == "B"


class TestParseDialogueColonVariants:
    """Test parsing with different colon characters."""

    def test_parse_chinese_colon(self) -> None:
        """Parse dialogue with Chinese full-width colon."""
        text = "A：你好 B：嗨"
        turns, speakers = parse_dialogue(text)

        assert len(turns) == 2
        assert turns[0].speaker == "A"
        assert turns[0].text == "你好"

    def test_parse_mixed_colons(self) -> None:
        """Parse dialogue mixing English and Chinese colons."""
        text = "A: 英文冒號 B：中文冒號"
        turns, speakers = parse_dialogue(text)

        assert len(turns) == 2


class TestParseDialogueEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_input_raises_error(self) -> None:
        """Empty input should raise ValueError."""
        with pytest.raises(ValueError, match="empty"):
            parse_dialogue("")

    def test_whitespace_only_raises_error(self) -> None:
        """Whitespace-only input should raise ValueError."""
        with pytest.raises(ValueError, match="empty"):
            parse_dialogue("   \n\t  ")

    def test_invalid_format_raises_error(self) -> None:
        """Input without valid speaker format should raise ValueError."""
        with pytest.raises(ValueError, match="format"):
            parse_dialogue("這是一段沒有說話者的文字")

    def test_too_many_speakers_raises_error(self) -> None:
        """More than 6 speakers should raise ValueError."""
        text = "A: 1 B: 2 C: 3 D: 4 E: 5 F: 6 G: 7"
        with pytest.raises(ValueError, match="6"):
            parse_dialogue(text)

    def test_exactly_six_speakers_allowed(self) -> None:
        """Exactly 6 speakers should be allowed."""
        text = "A: 1 B: 2 C: 3 D: 4 E: 5 F: 6"
        turns, speakers = parse_dialogue(text)

        assert len(speakers) == 6

    def test_preserve_text_whitespace(self) -> None:
        """Text content whitespace should be preserved."""
        text = "A: 有  空格  的文字"
        turns, _ = parse_dialogue(text)

        # Leading/trailing whitespace stripped, internal preserved
        assert "空格" in turns[0].text

    def test_speaker_name_max_length(self) -> None:
        """Speaker names longer than 50 characters should be rejected."""
        long_name = "A" * 51
        text = f"[{long_name}]: 測試"
        with pytest.raises(ValueError, match="50"):
            parse_dialogue(text)


class TestParseDialogueReturnTypes:
    """Test return type structure."""

    def test_returns_tuple(self) -> None:
        """parse_dialogue should return a tuple."""
        result = parse_dialogue("A: test")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_turns_are_dialogue_turn_objects(self) -> None:
        """Turns should be DialogueTurn dataclass instances."""
        from src.domain.entities.multi_role_tts import DialogueTurn

        turns, _ = parse_dialogue("A: test")
        assert all(isinstance(t, DialogueTurn) for t in turns)

    def test_speakers_are_unique_list(self) -> None:
        """Speakers should be a unique list in order of appearance."""
        text = "A: 1 B: 2 A: 3 C: 4 B: 5"
        _, speakers = parse_dialogue(text)

        assert speakers == ["A", "B", "C"]  # Order of first appearance
