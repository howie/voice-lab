"""Azure SSML Builder for Multi-Role TTS.

Feature: 008-voai-multi-role-voice-generation
T011: Implement AzureSSMLBuilder.build_multi_voice_ssml()

Builds SSML with multiple <voice> tags for native multi-role synthesis.
Supports [style] tags for Azure express-as styles.
"""

import re
from dataclasses import dataclass

from src.domain.entities.multi_role_tts import DialogueTurn

KNOWN_STYLES: frozenset[str] = frozenset(
    {
        "advertisement_upbeat",
        "affectionate",
        "angry",
        "assistant",
        "calm",
        "chat",
        "cheerful",
        "customerservice",
        "depressed",
        "disgruntled",
        "documentary-narration",
        "embarrassed",
        "empathetic",
        "envious",
        "excited",
        "fearful",
        "friendly",
        "gentle",
        "hopeful",
        "lyrical",
        "narration-professional",
        "narration-relaxed",
        "newscast",
        "newscast-casual",
        "newscast-formal",
        "poetry-reading",
        "sad",
        "serious",
        "shouting",
        "sports_commentary",
        "sports_commentary_excited",
        "story",
        "terrified",
        "unfriendly",
        "whispering",
    }
)

_STYLE_TAG_RE = re.compile(r"\[([a-zA-Z][a-zA-Z0-9_-]*)\]")


@dataclass
class AzureSSMLConfig:
    """Configuration for Azure SSML generation."""

    language: str = "zh-TW"
    gap_ms: int = 300
    default_rate: str = "+0%"
    default_pitch: str = "+0Hz"


