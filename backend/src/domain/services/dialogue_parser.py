"""Dialogue Parser Service.

Parses multi-role dialogue text into structured DialogueTurn objects.
"""

import re

from src.domain.entities.multi_role_tts import DialogueTurn

# Maximum number of unique speakers allowed
MAX_SPEAKERS = 6

# Regex pattern to match dialogue turns:
# - [SpeakerName]: text  (bracket format)
# - A: text  (letter format, uppercase only)
# Supports both English colon (:) and Chinese full-width colon (：)
DIALOGUE_PATTERN = re.compile(
    r"(?:\[([^\]]+)\]|([A-Z]))\s*[:：]\s*(.+?)(?=(?:\[[^\]]+\]|[A-Z])\s*[:：]|$)",
    re.DOTALL,
)


def parse_dialogue(text: str) -> tuple[list[DialogueTurn], list[str]]:
    """Parse dialogue text into structured turns.

    Supports two speaker formats:
    - Letter format: A: text, B: text
    - Bracket format: [Host]: text, [Guest]: text

    Both English (:) and Chinese (：) colons are supported.

    Args:
        text: The dialogue text to parse.

    Returns:
        A tuple of (turns, speakers) where:
        - turns: List of DialogueTurn objects in order
        - speakers: Unique list of speakers in order of first appearance

    Raises:
        ValueError: If text is empty, has invalid format, speaker name > 50 chars,
                   or more than 6 speakers.
    """
    # Validate non-empty input
    if not text or not text.strip():
        raise ValueError("Dialogue text cannot be empty")

    # Find all matches
    matches = DIALOGUE_PATTERN.findall(text)

    if not matches:
        raise ValueError("Invalid dialogue format. Use 'A: text' or '[Speaker]: text'")

    turns: list[DialogueTurn] = []
    speakers_seen: list[str] = []

    for index, match in enumerate(matches):
        # match is (bracket_name, letter_name, text)
        bracket_name, letter_name, turn_text = match
        speaker = bracket_name if bracket_name else letter_name
        turn_text = turn_text.strip()

        # Validate speaker name length
        if len(speaker) > 50:
            raise ValueError(
                f"Speaker name '{speaker[:20]}...' exceeds maximum length of 50 characters"
            )

        # Track unique speakers in order of first appearance
        if speaker not in speakers_seen:
            speakers_seen.append(speaker)

        # Check speaker limit
        if len(speakers_seen) > MAX_SPEAKERS:
            raise ValueError(
                f"Too many speakers. Maximum allowed is {MAX_SPEAKERS}, found {len(speakers_seen)}"
            )

        # Create DialogueTurn
        turns.append(
            DialogueTurn(
                speaker=speaker,
                text=turn_text,
                index=index,
            )
        )

    return turns, speakers_seen
