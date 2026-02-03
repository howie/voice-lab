"""Voice Metadata Inferrer Service.

Feature: 008-voai-multi-role-voice-generation
T024: Implement age_group inference logic per provider

Infers age_group and other metadata from provider-specific voice information.
"""

import logging
import re

from src.domain.entities.voice import AgeGroup

logger = logging.getLogger(__name__)

# Azure voice name patterns that suggest age groups
AZURE_CHILD_PATTERNS = [
    r"child",
    r"kid",
    r"boy",
    r"girl",
    r"童",
    r"小",
]

AZURE_YOUNG_PATTERNS = [
    r"young",
    r"youth",
    r"teen",
    r"青年",
    r"少",
]

AZURE_SENIOR_PATTERNS = [
    r"senior",
    r"elder",
    r"old",
    r"長者",
    r"老",
]

# Azure style patterns that suggest age groups
AZURE_STYLE_AGE_HINTS = {
    "childlike": AgeGroup.CHILD,
    "newscast": AgeGroup.ADULT,
    "customerservice": AgeGroup.ADULT,
    "assistant": AgeGroup.ADULT,
    "narration": AgeGroup.ADULT,
}


class VoiceMetadataInferrer:
    """Infers voice metadata from provider-specific information.

    This service analyzes provider-specific voice data to infer standardized
    metadata fields like age_group.
    """

    def infer_age_group_from_azure(
        self,
        display_name: str,
        local_name: str,
        style_list: list[str] | None = None,
        role_play_list: list[str] | None = None,
    ) -> AgeGroup | None:
        """Infer age group from Azure voice metadata.

        Azure provides:
        - DisplayName: e.g., "HsiaoChen"
        - LocalName: e.g., "曉臻"
        - StyleList: e.g., ["chat", "cheerful"]
        - RolePlayList: e.g., ["Girl", "Boy"]

        Args:
            display_name: Azure voice display name.
            local_name: Azure voice local name.
            style_list: List of supported styles.
            role_play_list: List of role-play capabilities.

        Returns:
            Inferred AgeGroup or None if cannot be determined.
        """
        style_list = style_list or []
        role_play_list = role_play_list or []

        # Check role play list first (most reliable)
        role_play_lower = " ".join(role_play_list).lower()
        if any(pattern in role_play_lower for pattern in ["girl", "boy", "child"]):
            return AgeGroup.CHILD

        # Check display name and local name
        combined_name = f"{display_name} {local_name}".lower()

        for pattern in AZURE_CHILD_PATTERNS:
            if re.search(pattern, combined_name, re.IGNORECASE):
                return AgeGroup.CHILD

        for pattern in AZURE_YOUNG_PATTERNS:
            if re.search(pattern, combined_name, re.IGNORECASE):
                return AgeGroup.YOUNG

        for pattern in AZURE_SENIOR_PATTERNS:
            if re.search(pattern, combined_name, re.IGNORECASE):
                return AgeGroup.SENIOR

        # Check styles for hints
        style_lower = " ".join(style_list).lower()
        for style, age in AZURE_STYLE_AGE_HINTS.items():
            if style in style_lower:
                return age

        # Default to adult for professional-sounding voices
        if any(
            s in style_lower for s in ["news", "narration", "customer", "assistant", "professional"]
        ):
            return AgeGroup.ADULT

        # If no clear indicators, default to adult (most common)
        return AgeGroup.ADULT

    def infer_age_group_from_elevenlabs(
        self,
        name: str,
        age_label: str | None = None,
        description: str | None = None,
    ) -> AgeGroup | None:
        """Infer age group from ElevenLabs voice metadata.

        ElevenLabs provides:
        - name: Voice name
        - labels.age: e.g., "young", "middle aged", "old"
        - description: Voice description

        Args:
            name: Voice name.
            age_label: Age label from ElevenLabs API.
            description: Voice description.

        Returns:
            Inferred AgeGroup or None if cannot be determined.
        """
        # ElevenLabs provides explicit age labels
        if age_label:
            age_lower = age_label.lower()

            if age_lower in ["young", "youth", "youthful"]:
                return AgeGroup.YOUNG
            elif age_lower in ["middle aged", "middle-aged", "adult"]:
                return AgeGroup.ADULT
            elif age_lower in ["old", "elderly", "senior", "aged"]:
                return AgeGroup.SENIOR
            elif age_lower in ["child", "children", "kid"]:
                return AgeGroup.CHILD

        # Fall back to description analysis
        if description:
            desc_lower = description.lower()

            if any(word in desc_lower for word in ["child", "kid", "boy", "girl"]):
                return AgeGroup.CHILD
            if any(word in desc_lower for word in ["young", "youth", "teen"]):
                return AgeGroup.YOUNG
            if any(word in desc_lower for word in ["senior", "elder", "old", "aged"]):
                return AgeGroup.SENIOR

        # Check name for hints
        name_lower = name.lower()
        if any(word in name_lower for word in ["child", "kid", "junior"]):
            return AgeGroup.CHILD
        if any(word in name_lower for word in ["young", "youth"]):
            return AgeGroup.YOUNG

        # Default to adult
        return AgeGroup.ADULT

    def infer_storybook_suitability(
        self,
        style_list: list[str] | None = None,
        role_play_list: list[str] | None = None,
        locale: str = "",
    ) -> bool:
        """Determine whether a voice is suitable for children's storybook narration.

        A voice is considered suitable if it:
        - Has gentle / cheerful / story / calm / affectionate styles, OR
        - Can role-play Girl / Boy characters, OR
        - Is a zh-TW locale voice (native Taiwan Mandarin).

        Args:
            style_list: Supported voice styles.
            role_play_list: Supported role-play characters.
            locale: Voice locale (e.g., "zh-TW").

        Returns:
            True if the voice is storybook-suitable.
        """
        storybook_styles = {
            "gentle",
            "cheerful",
            "story",
            "calm",
            "affectionate",
            "narration-relaxed",
            "friendly",
        }
        storybook_roles = {"Girl", "Boy"}

        if style_list and set(style_list) & storybook_styles:
            return True
        if role_play_list and set(role_play_list) & storybook_roles:
            return True
        return locale == "zh-TW"

    def infer_gender_from_azure(self, gender: str) -> str | None:
        """Normalize Azure gender to standard format.

        Args:
            gender: Azure gender string (e.g., "Female", "Male").

        Returns:
            Normalized gender string or None.
        """
        if not gender:
            return None

        gender_lower = gender.lower()
        if gender_lower == "female":
            return "female"
        elif gender_lower == "male":
            return "male"
        else:
            return "neutral"

    def infer_gender_from_elevenlabs(self, gender_label: str | None) -> str | None:
        """Normalize ElevenLabs gender to standard format.

        Args:
            gender_label: Gender label from ElevenLabs API.

        Returns:
            Normalized gender string or None.
        """
        if not gender_label:
            return None

        gender_lower = gender_label.lower()
        if gender_lower in ["female", "woman"]:
            return "female"
        elif gender_lower in ["male", "man"]:
            return "male"
        else:
            return "neutral"
