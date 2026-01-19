"""Unit tests for WER/CER calculator.

Feature: 003-stt-testing-module - User Story 3
Task: T045, T046 - Unit tests for WER/CER calculation
"""

import pytest

from src.domain.services.wer_calculator import (
    calculate_alignment,
    calculate_cer,
    calculate_error_rate,
    calculate_wer,
)


class TestWERCalculation:
    """Tests for Word Error Rate (WER) calculation."""

    def test_wer_perfect_match(self) -> None:
        """Test WER with perfect match (0.0)."""
        reference = "hello world this is a test"
        hypothesis = "hello world this is a test"
        assert calculate_wer(reference, hypothesis) == 0.0

    def test_wer_complete_mismatch(self) -> None:
        """Test WER with complete mismatch."""
        reference = "hello world"
        hypothesis = "foo bar"
        wer = calculate_wer(reference, hypothesis)
        assert wer == 1.0  # 2 substitutions / 2 words

    def test_wer_single_substitution(self) -> None:
        """Test WER with one word substituted."""
        reference = "hello world"
        hypothesis = "hello earth"
        wer = calculate_wer(reference, hypothesis)
        assert wer == 0.5  # 1 substitution / 2 words

    def test_wer_single_insertion(self) -> None:
        """Test WER with one word inserted."""
        reference = "hello world"
        hypothesis = "hello beautiful world"
        wer = calculate_wer(reference, hypothesis)
        assert wer == 0.5  # 1 insertion / 2 words

    def test_wer_single_deletion(self) -> None:
        """Test WER with one word deleted."""
        reference = "hello beautiful world"
        hypothesis = "hello world"
        wer = calculate_wer(reference, hypothesis)
        assert wer == pytest.approx(0.333, rel=0.01)  # 1 deletion / 3 words

    def test_wer_empty_reference(self) -> None:
        """Test WER with empty reference."""
        assert calculate_wer("", "hello") == 1.0
        assert calculate_wer("", "") == 0.0

    def test_wer_empty_hypothesis(self) -> None:
        """Test WER with empty hypothesis."""
        assert calculate_wer("hello world", "") == 1.0

    def test_wer_whitespace_normalization(self) -> None:
        """Test WER normalizes whitespace."""
        reference = "  hello   world  "
        hypothesis = "hello world"
        assert calculate_wer(reference, hypothesis) == 0.0


class TestCERCalculation:
    """Tests for Character Error Rate (CER) calculation."""

    def test_cer_perfect_match_chinese(self) -> None:
        """Test CER with perfect Chinese match."""
        reference = "你好世界"
        hypothesis = "你好世界"
        assert calculate_cer(reference, hypothesis) == 0.0

    def test_cer_single_substitution_chinese(self) -> None:
        """Test CER with one Chinese character substituted."""
        reference = "你好世界"
        hypothesis = "你號世界"
        cer = calculate_cer(reference, hypothesis)
        assert cer == 0.25  # 1 substitution / 4 characters

    def test_cer_ignores_spaces(self) -> None:
        """Test CER ignores whitespace."""
        reference = "你好 世界"
        hypothesis = "你好世界"
        assert calculate_cer(reference, hypothesis) == 0.0

    def test_cer_japanese(self) -> None:
        """Test CER with Japanese text."""
        reference = "こんにちは世界"
        hypothesis = "こんにちわ世界"
        cer = calculate_cer(reference, hypothesis)
        assert cer == pytest.approx(0.142, rel=0.01)  # 1 / 7

    def test_cer_korean(self) -> None:
        """Test CER with Korean text."""
        reference = "안녕하세요"
        hypothesis = "안녕하새요"
        cer = calculate_cer(reference, hypothesis)
        assert cer == 0.2  # 1 / 5

    def test_cer_mixed_cjk_english(self) -> None:
        """Test CER with mixed CJK and English."""
        reference = "Hello世界"
        hypothesis = "Hello世間"
        cer = calculate_cer(reference, hypothesis)
        # "Hello世界" -> 7 chars (spaces removed), 1 substitution
        assert cer == pytest.approx(0.143, rel=0.01)  # 1 / 7

    def test_cer_empty_reference(self) -> None:
        """Test CER with empty reference."""
        assert calculate_cer("", "你好") == 1.0
        assert calculate_cer("", "") == 0.0


