/**
 * Multi-Role TTS Types
 *
 * TypeScript types for multi-role dialogue text-to-speech synthesis.
 */

/**
 * Type of multi-role support a provider offers.
 */
export type MultiRoleSupportType = 'native' | 'segmented' | 'unsupported'

/**
 * Extended TTS provider type including all multi-role capable providers.
 */
export type MultiRoleTTSProvider =
  | 'elevenlabs'
  | 'azure'
  | 'gcp'
  | 'gemini'
  | 'openai'
  | 'cartesia'
  | 'deepgram'

/**
 * Represents a single turn in a dialogue.
 */
export interface DialogueTurn {
  /** Speaker identifier (e.g., 'A', 'B', 'Host') */
  speaker: string
  /** The text content of this turn */
  text: string
  /** Position in the dialogue sequence (0-based) */
  index: number
}

/**
 * Maps a speaker to a voice.
 */
export interface VoiceAssignment {
  /** Speaker identifier matching DialogueTurn.speaker */
  speaker: string
  /** Provider-specific voice ID */
  voiceId: string
  /** Human-readable voice name (optional, for display) */
  voiceName?: string
}

/**
 * Describes a provider's multi-role capabilities.
 */
export interface ProviderMultiRoleCapability {
  /** Provider identifier (e.g., 'elevenlabs', 'azure') */
  providerName: string
  /** Type of multi-role support */
  supportType: MultiRoleSupportType
  /** Maximum number of speakers supported */
  maxSpeakers: number
  /** Maximum total characters for the dialogue */
  characterLimit: number
  /** List of advanced features (e.g., 'interrupting', 'overlapping') */
  advancedFeatures: string[]
  /** Additional notes about this provider's capabilities */
  notes?: string
}

/**
 * Timing information for a single turn.
 */
export interface TurnTiming {
  /** Index of the turn */
  turnIndex: number
  /** Start time in milliseconds */
  startMs: number
  /** End time in milliseconds */
  endMs: number
}

/**
 * Request for multi-role TTS synthesis.
 */
export interface MultiRoleTTSRequest {
  /** TTS provider to use */
  provider: MultiRoleTTSProvider
  /** List of dialogue turns to synthesize */
  turns: DialogueTurn[]
  /** Voice assignment for each speaker */
  voiceAssignments: VoiceAssignment[]
  /** Language code for synthesis */
  language?: string
  /** Output audio format */
  outputFormat?: 'mp3' | 'wav' | 'opus'
  /** Gap between turns in milliseconds (for segmented mode) */
  gapMs?: number
  /** Crossfade duration in milliseconds (for segmented mode) */
  crossfadeMs?: number
}

/**
 * Result of multi-role TTS synthesis.
 */
export interface MultiRoleTTSResult {
  /** URL to access the synthesized audio */
  audioUrl?: string
  /** Base64 encoded audio content */
  audioContent?: string
  /** MIME type (e.g., 'audio/mpeg') */
  contentType: string
  /** Total audio duration in milliseconds */
  durationMs: number
  /** Total processing latency in milliseconds */
  latencyMs: number
  /** Provider used for synthesis */
  provider: string
  /** Whether native or segmented mode was used */
  synthesisMode: MultiRoleSupportType
  /** Optional timing information for each turn */
  turnTimings?: TurnTiming[]
  /** Path where audio was stored (if applicable) */
  storagePath?: string
}

/**
 * Response from the parse dialogue endpoint.
 */
export interface ParseDialogueResponse {
  /** Parsed dialogue turns */
  turns: DialogueTurn[]
  /** Unique speaker identifiers found */
  speakers: string[]
  /** Total character count */
  totalCharacters: number
}

/**
 * Response from the capabilities endpoint.
 */
export interface CapabilitiesResponse {
  /** All provider capabilities */
  providers: ProviderMultiRoleCapability[]
}

/**
 * Error response from multi-role TTS API.
 */
export interface MultiRoleTTSError {
  /** Error code */
  code: string
  /** Human-readable error message */
  message: string
  /** Additional error details */
  details?: Record<string, unknown>
}
