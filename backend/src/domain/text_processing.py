"""Text processing utilities for TTS.

T069: Handle special characters and emojis in input text
"""

import re
import unicodedata

# Emoji pattern (covers most common emoji ranges)
EMOJI_PATTERN = re.compile(
    "["
    "\U0001f600-\U0001f64f"  # emoticons
    "\U0001f300-\U0001f5ff"  # symbols & pictographs
    "\U0001f680-\U0001f6ff"  # transport & map symbols
    "\U0001f1e0-\U0001f1ff"  # flags
    "\U00002702-\U000027b0"  # dingbats
    "\U000024c2-\U0001f251"  # enclosed characters
    "\U0001f900-\U0001f9ff"  # supplemental symbols
    "\U0001fa00-\U0001fa6f"  # chess symbols
    "\U0001fa70-\U0001faff"  # symbols and pictographs extended-A
    "\U00002600-\U000026ff"  # misc symbols
    "\U00002700-\U000027bf"  # dingbats
    "]+",
    flags=re.UNICODE,
)

# SSML special characters that need escaping
SSML_ESCAPE_MAP = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&apos;",
}

# Characters that might cause issues in TTS
PROBLEMATIC_CHARS = re.compile(
    r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]"  # Control characters
)


class TextProcessor:
    """Processor for cleaning and normalizing TTS input text."""

    def __init__(
        self,
        remove_emojis: bool = False,
        normalize_whitespace: bool = True,
        escape_ssml: bool = True,
        max_consecutive_punctuation: int = 3,
    ) -> None:
        """Initialize text processor.

        Args:
            remove_emojis: Whether to remove emojis from text
            normalize_whitespace: Whether to normalize whitespace
            escape_ssml: Whether to escape SSML special characters
            max_consecutive_punctuation: Max consecutive punctuation marks
        """
        self.remove_emojis = remove_emojis
        self.normalize_whitespace = normalize_whitespace
        self.escape_ssml = escape_ssml
        self.max_consecutive_punctuation = max_consecutive_punctuation

    def process(self, text: str) -> str:
        """Process text for TTS synthesis.

        Args:
            text: Input text to process

        Returns:
            Cleaned and normalized text
        """
        if not text:
            return text

        result = text

        # Remove control characters
        result = PROBLEMATIC_CHARS.sub("", result)

        # Handle emojis
        if self.remove_emojis:
            result = self._remove_emojis(result)
        else:
            result = self._convert_emojis_to_text(result)

        # Normalize unicode
        result = unicodedata.normalize("NFC", result)

        # Escape SSML characters if needed
        if self.escape_ssml:
            result = self._escape_ssml(result)

        # Normalize whitespace
        if self.normalize_whitespace:
            result = self._normalize_whitespace(result)

        # Limit consecutive punctuation
        result = self._limit_punctuation(result)

        return result.strip()

    def _remove_emojis(self, text: str) -> str:
        """Remove all emojis from text."""
        return EMOJI_PATTERN.sub("", text)

    def _convert_emojis_to_text(self, text: str) -> str:
        """Convert emojis to their text descriptions.

        This provides better TTS output than just removing emojis.
        """
        # Common emoji to text mappings
        emoji_to_text = {
            "😀": " smile ",
            "😃": " smile ",
            "😄": " smile ",
            "😁": " grin ",
            "😅": " nervous laugh ",
            "😂": " laugh ",
            "🤣": " laugh ",
            "😊": " smile ",
            "😇": " innocent ",
            "🥰": " love ",
            "😍": " heart eyes ",
            "😘": " kiss ",
            "😗": " kiss ",
            "😚": " kiss ",
            "😋": " yummy ",
            "😛": " tongue out ",
            "😜": " wink ",
            "🤪": " crazy ",
            "😎": " cool ",
            "🤩": " star eyes ",
            "🥳": " party ",
            "😏": " smirk ",
            "😒": " unamused ",
            "😞": " sad ",
            "😔": " sad ",
            "😟": " worried ",
            "😕": " confused ",
            "🙁": " sad ",
            "😣": " frustrated ",
            "😖": " frustrated ",
            "😫": " tired ",
            "😩": " tired ",
            "🥺": " pleading ",
            "😢": " cry ",
            "😭": " cry ",
            "😤": " angry ",
            "😠": " angry ",
            "😡": " angry ",
            "🤬": " angry ",
            "😱": " scared ",
            "😨": " scared ",
            "😰": " anxious ",
            "😥": " sad ",
            "😓": " sweat ",
            "🤗": " hug ",
            "🤔": " thinking ",
            "🤭": " oops ",
            "🤫": " shush ",
            "🤥": " lie ",
            "😶": " silence ",
            "😐": " neutral ",
            "😑": " expressionless ",
            "😬": " grimace ",
            "🙄": " eye roll ",
            "😯": " surprised ",
            "😦": " frown ",
            "😧": " anguish ",
            "😮": " surprised ",
            "😲": " astonished ",
            "🥱": " yawn ",
            "😴": " sleep ",
            "🤤": " drool ",
            "😪": " sleepy ",
            "😵": " dizzy ",
            "🤐": " zipper mouth ",
            "🥴": " woozy ",
            "🤢": " nauseated ",
            "🤮": " vomit ",
            "🤧": " sneeze ",
            "😷": " mask ",
            "🤒": " sick ",
            "🤕": " injured ",
            "👍": " thumbs up ",
            "👎": " thumbs down ",
            "👏": " clap ",
            "🙌": " hands up ",
            "👋": " wave ",
            "✌️": " peace ",
            "🤞": " fingers crossed ",
            "🤟": " love you ",
            "🤘": " rock on ",
            "👌": " okay ",
            "🤙": " call me ",
            "💪": " strong ",
            "🙏": " pray ",
            "❤️": " heart ",
            "💕": " hearts ",
            "💖": " sparkle heart ",
            "💗": " growing heart ",
            "💓": " beating heart ",
            "💞": " revolving hearts ",
            "💘": " cupid ",
            "💝": " heart with ribbon ",
            "💔": " broken heart ",
            "🔥": " fire ",
            "⭐": " star ",
            "🌟": " glowing star ",
            "✨": " sparkles ",
            "💫": " dizzy ",
            "🎉": " party ",
            "🎊": " confetti ",
            "🎁": " gift ",
            "🎈": " balloon ",
            "🎂": " birthday cake ",
            "🍰": " cake ",
            "☀️": " sun ",
            "🌈": " rainbow ",
            "🌸": " cherry blossom ",
            "🌺": " flower ",
            "🌻": " sunflower ",
            "🌷": " tulip ",
            "🌹": " rose ",
            "💐": " bouquet ",
            "🍀": " four leaf clover ",
            "🌲": " tree ",
            "🌴": " palm tree ",
            "🌊": " wave ",
            "🌙": " moon ",
            "⚡": " lightning ",
            "☁️": " cloud ",
            "❄️": " snowflake ",
            "🌨️": " snow ",
            "☔": " rain ",
            "🚀": " rocket ",
            "✈️": " airplane ",
            "🚗": " car ",
            "🚌": " bus ",
            "🚂": " train ",
            "🚢": " ship ",
            "🏠": " house ",
            "🏢": " building ",
            "🏥": " hospital ",
            "🏫": " school ",
            "⏰": " alarm clock ",
            "📱": " phone ",
            "💻": " laptop ",
            "📧": " email ",
            "📝": " memo ",
            "📚": " books ",
            "🎵": " music note ",
            "🎶": " music notes ",
            "🎤": " microphone ",
            "🎸": " guitar ",
            "🎹": " piano ",
            "🎬": " movie ",
            "📷": " camera ",
            "💡": " light bulb ",
            "🔔": " bell ",
            "✅": " check mark ",
            "❌": " cross mark ",
            "⚠️": " warning ",
            "❓": " question ",
            "❗": " exclamation ",
            "💯": " hundred points ",
        }

        result = text
        for emoji, replacement in emoji_to_text.items():
            result = result.replace(emoji, replacement)

        # Remove any remaining emojis that weren't mapped
        result = EMOJI_PATTERN.sub(" ", result)

        return result

    def _escape_ssml(self, text: str) -> str:
        """Escape SSML special characters."""
        for char, escaped in SSML_ESCAPE_MAP.items():
            text = text.replace(char, escaped)
        return text

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text."""
        # Replace various whitespace with regular space
        text = re.sub(r"[\t\r\n]+", " ", text)
        # Collapse multiple spaces
        text = re.sub(r" +", " ", text)
        return text

    def _limit_punctuation(self, text: str) -> str:
        """Limit consecutive punctuation marks."""
        # Match repeated punctuation
        pattern = r"([!?.,;:…]+)"

        def replace_func(match):
            punct = match.group(1)
            if len(punct) > self.max_consecutive_punctuation:
                # Keep only first few characters
                return punct[: self.max_consecutive_punctuation]
            return punct

        return re.sub(pattern, replace_func, text)


# Default processor instance
default_processor = TextProcessor()


def process_text(
    text: str,
    remove_emojis: bool = False,
    escape_ssml: bool = True,
) -> str:
    """Process text for TTS synthesis.

    Convenience function using default processor settings.

    Args:
        text: Input text to process
        remove_emojis: Whether to remove emojis (default: convert to text)
        escape_ssml: Whether to escape SSML characters

    Returns:
        Processed text ready for TTS synthesis
    """
    processor = TextProcessor(
        remove_emojis=remove_emojis,
        escape_ssml=escape_ssml,
    )
    return processor.process(text)


def contains_emojis(text: str) -> bool:
    """Check if text contains emojis."""
    return bool(EMOJI_PATTERN.search(text))


def extract_emojis(text: str) -> list[str]:
    """Extract all emojis from text."""
    return EMOJI_PATTERN.findall(text)


def count_characters(text: str, count_emojis_as: int = 1) -> int:
    """Count characters in text.

    Args:
        text: Input text
        count_emojis_as: How many characters each emoji counts as

    Returns:
        Character count
    """
    emojis = extract_emojis(text)
    text_without_emojis = EMOJI_PATTERN.sub("", text)

    return len(text_without_emojis) + (len(emojis) * count_emojis_as)


def validate_text_for_tts(text: str, max_length: int = 5000) -> tuple[bool, str | None]:
    """Validate text for TTS synthesis.

    Args:
        text: Text to validate
        max_length: Maximum allowed length

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text:
        return False, "Text cannot be empty"

    if not text.strip():
        return False, "Text cannot be only whitespace"

    if len(text) > max_length:
        return False, f"Text exceeds maximum length of {max_length} characters"

    # Check for problematic patterns
    if PROBLEMATIC_CHARS.search(text):
        return False, "Text contains invalid control characters"

    return True, None
