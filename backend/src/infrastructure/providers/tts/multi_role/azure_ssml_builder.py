"""Azure SSML Builder for Multi-Role TTS.

Feature: 008-voai-multi-role-voice-generation
T011: Implement AzureSSMLBuilder.build_multi_voice_ssml()

Builds SSML with multiple <voice> tags for native multi-role synthesis.
"""

from dataclasses import dataclass

from src.domain.entities.multi_role_tts import DialogueTurn


@dataclass
class AzureSSMLConfig:
    """Configuration for Azure SSML generation."""

    language: str = "zh-TW"
    gap_ms: int = 300
    default_rate: str = "0%"
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
            escaped_text = self._escape_xml(turn.text)

            ssml_parts.append(f'    <voice name="{voice_name}">')
            ssml_parts.append(
                f'        <prosody rate="{self.config.default_rate}" '
                f'pitch="{self.config.default_pitch}">{escaped_text}</prosody>'
            )
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

        # Text content
        text_chars = sum(len(t.text) for t in turns)

        # Voice name length (average)
        avg_voice_name_len = sum(len(v) for v in voice_map.values()) / max(len(voice_map), 1)

        return int(
            base_overhead + (per_turn_overhead + avg_voice_name_len) * len(turns) + text_chars
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
