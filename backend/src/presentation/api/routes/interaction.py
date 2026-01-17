"""Interaction API Routes."""

import base64
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from src.presentation.schemas.interaction import (
    InteractionResponse,
    ConversationMessage,
)
from src.presentation.api.dependencies import get_voice_interaction_use_case
from src.application.use_cases.voice_interaction import (
    VoiceInteractionUseCase,
    VoiceInteractionInput,
)
from src.domain.entities.audio import AudioData, AudioFormat

router = APIRouter()


@router.post("/voice", response_model=InteractionResponse)
async def voice_interaction(
    audio: UploadFile = File(..., description="User audio input"),
    stt_provider: str = Form(..., description="STT provider"),
    llm_provider: str = Form(..., description="LLM provider"),
    tts_provider: str = Form(..., description="TTS provider"),
    voice_id: str = Form(..., description="TTS voice ID"),
    system_prompt: str = Form(default="", description="System prompt for LLM"),
    conversation_history: str = Form(default="[]", description="JSON array of previous messages"),
    language: str = Form(default="zh-TW", description="Language code"),
    max_response_tokens: int = Form(default=150, description="Max LLM response tokens"),
    use_case: VoiceInteractionUseCase = Depends(get_voice_interaction_use_case),
):
    """Process voice interaction: STT -> LLM -> TTS."""
    import json

    try:
        # Read audio data
        audio_bytes = await audio.read()
        audio_format = AudioFormat.WEBM  # Assume WebM from browser

        if audio.filename:
            if audio.filename.endswith(".wav"):
                audio_format = AudioFormat.WAV
            elif audio.filename.endswith(".mp3"):
                audio_format = AudioFormat.MP3

        audio_data = AudioData(
            data=audio_bytes,
            format=audio_format,
            sample_rate=16000,
        )

        # Parse conversation history
        try:
            history = json.loads(conversation_history)
            if not isinstance(history, list):
                history = []
        except json.JSONDecodeError:
            history = []

        input_data = VoiceInteractionInput(
            user_audio=audio_data,
            stt_provider=stt_provider,
            llm_provider=llm_provider,
            tts_provider=tts_provider,
            voice_id=voice_id,
            system_prompt=system_prompt,
            conversation_history=history,
            language=language,
            max_response_tokens=max_response_tokens,
            user_id="anonymous",
        )

        output = await use_case.execute(input_data)

        return InteractionResponse(
            user_transcript=output.user_transcript,
            ai_response_text=output.ai_response_text,
            ai_response_audio_base64=base64.b64encode(
                output.ai_response_audio.data
            ).decode("utf-8"),
            audio_format=output.ai_response_audio.format.value,
            stt_latency_ms=output.stt_latency_ms,
            llm_latency_ms=output.llm_latency_ms,
            tts_latency_ms=output.tts_latency_ms,
            total_latency_ms=output.total_latency_ms,
            updated_history=[
                ConversationMessage(role=m["role"], content=m["content"])
                for m in output.updated_history
            ],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Interaction failed: {str(e)}")
