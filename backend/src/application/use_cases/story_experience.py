"""Story Experience MVP use case.

Feature: 016-story-experience-mvp
Coordinates LLM content generation and TTS synthesis
for the parent story experience interface.
"""

from __future__ import annotations

import base64
import json
import logging
import re
from uuid import uuid4

from src.application.interfaces.llm_provider import ILLMProvider, LLMMessage
from src.application.interfaces.tts_provider import ITTSProvider
from src.domain.entities.tts import TTSRequest
from src.domain.services.story.mvp_prompts import (
    MVP_SONG_GENERATE_PROMPT,
    MVP_STORY_BRANCH_CONTINUE_PROMPT,
    MVP_STORY_BRANCH_PROMPT,
    MVP_STORY_GENERATE_PROMPT,
    MVP_STORY_QA_ANSWER_PROMPT,
    MVP_STORY_QA_GENERATE_PROMPT,
    MVP_STORY_SYSTEM_PROMPT,
    get_length_guidance,
    get_length_range,
)

logger = logging.getLogger(__name__)


class StoryExperienceUseCase:
    """Use case for parent story experience MVP.

    Orchestrates LLM for content generation and TTS for audio synthesis.
    """

    def __init__(
        self,
        llm_provider: ILLMProvider,
        tts_provider: ITTSProvider,
    ) -> None:
        self._llm = llm_provider
        self._tts = tts_provider

    # =========================================================================
    # Content Generation
    # =========================================================================

    async def generate_content(
        self,
        *,
        age: int,
        educational_content: str,
        values: list[str],
        emotions: list[str],
        favorite_character: str,
        content_type: str,
    ) -> dict:
        """Generate story or song content from parent input parameters.

        Returns:
            Dict with content_id, content_type, text_content, parameters_summary.
        """
        length_guidance = get_length_guidance(age)
        min_chars, max_chars = get_length_range(age)

        # Select prompt template based on content type
        if content_type == "song":
            prompt_template = MVP_SONG_GENERATE_PROMPT
        else:
            prompt_template = MVP_STORY_GENERATE_PROMPT

        user_prompt = prompt_template.format(
            age=age,
            educational_content=educational_content,
            values="、".join(values),
            emotions="、".join(emotions),
            favorite_character=favorite_character,
            length_guidance=length_guidance,
            min_chars=min_chars,
            max_chars=max_chars,
        )

        messages = [
            LLMMessage(role="system", content=MVP_STORY_SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_prompt),
        ]

        response = await self._llm.generate(
            messages=messages,
            max_tokens=2000,
            temperature=0.8,
        )

        content_id = str(uuid4())
        return {
            "content_id": content_id,
            "content_type": content_type,
            "text_content": response.content.strip(),
            "parameters_summary": {
                "age": age,
                "educational_content": educational_content,
                "values": values,
                "emotions": emotions,
                "favorite_character": favorite_character,
            },
        }

    # =========================================================================
    # Story Branching
    # =========================================================================

    async def generate_branches(
        self,
        *,
        story_context: str,
    ) -> list[dict]:
        """Generate 2-3 story branch options.

        Returns:
            List of dicts with id and description.
        """
        user_prompt = MVP_STORY_BRANCH_PROMPT.format(story_context=story_context)

        messages = [
            LLMMessage(role="system", content=MVP_STORY_SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_prompt),
        ]

        response = await self._llm.generate(
            messages=messages,
            max_tokens=500,
            temperature=0.8,
        )

        return self._parse_json_branches(response.content)

    async def continue_from_branch(
        self,
        *,
        story_context: str,
        selected_branch: str,
    ) -> str:
        """Generate continuation text based on selected branch.

        Returns:
            Continuation text string.
        """
        user_prompt = MVP_STORY_BRANCH_CONTINUE_PROMPT.format(
            story_context=story_context,
            selected_branch=selected_branch,
        )

        messages = [
            LLMMessage(role="system", content=MVP_STORY_SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_prompt),
        ]

        response = await self._llm.generate(
            messages=messages,
            max_tokens=1000,
            temperature=0.8,
        )

        return response.content.strip()

    # =========================================================================
    # Q&A
    # =========================================================================

    async def generate_questions(
        self,
        *,
        story_context: str,
        age: int = 5,
    ) -> list[dict]:
        """Generate Q&A questions based on story content.

        Returns:
            List of dicts with id and text.
        """
        user_prompt = MVP_STORY_QA_GENERATE_PROMPT.format(
            story_context=story_context,
            age=age,
        )

        messages = [
            LLMMessage(role="system", content=MVP_STORY_SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_prompt),
        ]

        response = await self._llm.generate(
            messages=messages,
            max_tokens=500,
            temperature=0.7,
        )

        return self._parse_json_questions(response.content)

    async def answer_question(
        self,
        *,
        story_context: str,
        question: str,
        age: int = 5,
    ) -> str:
        """Answer a question based on story context.

        Returns:
            Answer text string.
        """
        user_prompt = MVP_STORY_QA_ANSWER_PROMPT.format(
            story_context=story_context,
            question=question,
            age=age,
        )

        messages = [
            LLMMessage(role="system", content=MVP_STORY_SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_prompt),
        ]

        response = await self._llm.generate(
            messages=messages,
            max_tokens=500,
            temperature=0.7,
        )

        return response.content.strip()

    # =========================================================================
    # TTS
    # =========================================================================

    async def generate_tts(
        self,
        *,
        text_content: str,
        voice_id: str,
    ) -> dict:
        """Generate TTS audio from text content.

        Returns:
            Dict with audio_content (base64), content_type, duration_ms.
        """
        tts_request = TTSRequest(
            text=text_content,
            voice_id=voice_id,
            provider=self._tts.name,
            language="zh-TW",
        )

        result = await self._tts.synthesize(tts_request)

        # Encode audio data as base64
        audio_base64 = base64.b64encode(result.audio.data).decode("utf-8")

        return {
            "audio_content": audio_base64,
            "content_type": f"audio/{result.audio.format.value}",
            "duration_ms": result.duration_ms,
        }

    # =========================================================================
    # Helpers
    # =========================================================================

    @staticmethod
    def _parse_json_branches(llm_response: str) -> list[dict]:
        """Parse LLM JSON response for branch options."""
        data = _extract_json(llm_response)
        if data and "branches" in data:
            return [
                {"id": b.get("id", str(i + 1)), "description": b.get("description", "")}
                for i, b in enumerate(data["branches"])
            ]
        return [
            {"id": "1", "description": "繼續探索"},
            {"id": "2", "description": "回家休息"},
            {"id": "3", "description": "尋找新朋友"},
        ]

    @staticmethod
    def _parse_json_questions(llm_response: str) -> list[dict]:
        """Parse LLM JSON response for Q&A questions."""
        data = _extract_json(llm_response)
        if data and "questions" in data:
            return [
                {"id": q.get("id", str(i + 1)), "text": q.get("text", "")}
                for i, q in enumerate(data["questions"])
            ]
        return [
            {"id": "1", "text": "你覺得故事中的主角做得對嗎？為什麼？"},
            {"id": "2", "text": "如果你是主角，你會怎麼做？"},
            {"id": "3", "text": "這個故事教了我們什麼道理？"},
        ]


def _extract_json(text: str) -> dict | None:
    """Extract JSON from LLM response, handling markdown code blocks."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM response as JSON: %s", text[:200])
        return None
