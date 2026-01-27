/**
 * Interaction Module TypeScript types.
 * Feature: 004-interaction-module
 *
 * T021: Types for real-time voice interaction with WebSocket support.
 */

// =============================================================================
// Enums and Constants
// =============================================================================

export type InteractionMode = 'realtime' | 'cascade'

export type SessionStatus = 'active' | 'completed' | 'disconnected' | 'error'

export type RealtimeProvider = 'openai' | 'gemini'

export type CascadeSTTProvider = 'azure' | 'gcp' | 'whisper'
export type CascadeLLMProvider = 'openai' | 'anthropic' | 'gemini' | 'azure-openai'
export type CascadeTTSProvider = 'azure' | 'gcp' | 'elevenlabs' | 'voai'

// WebSocket message types
export type WSMessageType =
  // Client -> Server
  | 'config'
  | 'audio_chunk'
  | 'end_turn'
  | 'interrupt'
  | 'ping'
  // Server -> Client
  | 'connected'
  | 'disconnected'
  | 'speech_started'
  | 'speech_ended'
  | 'transcript'
  | 'text_delta'
  | 'audio'
  | 'response_started'
  | 'response_ended'
  | 'interrupted'
  | 'error'
  | 'pong'

// =============================================================================
// Provider Configuration
// =============================================================================

export interface RealtimeProviderConfig {
  provider: RealtimeProvider
  model?: string
  voice?: string
  temperature?: number
}

export interface CascadeProviderConfig {
  stt_provider: CascadeSTTProvider
  stt_model?: string
  llm_provider: CascadeLLMProvider
  llm_model?: string
  tts_provider: CascadeTTSProvider
  tts_voice?: string
  language?: string
}

export type ProviderConfig = RealtimeProviderConfig | CascadeProviderConfig

// =============================================================================
// Session Types
// =============================================================================

export interface InteractionSession {
  id: string
  user_id: string
  mode: InteractionMode
  provider_config: ProviderConfig
  system_prompt: string
  status: SessionStatus
  started_at: string
  ended_at: string | null
  created_at: string
  updated_at: string
}

export interface ConversationTurn {
  id: string
  session_id: string
  turn_number: number
  user_audio_path: string | null
  user_transcript: string | null
  ai_response_text: string | null
  ai_audio_path: string | null
  interrupted: boolean
  started_at: string
  ended_at: string | null
}

export interface LatencyMetrics {
  id: string
  turn_id: string
  total_latency_ms: number
  stt_latency_ms: number | null
  llm_ttft_ms: number | null
  tts_ttfb_ms: number | null
  realtime_latency_ms: number | null
  created_at: string
}

// T061: Latency data included in response_ended WebSocket message
export interface TurnLatencyData {
  total_ms: number
  stt_ms: number | null
  llm_ttft_ms: number | null
  tts_ttfb_ms: number | null
  realtime_ms: number | null
  // T088: Interrupt latency (time AI was speaking before interrupted)
  interrupt_ms: number | null
}

export interface LatencyStats {
  total_turns: number
  avg_total_ms: number | null
  min_total_ms: number | null
  max_total_ms: number | null
  p95_total_ms: number | null
  avg_stt_ms: number | null
  avg_llm_ttft_ms: number | null
  avg_tts_ttfb_ms: number | null
}

// =============================================================================
// WebSocket Message Types
// =============================================================================

export interface WSMessage<T = unknown> {
  type: WSMessageType
  data: T
  session_id?: string
  turn_id?: string
}

// Client -> Server messages
export interface ConfigMessageData {
  config: ProviderConfig
  system_prompt: string
}

export interface AudioChunkMessageData {
  audio: string // base64 encoded
  format: 'pcm16' | 'webm'
  sample_rate: number
  is_final?: boolean
}

// Server -> Client messages
export interface ConnectedMessageData {
  user_id: string
  mode: InteractionMode
  session_id?: string
  status?: string
  // US4: Role names from session config
  user_role?: string
  ai_role?: string
}

export interface TranscriptMessageData {
  text: string
  is_final: boolean
  confidence?: number
  // US4: Role name for display
  role?: string
}

export interface TextDeltaMessageData {
  delta: string
  accumulated?: string
  // US4: Role name for display
  role?: string
}

