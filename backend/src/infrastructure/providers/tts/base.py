from typing import AsyncGenerator
from pipecat.services.ai_services import TTSService
from pipecat.frames.frames import AudioRawFrame, TTSAudioRawFrame, ErrorFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask
from pipecat.processors.aggregators.llm_response import LLMResponseAggregator
from pipecat.transport.network.websocket_server import WebsocketServerTransport, WebsocketServerParams

# Base infrastructure for Pipecat integration
# This file serves as a placeholder and utility collection for Pipecat setup.

async def create_tts_pipeline(
    tts_service: TTSService,
    text_input: str
) -> Pipeline:
    """
    Creates a simple TTS pipeline for batch synthesis.
    Note: For batch synthesis, we might not strictly need a full Pipecat pipeline 
    if we just use the service directly, but this standardizes the flow.
    """
    # In a real Pipecat flow, we usually have a transport.
    # For batch generation (server-side), we might iterate over the service output directly.
    pass

async def collect_audio_from_service(
    service: TTSService, 
    text: str
) -> bytes:
    """
    Helper to run TTS service and collect all audio bytes.
    Useful for the 'synthesize' batch endpoint.
    """
    audio_chunks = []
    
    # TTSService.run_tts returns an AsyncGenerator yielding frames
    # We need to handle the specific generator signature of the service
    try:
        # Assuming service.run_tts(text) yields frames
        async for frame in service.run_tts(text):
            if isinstance(frame, (AudioRawFrame, TTSAudioRawFrame)):
                audio_chunks.append(frame.audio)
            elif isinstance(frame, ErrorFrame):
                raise Exception(f"TTS Error: {frame.error}")
    except Exception as e:
        # Re-raise or handle
        raise e

    return b"".join(audio_chunks)