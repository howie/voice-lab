"""WebSocket handler for StoryPal interactive story sessions.

Feature: StoryPal — AI Interactive Story Companion

Handles the story interaction protocol: configure → segments → choices → continuation.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from uuid import UUID

from fastapi import WebSocket

from src.application.interfaces.llm_provider import ILLMProvider
from src.domain.entities.story import (
    SceneInfo,
    StorySession,
    StorySessionStatus,
    StoryTurnType,
)
from src.domain.services.story.engine import StoryEngine, StorySegment
from src.domain.services.story.templates import get_default_templates
from src.infrastructure.websocket.base_handler import (
    BaseWebSocketHandler,
    MessageType,
    WebSocketMessage,
)

logger = logging.getLogger(__name__)


class StoryMessageType:
    """Story-specific message types."""

    # Client -> Server
    STORY_CONFIGURE = "story_configure"
    STORY_CHOICE = "story_choice"

    # Server -> Client
    STORY_SEGMENT = "story_segment"
    CHOICE_PROMPT = "choice_prompt"
    SCENE_CHANGE = "scene_change"
    STORY_END = "story_end"


class StoryWebSocketHandler(BaseWebSocketHandler):
    """Handles WebSocket communication for interactive story sessions."""

    def __init__(
        self,
        websocket: WebSocket,
        user_id: UUID,
        llm_provider: ILLMProvider,
        logger_instance: logging.Logger | None = None,
    ) -> None:
        super().__init__(websocket, logger=logger_instance or logger)
        self._user_id = user_id
        self._engine = StoryEngine(llm_provider)
        self._session: StorySession | None = None
        self._turn_counter = 0
        self._is_generating = False

    async def on_connect(self) -> None:
        """Handle new connection."""
        await self.send_message(
            WebSocketMessage(
                type=MessageType.CONNECTED,
                data={"message": "歡迎來到 StoryPal！準備好聽故事了嗎？"},
            )
        )

    async def on_disconnect(self) -> None:
        """Handle disconnect - save session state."""
        if self._session and self._session.status == StorySessionStatus.ACTIVE:
            self._session.pause()
        self._logger.info(f"Story session disconnected for user {self._user_id}")

    async def run(self) -> None:
        """Main handler loop for story messages."""
        try:
            while self.is_connected:
                try:
                    data = await self._websocket.receive_json()
                except Exception:
                    break

                msg_type = data.get("type", "")
                msg_data = data.get("data", {})

                if msg_type == StoryMessageType.STORY_CONFIGURE:
                    await self._handle_configure(msg_data)
                elif msg_type == StoryMessageType.STORY_CHOICE:
                    await self._handle_choice(msg_data)
                elif msg_type == "text_input":
                    await self._handle_text_input(msg_data)
                elif msg_type == "interrupt":
                    await self._handle_interrupt()
                elif msg_type == "ping":
                    await self.send_message(WebSocketMessage(type=MessageType.PONG))
                else:
                    self._logger.warning(f"Unknown message type: {msg_type}")
        except Exception as e:
            self._logger.error(f"Story handler error: {e}")
            await self.send_error("STORY_ERROR", str(e))

    async def _handle_configure(self, data: dict[str, Any]) -> None:
        """Handle story configuration and start the story."""
        template_id = data.get("template_id")
        language = data.get("language", "zh-TW")
        characters_config = data.get("characters_config")

        # Find template
        template = None
        if template_id:
            for t in get_default_templates():
                if str(t.id) == template_id:
                    template = t
                    break

        if not template:
            await self.send_error("TEMPLATE_NOT_FOUND", f"Template {template_id} not found")
            return

        # Create in-memory session
        from src.domain.entities.story import StoryCharacter

        chars = template.characters
        if characters_config:
            chars = [StoryCharacter(**c) for c in characters_config]

        self._session = StorySession(
            title=template.name,
            language=language,
            user_id=str(self._user_id),
            template_id=template.id,
            characters_config=chars,
            story_state={"system_prompt": self._engine._build_system_prompt(template)},
        )
        self._turn_counter = 0

        # Generate opening
        self._is_generating = True
        try:
            segments, scene_change = await self._engine.start_story(template, language)
            await self._send_story_segments(segments, scene_change)
        except Exception as e:
            self._logger.error(f"Failed to start story: {e}")
            await self.send_error("GENERATION_ERROR", f"無法開始故事：{e}")
        finally:
            self._is_generating = False

    async def _handle_choice(self, data: dict[str, Any]) -> None:
        """Handle child's choice selection."""
        if not self._session:
            await self.send_error("NO_SESSION", "尚未開始故事")
            return

        choice = data.get("choice", "")
        if not choice:
            await self.send_error("EMPTY_CHOICE", "請選擇一個選項")
            return

        # Record child's choice as a turn
        from src.domain.entities.story import StoryTurn

        self._turn_counter += 1
        child_turn = StoryTurn(
            session_id=self._session.id,
            turn_number=self._turn_counter,
            turn_type=StoryTurnType.CHILD_RESPONSE,
            content=choice,
            child_choice=choice,
        )
        self._session.add_turn(child_turn)

        # Continue story
        self._is_generating = True
        try:
            segments, scene_change = await self._engine.continue_story(self._session, choice)
            await self._send_story_segments(segments, scene_change)
        except Exception as e:
            self._logger.error(f"Failed to continue story: {e}")
            await self.send_error("GENERATION_ERROR", f"無法繼續故事：{e}")
        finally:
            self._is_generating = False

    async def _handle_text_input(self, data: dict[str, Any]) -> None:
        """Handle free text input (questions or responses)."""
        if not self._session:
            await self.send_error("NO_SESSION", "尚未開始故事")
            return

        text = data.get("text", "")
        if not text:
            return

        # Determine if this is a question or a story response
        is_question = any(
            text.strip().endswith(c) for c in ("？", "?", "嗎", "呢", "為什麼", "怎麼")
        )

        from src.domain.entities.story import StoryTurn

        self._turn_counter += 1
        child_turn = StoryTurn(
            session_id=self._session.id,
            turn_number=self._turn_counter,
            turn_type=StoryTurnType.QUESTION if is_question else StoryTurnType.CHILD_RESPONSE,
            content=text,
        )
        self._session.add_turn(child_turn)

        self._is_generating = True
        try:
            if is_question:
                segments, scene_change = await self._engine.handle_question(self._session, text)
            else:
                segments, scene_change = await self._engine.continue_story(self._session, text)
            await self._send_story_segments(segments, scene_change)
        except Exception as e:
            self._logger.error(f"Failed to handle input: {e}")
            await self.send_error("GENERATION_ERROR", f"處理失敗：{e}")
        finally:
            self._is_generating = False

    async def _handle_interrupt(self) -> None:
        """Handle interrupt/barge-in."""
        self._is_generating = False
        if self._session:
            self._session.pause()
        await self.send_message(
            WebSocketMessage(
                type=MessageType.INTERRUPTED,
                data={"message": "故事已暫停"},
            )
        )

    async def _send_story_segments(
        self,
        segments: list[StorySegment],
        scene_change: SceneInfo | None,
    ) -> None:
        """Send story segments to client with appropriate delays."""
        if not self.is_connected:
            return

        # Send scene change first if present
        if scene_change:
            await self._websocket.send_json(
                {
                    "type": StoryMessageType.SCENE_CHANGE,
                    "data": {
                        "scene_name": scene_change.name,
                        "description": scene_change.description,
                        "bgm_prompt": scene_change.bgm_prompt,
                        "mood": scene_change.mood,
                    },
                }
            )
            if self._session:
                self._session.current_scene = scene_change.name

        # Send each segment with a small delay for natural pacing
        for seg in segments:
            if not self.is_connected or not self._is_generating:
                break

            # Record turn
            from src.domain.entities.story import StoryTurn

            self._turn_counter += 1
            turn = StoryTurn(
                session_id=self._session.id if self._session else UUID(int=0),
                turn_number=self._turn_counter,
                turn_type=seg.type,
                content=seg.content,
                character_name=seg.character_name,
                bgm_scene=seg.scene,
            )
            if self._session:
                self._session.add_turn(turn)

            if seg.type == StoryTurnType.CHOICE_PROMPT:
                # Parse options from content
                options = []
                import re

                for line in seg.content.split("\n"):
                    match = re.match(r"^\d+[.、]\s*(.+)$", line.strip())
                    if match:
                        options.append(match.group(1))

                # Remove options from prompt text
                prompt_text = seg.content.split("\n")[0] if "\n" in seg.content else seg.content

                await self._websocket.send_json(
                    {
                        "type": StoryMessageType.CHOICE_PROMPT,
                        "data": {
                            "prompt": prompt_text,
                            "options": options,
                            "context": "",
                        },
                    }
                )
            else:
                await self._websocket.send_json(
                    {
                        "type": StoryMessageType.STORY_SEGMENT,
                        "data": {
                            "turn_type": seg.type.value,
                            "content": seg.content,
                            "character_name": seg.character_name,
                            "emotion": seg.emotion,
                            "scene": seg.scene,
                        },
                    }
                )

            # Small delay between segments for natural pacing
            if len(segments) > 1:
                await asyncio.sleep(0.3)

        # Update session summary
        if self._session and segments:
            last_content = segments[-1].content[:100]
            self._session.story_state["summary"] = last_content
