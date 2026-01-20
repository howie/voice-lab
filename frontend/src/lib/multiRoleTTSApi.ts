/**
 * Multi-Role TTS API Client
 * T029: Create API client for multi-role TTS endpoints
 */

import { api } from './api'
import type {
  CapabilitiesResponse,
  DialogueTurn,
  MultiRoleTTSResult,
  ParseDialogueResponse,
  ProviderMultiRoleCapability,
  VoiceAssignment,
} from '@/types/multi-role-tts'

// Request types (snake_case for API compatibility)
interface ParseDialogueRequest {
  text: string
}

interface SynthesizeRequest {
  provider: string
  turns: Array<{
    speaker: string
    text: string
    index: number
  }>
  voice_assignments: Array<{
    speaker: string
    voice_id: string
    voice_name?: string
  }>
  language?: string
  output_format?: string
  gap_ms?: number
  crossfade_ms?: number
}

// API Response types (snake_case from backend)
interface ApiCapabilitiesResponse {
  providers: Array<{
    provider_name: string
    support_type: string
    max_speakers: number
    character_limit: number
    advanced_features: string[]
    notes?: string
  }>
}

interface ApiParseResponse {
  turns: Array<{
    speaker: string
    text: string
    index: number
  }>
  speakers: string[]
  total_characters: number
}

interface ApiSynthesizeResponse {
  audio_url?: string
  audio_content?: string // base64
  content_type: string
  duration_ms: number
  latency_ms: number
  provider: string
  synthesis_mode: string
  turn_timings?: Array<{
    turn_index: number
    start_ms: number
    end_ms: number
  }>
}

/**
 * Transform API response to frontend types (snake_case -> camelCase)
 */
function transformCapability(
  cap: ApiCapabilitiesResponse['providers'][0]
): ProviderMultiRoleCapability {
  return {
    providerName: cap.provider_name,
    supportType: cap.support_type as 'native' | 'segmented' | 'unsupported',
    maxSpeakers: cap.max_speakers,
    characterLimit: cap.character_limit,
    advancedFeatures: cap.advanced_features,
    notes: cap.notes,
  }
}

function transformParseResponse(resp: ApiParseResponse): ParseDialogueResponse {
  return {
    turns: resp.turns.map((t) => ({
      speaker: t.speaker,
      text: t.text,
      index: t.index,
    })),
    speakers: resp.speakers,
    totalCharacters: resp.total_characters,
  }
}

function transformSynthesizeResponse(
  resp: ApiSynthesizeResponse
): MultiRoleTTSResult {
  return {
    audioUrl: resp.audio_url,
    audioContent: resp.audio_content,
    contentType: resp.content_type,
    durationMs: resp.duration_ms,
    latencyMs: resp.latency_ms,
    provider: resp.provider,
    synthesisMode: resp.synthesis_mode as 'native' | 'segmented' | 'unsupported',
    turnTimings: resp.turn_timings?.map((tt) => ({
      turnIndex: tt.turn_index,
      startMs: tt.start_ms,
      endMs: tt.end_ms,
    })),
  }
}

/**
 * Multi-Role TTS API endpoints
 */
export const multiRoleTTSApi = {
  /**
   * Get capabilities for all providers
   */
  getCapabilities: async (): Promise<CapabilitiesResponse> => {
    const response = await api.get<ApiCapabilitiesResponse>(
      '/tts/multi-role/capabilities'
    )
    return {
      providers: response.data.providers.map(transformCapability),
    }
  },

  /**
   * Parse dialogue text into structured turns
   */
  parseDialogue: async (text: string): Promise<ParseDialogueResponse> => {
    const response = await api.post<ApiParseResponse>(
      '/tts/multi-role/parse',
      { text } as ParseDialogueRequest
    )
    return transformParseResponse(response.data)
  },

  /**
   * Synthesize multi-role dialogue (returns base64 audio)
   */
  synthesize: async (
    provider: string,
    turns: DialogueTurn[],
    voiceAssignments: VoiceAssignment[],
    options?: {
      language?: string
      outputFormat?: string
      gapMs?: number
      crossfadeMs?: number
      signal?: AbortSignal
    }
  ): Promise<MultiRoleTTSResult> => {
    const request: SynthesizeRequest = {
      provider,
      turns: turns.map((t) => ({
        speaker: t.speaker,
        text: t.text,
        index: t.index,
      })),
      voice_assignments: voiceAssignments.map((va) => ({
        speaker: va.speaker,
        voice_id: va.voiceId,
        voice_name: va.voiceName,
      })),
      language: options?.language,
      output_format: options?.outputFormat,
      gap_ms: options?.gapMs,
      crossfade_ms: options?.crossfadeMs,
    }

    const response = await api.post<ApiSynthesizeResponse>(
      '/tts/multi-role/synthesize',
      request,
      { signal: options?.signal }
    )
    return transformSynthesizeResponse(response.data)
  },

  /**
   * Synthesize multi-role dialogue (returns binary audio blob)
   */
  synthesizeBinary: async (
    provider: string,
    turns: DialogueTurn[],
    voiceAssignments: VoiceAssignment[],
    options?: {
      language?: string
      outputFormat?: string
      gapMs?: number
      crossfadeMs?: number
    }
  ): Promise<{
    blob: Blob
    durationMs: number
    latencyMs: number
    provider: string
    synthesisMode: string
  }> => {
    const request: SynthesizeRequest = {
      provider,
      turns: turns.map((t) => ({
        speaker: t.speaker,
        text: t.text,
        index: t.index,
      })),
      voice_assignments: voiceAssignments.map((va) => ({
        speaker: va.speaker,
        voice_id: va.voiceId,
        voice_name: va.voiceName,
      })),
      language: options?.language,
      output_format: options?.outputFormat,
      gap_ms: options?.gapMs,
      crossfade_ms: options?.crossfadeMs,
    }

    const response = await api.post('/tts/multi-role/synthesize/binary', request, {
      responseType: 'blob',
    })

    return {
      blob: response.data,
      durationMs: parseInt(response.headers['x-duration-ms'] || '0', 10),
      latencyMs: parseInt(response.headers['x-latency-ms'] || '0', 10),
      provider: response.headers['x-provider'] || provider,
      synthesisMode: response.headers['x-synthesis-mode'] || 'segmented',
    }
  },
}