class TestErrorRateAutoSelection:
    """Tests for automatic WER/CER selection based on language."""

    def test_auto_selects_cer_for_zh_tw(self) -> None:
        """Test auto-selects CER for Traditional Chinese."""
        reference = "你好世界"
        hypothesis = "你號世界"
        rate, error_type = calculate_error_rate(reference, hypothesis, "zh-TW")
        assert error_type == "CER"
        assert rate == 0.25

    def test_auto_selects_cer_for_zh_cn(self) -> None:
        """Test auto-selects CER for Simplified Chinese."""
        reference = "你好世界"
        hypothesis = "你號世界"
        rate, error_type = calculate_error_rate(reference, hypothesis, "zh-CN")
        assert error_type == "CER"
        assert rate == 0.25

    def test_auto_selects_cer_for_ja_jp(self) -> None:
        """Test auto-selects CER for Japanese."""
        reference = "こんにちは"
        hypothesis = "こんにちわ"
        rate, error_type = calculate_error_rate(reference, hypothesis, "ja-JP")
        assert error_type == "CER"
        assert rate == 0.2

    def test_auto_selects_cer_for_ko_kr(self) -> None:
        """Test auto-selects CER for Korean."""
        reference = "안녕하세요"
        hypothesis = "안녕하새요"
        rate, error_type = calculate_error_rate(reference, hypothesis, "ko-KR")
        assert error_type == "CER"
        assert rate == 0.2

    def test_auto_selects_wer_for_en_us(self) -> None:
        """Test auto-selects WER for English."""
        reference = "hello world"
        hypothesis = "hello earth"
        rate, error_type = calculate_error_rate(reference, hypothesis, "en-US")
        assert error_type == "WER"
        assert rate == 0.5

    def test_auto_selects_wer_for_unknown_language(self) -> None:
        """Test defaults to WER for unknown language."""
        reference = "hello world"
        hypothesis = "hello earth"
        rate, error_type = calculate_error_rate(reference, hypothesis, "fr-FR")
        assert error_type == "WER"
        assert rate == 0.5


class TestAlignment:
    """Tests for alignment calculation."""

    def test_alignment_perfect_match(self) -> None:
        """Test alignment with perfect match."""
        ref = ["hello", "world"]
        hyp = ["hello", "world"]
        alignment, insertions, deletions, substitutions = calculate_alignment(ref, hyp)

        assert len(alignment) == 2
        assert insertions == 0
        assert deletions == 0
        assert substitutions == 0
        assert all(op == "match" for _, _, op in alignment)

    def test_alignment_substitution(self) -> None:
        """Test alignment with substitution."""
        ref = ["hello", "world"]
        hyp = ["hello", "earth"]
        alignment, insertions, deletions, substitutions = calculate_alignment(ref, hyp)

        assert insertions == 0
        assert deletions == 0
        assert substitutions == 1
        assert alignment[0] == ("hello", "hello", "match")
        assert alignment[1] == ("world", "earth", "substitute")

    def test_alignment_insertion(self) -> None:
        """Test alignment with insertion."""
        ref = ["hello", "world"]
        hyp = ["hello", "beautiful", "world"]
        alignment, insertions, deletions, substitutions = calculate_alignment(ref, hyp)

        assert insertions == 1
        assert deletions == 0
        assert substitutions == 0

    def test_alignment_deletion(self) -> None:
        """Test alignment with deletion."""
        ref = ["hello", "beautiful", "world"]
        hyp = ["hello", "world"]
        alignment, insertions, deletions, substitutions = calculate_alignment(ref, hyp)

        assert insertions == 0
        assert deletions == 1
        assert substitutions == 0

    def test_alignment_mixed_operations(self) -> None:
        """Test alignment with mixed operations."""
        ref = ["the", "quick", "brown", "fox"]
        hyp = ["the", "slow", "fox"]
        alignment, insertions, deletions, substitutions = calculate_alignment(ref, hyp)

        assert insertions == 0
        assert deletions == 1  # "brown" deleted
        assert substitutions == 1  # "quick" -> "slow"
        assert len(alignment) == 4

    def test_alignment_chinese_characters(self) -> None:
        """Test alignment with Chinese characters."""
        ref = list("你好世界")
        hyp = list("你號世界")
        alignment, insertions, deletions, substitutions = calculate_alignment(ref, hyp)

        assert insertions == 0
        assert deletions == 0
        assert substitutions == 1
        assert alignment[1] == ("好", "號", "substitute")
