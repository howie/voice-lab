"""Core StoryPal story engine service.

LLM-driven interactive story engine that generates branching
narratives for children with structured JSON output.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from src.application.interfaces.llm_provider import ILLMProvider, LLMMessage
from src.domain.entities.story import (
    SceneInfo,
    StoryBranch,
    StorySession,
    StoryTemplate,
    StoryTurnType,
)
from src.domain.services.story.prompts import (
    STORY_CHOICE_PROMPT,
    STORY_CONTINUATION_PROMPT,
    STORY_OPENING_PROMPT,
    STORY_QUESTION_RESPONSE_PROMPT,
    STORY_SYSTEM_PROMPT_TEMPLATE,
)

logger = logging.getLogger(__name__)


@dataclass
class StorySegment:
    """A parsed segment from LLM story response."""

    type: StoryTurnType
    content: str
    character_name: str | None = None
    emotion: str = "neutral"
    scene: str | None = None


@dataclass
class StoryResponse:
    """Full parsed response from story LLM call."""

    segments: list[StorySegment] = field(default_factory=list)
    scene_change: SceneInfo | None = None
    story_summary: str = ""


class StoryEngine:
    """LLM-driven interactive story engine."""

    def __init__(self, llm_provider: ILLMProvider) -> None:
        self._llm = llm_provider

    async def start_story(
        self,
        template: StoryTemplate,
        language: str = "繁體中文",
    ) -> tuple[list[StorySegment], SceneInfo | None]:
        """Generate opening story segments from template.

        Args:
            template: Story template with characters, scenes, and prompts.
            language: Language for the story output.

        Returns:
            Tuple of (story segments, optional scene info).
        """
        system_prompt = self._build_system_prompt(template)
        user_prompt = STORY_OPENING_PROMPT.format(language=language)

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]

        response = await self._call_llm(messages)
        parsed = self._parse_story_response(response)
        return parsed.segments, parsed.scene_change

    async def continue_story(
        self,
        session: StorySession,
        child_input: str,
    ) -> tuple[list[StorySegment], SceneInfo | None]:
        """Continue story based on child's choice or response.

        Args:
            session: Current story session with history.
            child_input: Child's text input (choice or free response).

        Returns:
            Tuple of (story segments, optional scene change).
        """
        story_summary = session.story_state.get("summary", "故事剛開始")
        current_scene = session.current_scene or "未知場景"

        user_prompt = STORY_CONTINUATION_PROMPT.format(
            child_input=child_input,
            story_summary=story_summary,
            current_scene=current_scene,
        )

        messages = self._build_conversation_messages(session, user_prompt)
        response = await self._call_llm(messages)
        parsed = self._parse_story_response(response)
        return parsed.segments, parsed.scene_change

    async def handle_question(
        self,
        session: StorySession,
        question: str,
    ) -> tuple[list[StorySegment], SceneInfo | None]:
        """Handle child's off-topic question, then return to story.

        Args:
            session: Current story session.
            question: Child's question text.

        Returns:
            Tuple of (response segments, optional scene change).
        """
        story_summary = session.story_state.get("summary", "故事剛開始")
        characters_info = self._format_characters(session.characters_config)

        user_prompt = STORY_QUESTION_RESPONSE_PROMPT.format(
            question=question,
            story_summary=story_summary,
            characters_info=characters_info,
        )

        messages = self._build_conversation_messages(session, user_prompt)
        response = await self._call_llm(messages)
        parsed = self._parse_story_response(response)
        return parsed.segments, parsed.scene_change

    async def generate_choice(
        self,
        session: StorySession,
    ) -> StoryBranch:
        """Generate a decision point for the child.

        Args:
            session: Current story session.

        Returns:
            StoryBranch with prompt and options.
        """
        story_summary = session.story_state.get("summary", "故事剛開始")
        current_scene = session.current_scene or "未知場景"

        user_prompt = STORY_CHOICE_PROMPT.format(
            story_summary=story_summary,
            current_scene=current_scene,
        )

        messages = self._build_conversation_messages(session, user_prompt)
        response = await self._call_llm(messages)
        parsed = self._parse_story_response(response)

        # Extract choice from the last choice_prompt segment
        options: list[str] = []
        prompt_text = ""
        for seg in parsed.segments:
            if seg.type == StoryTurnType.CHOICE_PROMPT:
                prompt_text = seg.content
                # Parse numbered options from content
                lines = seg.content.split("\n")
                for line in lines:
                    match = re.match(r"^\d+[.、]\s*(.+)$", line.strip())
                    if match:
                        options.append(match.group(1))

        return StoryBranch(
            prompt_text=prompt_text,
            options=options,
            context=parsed.story_summary,
        )

    def _build_system_prompt(self, template: StoryTemplate) -> str:
        """Build the system prompt from template."""
        characters_info = self._format_characters(template.characters)
        story_context = template.system_prompt or template.description

        return STORY_SYSTEM_PROMPT_TEMPLATE.format(
            age_min=template.target_age_min,
            age_max=template.target_age_max,
            story_context=story_context,
            characters_info=characters_info,
        )

    def _build_conversation_messages(
        self,
        session: StorySession,
        user_prompt: str,
    ) -> list[LLMMessage]:
        """Build conversation history context for LLM.

        Constructs a message list from the session's system prompt
        and recent turn history.
        """
        messages: list[LLMMessage] = []

        # Add system prompt from story state
        system_prompt = session.story_state.get("system_prompt", "")
        if system_prompt:
            messages.append(LLMMessage(role="system", content=system_prompt))

        # Add recent turns as conversation history (last 20 turns max)
        recent_turns = session.turns[-20:]
        for turn in recent_turns:
            if turn.turn_type in (
                StoryTurnType.CHILD_RESPONSE,
                StoryTurnType.QUESTION,
            ):
                messages.append(LLMMessage(role="user", content=turn.content))
            elif turn.turn_type in (
                StoryTurnType.NARRATION,
                StoryTurnType.DIALOGUE,
                StoryTurnType.CHOICE_PROMPT,
                StoryTurnType.ANSWER,
            ):
                messages.append(LLMMessage(role="assistant", content=turn.content))

        # Add current user prompt
        messages.append(LLMMessage(role="user", content=user_prompt))
        return messages

    def _format_characters(
        self,
        characters: list[Any],
    ) -> str:
        """Format character list for prompt insertion."""
        if not characters:
            return "無指定角色"

        lines = []
        for char in characters:
            line = f"- {char.name}：{char.description}"
            if char.emotion != "neutral":
                line += f"（目前情緒：{char.emotion}）"
            lines.append(line)
        return "\n".join(lines)

    async def _call_llm(self, messages: list[LLMMessage]) -> str:
        """Call LLM and return raw response content."""
        response = await self._llm.generate(
            messages=messages,
            max_tokens=1500,
            temperature=0.8,
        )
        return response.content

    def _parse_story_response(self, llm_response: str) -> StoryResponse:
        """Parse LLM JSON response into StoryResponse.

        Handles cases where the LLM wraps JSON in markdown code blocks.
        """
        # Strip markdown code block wrapper if present
        text = llm_response.strip()
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
        if match:
            text = match.group(1).strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM response as JSON, using raw text")
            return StoryResponse(
                segments=[
                    StorySegment(
                        type=StoryTurnType.NARRATION,
                        content=llm_response.strip(),
                    )
                ],
            )

        # Parse segments
        segments: list[StorySegment] = []
        for seg_data in data.get("segments", []):
            turn_type = self._map_segment_type(seg_data.get("type", "narration"))
            segments.append(
                StorySegment(
                    type=turn_type,
                    content=seg_data.get("content", ""),
                    character_name=seg_data.get("character_name"),
                    emotion=seg_data.get("emotion", "neutral"),
                    scene=seg_data.get("scene"),
                )
            )

        # Parse scene change
        scene_change = None
        sc_data = data.get("scene_change")
        if sc_data:
            scene_change = SceneInfo(
                name=sc_data.get("name", ""),
                description=sc_data.get("description", ""),
                bgm_prompt=sc_data.get("bgm_prompt", ""),
                mood=sc_data.get("mood", "neutral"),
            )

        return StoryResponse(
            segments=segments,
            scene_change=scene_change,
            story_summary=data.get("story_summary", ""),
        )

    @staticmethod
    def _map_segment_type(type_str: str) -> StoryTurnType:
        """Map string type to StoryTurnType enum."""
        mapping = {
            "narration": StoryTurnType.NARRATION,
            "dialogue": StoryTurnType.DIALOGUE,
            "choice_prompt": StoryTurnType.CHOICE_PROMPT,
            "child_response": StoryTurnType.CHILD_RESPONSE,
            "question": StoryTurnType.QUESTION,
            "answer": StoryTurnType.ANSWER,
        }
        return mapping.get(type_str, StoryTurnType.NARRATION)
