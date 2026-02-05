"""Gemini Dialogue Builder for Multi-Role TTS.

Builds request payloads for Gemini's native multi-speaker TTS API
using multiSpeakerVoiceConfig.

Gemini Multi-Speaker API Limits:
    - Max input: 4000 bytes (UTF-8)
    - CJK characters: 3 bytes each (~1333 chars max)
    - Max speakers: 6

When input exceeds the byte limit, the caller should fall back to
segmented synthesis mode.
"""

from dataclasses import dataclass
from typing import Any

from src.domain.entities.multi_role_tts import DialogueTurn


@dataclass
class GeminiDialogueConfig:
    """Configuration for Gemini multi-speaker dialogue."""

    model: str = "gemini-2.5-pro-preview-tts"


class GeminiDialogueBuilder:
    """Builder for Gemini multi-speaker TTS API requests.

    Constructs payloads using Gemini's multiSpeakerVoiceConfig format,
    which allows native multi-speaker synthesis in a single API call.

    The dialogue text uses "Speaker: text" format, and each speaker
    maps to a prebuilt voice via speakerVoiceConfigs.
    """

    MAX_INPUT_BYTES = 4000

    def __init__(self, config: GeminiDialogueConfig | None = None):
        self.config = config or GeminiDialogueConfig()

    def build_multi_speaker_payload(
        self,
        turns: list[DialogueTurn],
        voice_map: dict[str, str],
        style_prompt: str | None = None,
        speaker_style_map: dict[str, str] | None = None,  # noqa: ARG002
    ) -> dict[str, Any]:
        """Build Gemini multiSpeakerVoiceConfig API payload.

        Args:
            turns: Dialogue turns in order.
            voice_map: Speaker name -> Gemini voice name mapping.
            style_prompt: Optional global style prompt prepended to dialogue text.
            speaker_style_map: Reserved for future per-speaker style support.

        Returns:
            API payload dict ready for JSON serialization.

        Raises:
            ValueError: If turns are empty, voice mapping is incomplete,
                or input exceeds the byte limit.
        """
        if not turns:
            raise ValueError("Turns cannot be empty")

        missing_speakers = {t.speaker for t in turns} - set(voice_map.keys())
        if missing_speakers:
            raise ValueError(f"Missing voice mapping for speakers: {missing_speakers}")

        dialogue_text = self._format_dialogue_text(turns, style_prompt)

        byte_length = len(dialogue_text.encode("utf-8"))
        if byte_length > self.MAX_INPUT_BYTES:
            raise ValueError(
                f"Dialogue text exceeds {self.MAX_INPUT_BYTES}-byte limit: "
                f"{byte_length} bytes. Use segmented mode instead."
            )

        # Build speakerVoiceConfigs from unique speakers in turn order
        seen_speakers: list[str] = []
        for turn in sorted(turns, key=lambda t: t.index):
            if turn.speaker not in seen_speakers:
                seen_speakers.append(turn.speaker)

        speaker_configs = []
        for speaker in seen_speakers:
            voice_name = voice_map[speaker]
            if voice_name.startswith("gemini:"):
                voice_name = voice_name[7:]
            speaker_configs.append(
                {
                    "speaker": speaker,
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {"voiceName": voice_name},
                    },
                }
            )

        return {
            "contents": [{"parts": [{"text": dialogue_text}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "multiSpeakerVoiceConfig": {
                        "speakerVoiceConfigs": speaker_configs,
                    },
                },
            },
        }

    def can_use_native(
        self,
        turns: list[DialogueTurn],
        voice_map: dict[str, str],  # noqa: ARG002
        style_prompt: str | None = None,
    ) -> bool:
        """Check if native multi-speaker mode can handle the dialogue.

        Validates total byte length against Gemini's 4000-byte limit.

        Args:
            turns: Dialogue turns.
            voice_map: Speaker to voice mapping (kept for interface consistency).
            style_prompt: Optional global style prompt.

        Returns:
            True if the dialogue fits within the byte limit.
        """
        dialogue_text = self._format_dialogue_text(turns, style_prompt)
        return len(dialogue_text.encode("utf-8")) <= self.MAX_INPUT_BYTES

    def estimate_bytes(self, turns: list[DialogueTurn], style_prompt: str | None = None) -> int:
        """Estimate total byte count of the dialogue text.

        Args:
            turns: Dialogue turns.
            style_prompt: Optional global style prompt.

        Returns:
            UTF-8 byte count of the formatted dialogue text.
        """
        dialogue_text = self._format_dialogue_text(turns, style_prompt)
        return len(dialogue_text.encode("utf-8"))

    def _format_dialogue_text(
        self,
        turns: list[DialogueTurn],
        style_prompt: str | None = None,
    ) -> str:
        """Format dialogue turns into Gemini multi-speaker text format.

        Produces "Speaker: text" lines joined by newlines.
        Optionally prepends a global style prompt as a leading instruction.

        Args:
            turns: Dialogue turns in order.
            style_prompt: Optional style instruction prepended to dialogue.

        Returns:
            Formatted dialogue text string.
        """
        sorted_turns = sorted(turns, key=lambda t: t.index)
        lines = [f"{turn.speaker}: {turn.text}" for turn in sorted_turns]
        dialogue = "\n".join(lines)

        if style_prompt:
            return f"{style_prompt}\n{dialogue}"
        return dialogue
