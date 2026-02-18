"""Story Experience MVP API routes.

Feature: 016-story-experience-mvp
REST endpoints for parent story experience interface.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.application.interfaces.llm_provider import ILLMProvider
from src.application.interfaces.tts_provider import ITTSProvider
from src.application.use_cases.story_experience import StoryExperienceUseCase
from src.presentation.api.dependencies import get_llm_providers, get_tts_providers
from src.presentation.api.schemas.story_experience_schemas import (
    BranchRequest,
    BranchResponse,
    GenerateContentRequest,
    GenerateContentResponse,
    QARequest,
    QAResponse,
    TTSGenerateRequest,
    TTSGenerateResponse,
    VoiceOptionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/story-experience", tags=["Story Experience"])


# =============================================================================
# Dependency
# =============================================================================


def get_story_experience_use_case(
    llm_providers: Annotated[dict[str, ILLMProvider], Depends(get_llm_providers)],
    tts_providers: Annotated[dict[str, ITTSProvider], Depends(get_tts_providers)],
) -> StoryExperienceUseCase:
    """Get StoryExperienceUseCase with Gemini LLM and TTS."""
    # Prefer gemini for both LLM and TTS
    llm = llm_providers.get("gemini")
    if not llm:
        # Fallback to any available LLM
        if llm_providers:
            llm = next(iter(llm_providers.values()))
        else:
            raise HTTPException(
                status_code=503,
                detail="No LLM provider available. Please configure GEMINI_API_KEY.",
            )

    tts = tts_providers.get("gemini")
    if not tts:
        # Fallback to any available TTS
        if tts_providers:
            tts = next(iter(tts_providers.values()))
        else:
            raise HTTPException(
                status_code=503,
                detail="No TTS provider available. Please configure GEMINI_API_KEY.",
            )

    return StoryExperienceUseCase(llm_provider=llm, tts_provider=tts)


# =============================================================================
# Content Generation
# =============================================================================


@router.post("/generate", response_model=GenerateContentResponse)
async def generate_content(
    request: GenerateContentRequest,
    use_case: Annotated[StoryExperienceUseCase, Depends(get_story_experience_use_case)],
) -> GenerateContentResponse:
    """Generate story or song content from parent input parameters."""
    try:
        result = await use_case.generate_content(
            age=request.age,
            educational_content=request.educational_content,
            values=request.values,
            emotions=request.emotions,
            favorite_character=request.favorite_character,
            content_type=request.content_type,
        )
        return GenerateContentResponse(**result)
    except Exception as e:
        logger.exception("Content generation failed")
        raise HTTPException(status_code=500, detail=f"內容生成失敗：{e}") from e


# =============================================================================
# Story Branching
# =============================================================================


@router.post("/branch", response_model=BranchResponse)
async def generate_branch(
    request: BranchRequest,
    use_case: Annotated[StoryExperienceUseCase, Depends(get_story_experience_use_case)],
) -> BranchResponse:
    """Generate branch options or continue from a selected branch."""
    try:
        if request.selected_branch:
            # Continue from selected branch
            text_content = await use_case.continue_from_branch(
                story_context=request.story_context,
                selected_branch=request.selected_branch,
            )
            return BranchResponse(
                content_id=request.content_id,
                text_content=text_content,
            )
        else:
            # Generate branch options
            branches_data = await use_case.generate_branches(
                story_context=request.story_context,
            )
            return BranchResponse(
                branches=[{"id": b["id"], "description": b["description"]} for b in branches_data],
            )
    except Exception as e:
        logger.exception("Branch generation failed")
        raise HTTPException(status_code=500, detail=f"故事走向生成失敗：{e}") from e


# =============================================================================
# Q&A
# =============================================================================


@router.post("/qa", response_model=QAResponse)
async def generate_qa(
    request: QARequest,
    use_case: Annotated[StoryExperienceUseCase, Depends(get_story_experience_use_case)],
) -> QAResponse:
    """Generate Q&A questions or answer a question."""
    try:
        if request.question:
            # Answer a specific question
            answer = await use_case.answer_question(
                story_context=request.story_context,
                question=request.question,
            )
            return QAResponse(question=request.question, answer=answer)
        else:
            # Generate questions
            questions_data = await use_case.generate_questions(
                story_context=request.story_context,
            )
            return QAResponse(
                questions=[{"id": q["id"], "text": q["text"]} for q in questions_data],
            )
    except Exception as e:
        logger.exception("Q&A generation failed")
        raise HTTPException(status_code=500, detail=f"Q&A 生成失敗：{e}") from e


# =============================================================================
# TTS
# =============================================================================


@router.post("/tts", response_model=TTSGenerateResponse)
async def generate_tts(
    request: TTSGenerateRequest,
    use_case: Annotated[StoryExperienceUseCase, Depends(get_story_experience_use_case)],
) -> TTSGenerateResponse:
    """Generate TTS audio from text content."""
    try:
        result = await use_case.generate_tts(
            text_content=request.text_content,
            voice_id=request.voice_id,
        )
        return TTSGenerateResponse(**result)
    except Exception as e:
        logger.exception("TTS generation failed")
        raise HTTPException(status_code=500, detail=f"TTS 音頻生成失敗：{e}") from e


# =============================================================================
# Voices
# =============================================================================


@router.get("/voices", response_model=list[VoiceOptionResponse])
async def list_voices(
    tts_providers: Annotated[dict[str, ITTSProvider], Depends(get_tts_providers)],
) -> list[VoiceOptionResponse]:
    """List available Chinese TTS voices."""
    tts = tts_providers.get("gemini")
    if not tts:
        if tts_providers:
            tts = next(iter(tts_providers.values()))
        else:
            return []

    try:
        voices = await tts.list_voices()
        # Filter for Chinese voices and convert to response format
        chinese_voices = []
        for voice in voices:
            # Include voices that support Chinese or are from Gemini (all support zh)
            if tts.name == "gemini" or "zh" in voice.language.lower():
                chinese_voices.append(
                    VoiceOptionResponse(
                        id=voice.id,
                        name=voice.name,
                        language=voice.language or "zh-TW",
                        gender=voice.gender,
                    )
                )

        return chinese_voices
    except Exception:
        logger.exception("Failed to list voices")
        # Return Gemini default voices as fallback
        return [
            VoiceOptionResponse(id="Kore", name="Kore", language="zh-TW"),
            VoiceOptionResponse(id="Aoede", name="Aoede", language="zh-TW"),
            VoiceOptionResponse(id="Puck", name="Puck", language="zh-TW"),
            VoiceOptionResponse(id="Zephyr", name="Zephyr", language="zh-TW"),
        ]