export interface AudioMessageData {
  audio: string // base64 encoded
  format: 'pcm16' | 'mp3'
  is_first?: boolean
  is_final?: boolean
}

export interface ErrorMessageData {
  error_code: string
  message: string
  details?: Record<string, unknown>
}

// =============================================================================
// System Prompt Templates
// =============================================================================

export interface SystemPromptTemplate {
  id: string
  name: string
  description: string
  prompt_content: string
  category: string
  is_default: boolean
}

// US4: Scenario Template for role-play configuration
export interface ScenarioTemplate {
  id: string
  name: string
  description: string
  user_role: string
  ai_role: string
  scenario_context: string
  category: string
  is_default: boolean
  created_at: string
  updated_at: string
}

// =============================================================================
// API Request/Response Types
// =============================================================================

export interface SessionListParams {
  user_id: string
  mode?: InteractionMode
  status?: SessionStatus
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}

export interface SessionListResponse {
  sessions: InteractionSession[]
  total: number
  page: number
  page_size: number
}

// =============================================================================
// UI State Types
// =============================================================================

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error'

export type InteractionState =
  | 'idle' // Not connected
  | 'ready' // Connected, waiting for user
  | 'listening' // Recording user speech
  | 'processing' // AI is processing
  | 'speaking' // AI is speaking
  | 'interrupted' // User interrupted AI

export interface InteractionUIState {
  // Connection
  connectionStatus: ConnectionStatus
  interactionState: InteractionState

  // Session
  session: InteractionSession | null
  currentTurn: ConversationTurn | null

  // Audio
  isRecording: boolean
  isMuted: boolean
  inputVolume: number
  outputVolume: number

  // Transcripts
  userTranscript: string
  aiResponseText: string
  isTranscriptFinal: boolean

  // Latency tracking
  currentLatency: number | null
  sessionStats: LatencyStats | null

  // Errors
  error: string | null
}

// =============================================================================
// Configuration Options
// =============================================================================

export interface InteractionOptions {
  // Mode selection
  mode: InteractionMode
  providerConfig: ProviderConfig
  systemPrompt: string

  // US4: Role and scenario configuration
  userRole: string
  aiRole: string
  scenarioContext: string

  // Audio settings
  autoPlayResponse: boolean
  enableVAD: boolean
  vadSensitivity: number // 0-1

  // US5: Barge-in (interrupt) settings
  bargeInEnabled: boolean

  // Display settings
  showLatencyMetrics: boolean
  showTranscripts: boolean

  // Performance optimization
  // Lightweight mode: skip sync audio storage for lower latency V2V
  lightweightMode?: boolean
}

export const DEFAULT_INTERACTION_OPTIONS: InteractionOptions = {
  mode: 'realtime',
  providerConfig: {
    provider: 'openai',
    voice: 'alloy',
  },
  systemPrompt: '',
  // US4 defaults
  userRole: '使用者',
  aiRole: 'AI 助理',
  scenarioContext: '',
  // Audio settings
  autoPlayResponse: true,
  enableVAD: true,
  vadSensitivity: 0.5,
  // US5: Barge-in enabled by default
  bargeInEnabled: true,
  showLatencyMetrics: true,
  showTranscripts: true,
}

// =============================================================================
// Event Types (for hooks)
// =============================================================================

export interface InteractionEvents {
  onConnectionChange: (status: ConnectionStatus) => void
  onStateChange: (state: InteractionState) => void
  onSpeechStarted: () => void
  onSpeechEnded: () => void
  onTranscript: (transcript: string, isFinal: boolean) => void
  onTextDelta: (delta: string, accumulated: string) => void
  onAudioChunk: (audio: ArrayBuffer, isFirst: boolean, isFinal: boolean) => void
  onResponseEnded: () => void
  onInterrupted: () => void
  onError: (error: ErrorMessageData) => void
}

// =============================================================================
// Provider Info Types (T056)
// =============================================================================

export interface ProviderInfo {
  name: string
  display_name: string
  description?: string
  default_model?: string
  available_models?: string[]
  /** Whether the user has configured credentials for this provider */
  has_credentials?: boolean
  /** Whether the credentials are valid */
  is_valid?: boolean
}

export interface ProvidersResponse {
  stt_providers: ProviderInfo[]
  llm_providers: ProviderInfo[]
  tts_providers: ProviderInfo[]
}
