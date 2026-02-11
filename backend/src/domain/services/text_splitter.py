"""Text splitter for long text TTS segmentation.

Splits text into segments that respect provider-specific byte/character limits,
prioritizing semantic boundaries (paragraphs > sentences > clauses > hard cut).
"""

from src.domain.entities.long_text_tts import SplitConfig, TextSegment


class TextSplitter:
    """Splits long text into provider-safe segments at semantic boundaries."""

    # Boundary patterns in priority order (highest first)
    _PARAGRAPH_BOUNDARY = "\n\n"
    _SENTENCE_BOUNDARIES_ZH = ("。", "！", "？")
    _SENTENCE_BOUNDARIES_EN = (". ", "! ", "? ")
    _CLAUSE_BOUNDARIES_ZH = ("，", "；", "：")
    _CLAUSE_BOUNDARIES_EN = (", ", "; ", ": ")

    def __init__(self, config: SplitConfig) -> None:
        self._config = config

    def needs_splitting(self, text: str) -> bool:
        """Check if text exceeds the configured limit and needs segmentation."""
        if self._config.max_bytes is not None:
            return len(text.encode("utf-8")) > self._config.max_bytes
        if self._config.max_chars is not None:
            return len(text) > self._config.max_chars
        return False  # pragma: no cover

    def split(self, text: str) -> list[TextSegment]:
        """Split text into segments respecting provider limits.

        Args:
            text: Input text to split.

        Returns:
            List of TextSegment objects covering the entire input text.

        Raises:
            ValueError: If text is empty or whitespace-only.
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        if not self.needs_splitting(text):
            return [self._make_segment(text, index=0, boundary_type="none")]

        segments: list[TextSegment] = []
        remaining = text
        index = 0

        while remaining:
            max_pos = self._get_max_char_position(remaining)

            if max_pos >= len(remaining):
                # Remaining text fits in one segment
                segments.append(self._make_segment(remaining, index, "none"))
                break

            cut_pos, boundary_type = self._find_best_boundary(remaining, max_pos)
            segment_text = remaining[:cut_pos]
            segments.append(self._make_segment(segment_text, index, boundary_type))

            remaining = remaining[cut_pos:]
            index += 1

        return segments

    def _get_max_char_position(self, text: str) -> int:
        """Get the maximum character position that fits within the limit."""
        if self._config.max_bytes is not None:
            return self._byte_limit_to_char_pos(text, self._config.max_bytes)
        if self._config.max_chars is not None:
            return self._config.max_chars
        return len(text)  # pragma: no cover

    def _find_best_boundary(self, text: str, max_pos: int) -> tuple[int, str]:
        """Find the best split point within max_pos characters.

        Searches for boundaries in priority order:
        paragraph > ZH sentence > EN sentence > ZH clause > EN clause > hard cut.

        Returns:
            Tuple of (cut_position, boundary_type).
        """
        window = text[:max_pos]

        # Priority 1: Paragraph boundary
        pos = window.rfind(self._PARAGRAPH_BOUNDARY)
        if pos > 0:
            return pos + len(self._PARAGRAPH_BOUNDARY), "paragraph"

        # Priority 2: Chinese sentence-end
        best_pos = self._rfind_any(window, self._SENTENCE_BOUNDARIES_ZH)
        if best_pos > 0:
            return best_pos + 1, "sentence"  # +1 to include the punctuation

        # Priority 3: English sentence-end
        best_pos = self._rfind_any(window, self._SENTENCE_BOUNDARIES_EN)
        if best_pos > 0:
            return best_pos + 2, "sentence"  # +2 to include ". " (punct + space)

        # Priority 4: Chinese clause boundary
        best_pos = self._rfind_any(window, self._CLAUSE_BOUNDARIES_ZH)
        if best_pos > 0:
            return best_pos + 1, "clause"

        # Priority 5: English clause boundary
        best_pos = self._rfind_any(window, self._CLAUSE_BOUNDARIES_EN)
        if best_pos > 0:
            return best_pos + 2, "clause"

        # Priority 6: Hard cut at character boundary
        return max_pos, "hard"

    def _rfind_any(self, text: str, patterns: tuple[str, ...]) -> int:
        """Find the rightmost occurrence of any pattern in text.

        Returns:
            The highest position found, or -1 if none found.
        """
        best = -1
        for pattern in patterns:
            pos = text.rfind(pattern)
            if pos > best:
                best = pos
        return best

    def _byte_limit_to_char_pos(self, text: str, max_bytes: int) -> int:
        """Find the character position that fits within max_bytes.

        Uses binary search for efficiency with mixed-width characters.
        """
        if len(text.encode("utf-8")) <= max_bytes:
            return len(text)

        # Binary search for the right character position
        low, high = 0, len(text)
        while low < high:
            mid = (low + high + 1) // 2
            if len(text[:mid].encode("utf-8")) <= max_bytes:
                low = mid
            else:
                high = mid - 1
        return low

    @staticmethod
    def _make_segment(text: str, index: int, boundary_type: str) -> TextSegment:
        """Create a TextSegment with computed lengths."""
        return TextSegment(
            text=text,
            index=index,
            byte_length=len(text.encode("utf-8")),
            char_length=len(text),
            boundary_type=boundary_type,
        )