class AzureSSMLBuilder:
    """Builder for Azure multi-voice SSML.

    Constructs SSML documents with multiple <voice> elements for native
    multi-role dialogue synthesis.

    Azure SSML Limits:
        - WebSocket (real-time): 64 KB max SSML message size
        - Max voice/audio tags: 50 per request
        - Conservative character limit: 50,000 Unicode characters

    Example SSML output:
        <speak version="1.0"
               xmlns="http://www.w3.org/2001/10/synthesis"
               xmlns:mstts="https://www.w3.org/2001/mstts"
               xml:lang="zh-TW">
            <voice name="zh-TW-HsiaoYuNeural">
                <prosody rate="0%" pitch="+0Hz">你好，我是 A</prosody>
            </voice>
            <break time="300ms"/>
            <voice name="zh-TW-YunJheNeural">
                <prosody rate="0%" pitch="+0Hz">嗨，我是 B</prosody>
            </voice>
        </speak>
    """

    # Azure WebSocket limit is 64KB, use conservative 50,000 chars
    MAX_CHARS = 50000
    MAX_VOICE_TAGS = 50

    def __init__(self, config: AzureSSMLConfig | None = None):
        """Initialize the builder.

        Args:
            config: Optional configuration for SSML generation.
        """
        self.config = config or AzureSSMLConfig()

    def build_multi_voice_ssml(
        self,
        turns: list[DialogueTurn],
        voice_map: dict[str, str],
        language: str | None = None,
        gap_ms: int | None = None,
    ) -> str:
        """Build multi-voice SSML from dialogue turns.

        Args:
            turns: List of dialogue turns in order.
            voice_map: Mapping from speaker ID to Azure voice name.
            language: Optional language override (e.g., "zh-TW").
            gap_ms: Optional gap between turns in milliseconds.

        Returns:
            Complete SSML document as string.

        Raises:
            ValueError: If turns exceed limits or voice mapping is incomplete.
        """
        if not turns:
            raise ValueError("Turns cannot be empty")

        # Check turn count limit
        if len(turns) > self.MAX_VOICE_TAGS:
            raise ValueError(
                f"Too many turns ({len(turns)}). "
                f"Azure supports max {self.MAX_VOICE_TAGS} voice tags per request."
            )

        # Validate voice mappings
        missing_speakers = {t.speaker for t in turns} - set(voice_map.keys())
        if missing_speakers:
            raise ValueError(f"Missing voice mapping for speakers: {missing_speakers}")

        lang = language or self.config.language
        gap = gap_ms if gap_ms is not None else self.config.gap_ms

        # Build SSML
        ssml_parts = [
            '<speak version="1.0"',
            '       xmlns="http://www.w3.org/2001/10/synthesis"',
            '       xmlns:mstts="https://www.w3.org/2001/mstts"',
            f'       xml:lang="{lang}">',
        ]

        # Sort turns by index
        sorted_turns = sorted(turns, key=lambda t: t.index)

        for i, turn in enumerate(sorted_turns):
            voice_name = voice_map[turn.speaker]

            ssml_parts.append(f'    <voice name="{voice_name}">')
            ssml_parts.extend(self._build_turn_ssml(turn.text))
            ssml_parts.append("    </voice>")

            # Add break between turns (except after last turn)
            if i < len(sorted_turns) - 1 and gap > 0:
                ssml_parts.append(f'    <break time="{gap}ms"/>')

        ssml_parts.append("</speak>")

        ssml = "\n".join(ssml_parts)

        # Validate total size
        if len(ssml) > self.MAX_CHARS:
            raise ValueError(
                f"SSML exceeds character limit ({len(ssml)} > {self.MAX_CHARS}). "
                "Consider using segmented mode."
            )

        return ssml

    def estimate_ssml_size(
        self,
        turns: list[DialogueTurn],
        voice_map: dict[str, str],
    ) -> int:
        """Estimate the SSML size without building it.

        Useful for checking if native mode is feasible before attempting.

        Args:
            turns: List of dialogue turns.
            voice_map: Mapping from speaker ID to Azure voice name.

        Returns:
            Estimated character count of the SSML.
        """
        # Base SSML overhead (speak tag, xmlns, etc.)
        base_overhead = 250

        # Per-turn overhead (voice tag, prosody, break)
        per_turn_overhead = 150

        # Text content + style tag overhead
        text_chars = 0
        style_overhead = 0
        for t in turns:
            text_chars += len(t.text)
            style_overhead += len(_STYLE_TAG_RE.findall(t.text)) * 80

        # Voice name length (average)
        avg_voice_name_len = sum(len(v) for v in voice_map.values()) / max(len(voice_map), 1)

        return int(
            base_overhead
            + (per_turn_overhead + avg_voice_name_len) * len(turns)
            + text_chars
            + style_overhead
        )

    def can_use_native(
        self,
        turns: list[DialogueTurn],
        voice_map: dict[str, str],
    ) -> bool:
        """Check if native mode can be used for the given turns.

        Args:
            turns: List of dialogue turns.
            voice_map: Mapping from speaker ID to Azure voice name.

        Returns:
            True if native mode is feasible, False otherwise.
        """
        if len(turns) > self.MAX_VOICE_TAGS:
            return False

        estimated_size = self.estimate_ssml_size(turns, voice_map)
        return estimated_size <= self.MAX_CHARS

    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters.

        Args:
            text: Text to escape.

        Returns:
            XML-safe text.
        """
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )

    def _parse_style_segments(self, text: str) -> list[tuple[str | None, str]]:
        """Parse style tags from text into segments.

        Splits text by [tag] markers. Known styles become style segments;
        unknown tags are kept as literal text.

        Args:
            text: Raw dialogue text possibly containing [style] tags.

        Returns:
            List of (style_or_none, text) tuples.
        """
        parts = _STYLE_TAG_RE.split(text)
        segments: list[tuple[str | None, str]] = []
        current_style: str | None = None

        for part in parts:
            lower = part.lower()
            if lower in KNOWN_STYLES:
                current_style = lower
                continue

            # If it matches the tag pattern but is unknown, restore brackets
            if _STYLE_TAG_RE.fullmatch(f"[{part}]") and lower not in KNOWN_STYLES:
                # This part came from a split — it was between brackets
                # but is not a known style, so treat as plain text
                chunk = f"[{part}]"
                if segments and segments[-1][0] == current_style:
                    segments[-1] = (current_style, segments[-1][1] + chunk)
                else:
                    segments.append((current_style, chunk))
                current_style = None
                continue

            stripped = part.strip()
            if not stripped:
                continue

            segments.append((current_style, stripped))

        return segments

    def _build_turn_ssml(
        self,
        text: str,
        rate: str | None = None,
        pitch: str | None = None,
    ) -> list[str]:
        """Build SSML fragments for a single turn, handling style segments.

        Args:
            text: Raw dialogue text possibly containing [style] tags.
            rate: Prosody rate override.
            pitch: Prosody pitch override.

        Returns:
            List of SSML lines for this turn.
        """
        r = rate or self.config.default_rate
        p = pitch or self.config.default_pitch

        segments = self._parse_style_segments(text)

        # No style tags found — backward compatible plain prosody
        if not segments:
            escaped = self._escape_xml(text.strip())
            return [
                f'        <prosody rate="{r}" pitch="{p}">{escaped}</prosody>',
            ]

        # Check if all segments have no style — backward compatible
        if all(s is None for s, _ in segments):
            combined = self._escape_xml(" ".join(t for _, t in segments))
            return [
                f'        <prosody rate="{r}" pitch="{p}">{combined}</prosody>',
            ]

        lines: list[str] = []
        for style, segment_text in segments:
            escaped = self._escape_xml(segment_text)
            if style:
                lines.append(f'        <mstts:express-as style="{style}">')
                lines.append(f'            <prosody rate="{r}" pitch="{p}">{escaped}</prosody>')
                lines.append("        </mstts:express-as>")
            else:
                lines.append(f'        <prosody rate="{r}" pitch="{p}">{escaped}</prosody>')
        return lines
