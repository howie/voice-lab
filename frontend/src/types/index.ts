// Re-export multi-role TTS types
export type {
  MultiRoleSupportType,
  MultiRoleTTSProvider,
  DialogueTurn,
  VoiceAssignment,
  ProviderMultiRoleCapability,
  TurnTiming,
  MultiRoleTTSRequest,
  MultiRoleTTSResult,
  ParseDialogueResponse,
  CapabilitiesResponse,
  MultiRoleTTSError,
} from './multi-role-tts'

// Re-export voice customization types
export type {
  VoiceCustomization,
  VoiceWithCustomization,
  UpdateVoiceCustomizationRequest,
  BulkUpdateItem,
  BulkUpdateVoiceCustomizationRequest,
  BulkUpdateFailure,
  BulkUpdateResult,
  VoiceListResponse,
  VoiceFilterParams,
  CustomizationFilterParams,
} from './voice-customization'

// Provider types
export type TTSProvider = 'gcp' | 'gemini' | 'azure' | 'elevenlabs' | 'voai'
export type STTProvider = 'gcp' | 'azure' | 'voai'
export type LLMProvider = 'anthropic' | 'openai'

export type TestType = 'tts' | 'stt' | 'interaction'

// TTS types
export interface TTSRequest {
  text: string
  provider: TTSProvider
  voice_id: string
  language?: string
  speed?: number
  pitch?: number
  volume?: number
  output_format?: 'mp3' | 'wav' | 'opus'
}

export interface TTSResponse {
  audio_url: string
  duration_ms: number
  latency_ms: number
  cost_estimate: number
  provider: string
  voice_id: string
  format: string
}

// STT types
export interface STTResponse {
  transcript: string
  confidence: number
  latency_ms: number
  words: Array<{
    word: string
    start_time: number
    end_time: number
  }>
  provider: string
}

// Interaction types
export interface InteractionConfig {
  stt_provider: STTProvider
  llm_provider: LLMProvider
  tts_provider: TTSProvider
  voice_id: string
  system_prompt?: string
  language?: string
}

export interface InteractionResponse {
  user_transcript: string
  ai_text: string
  ai_audio_url: string
  stt_latency_ms: number
  llm_latency_ms: number
  tts_latency_ms: number
  total_latency_ms: number
}

// History types
export interface TestRecord {
  id: string
  user_id: string
  test_type: TestType
  created_at: string
  metadata: Record<string, unknown>
}

// Voice types
export interface VoiceProfile {
  id: string
  provider: string
  voice_id: string
  display_name: string
  language: string
  gender?: string
  description?: string
  sample_audio_url?: string
}
