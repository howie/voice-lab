/**
 * STT (Speech-to-Text) TypeScript types for the STT Testing Module.
 * Feature: 003-stt-testing-module
 */

// Provider types
export type STTProviderName = 'azure' | 'gcp' | 'whisper'

export interface STTProvider {
  name: STTProviderName
  display_name: string
  supports_streaming: boolean
  supports_child_mode: boolean
  max_duration_sec: number
  max_file_size_mb: number
  supported_formats: AudioFormat[]
  supported_languages: string[]
  /** Whether the user has configured credentials for this provider */
  has_credentials?: boolean
  /** Whether the configured credentials are valid */
  is_valid?: boolean
}

// Audio types
export type AudioFormat = 'mp3' | 'wav' | 'm4a' | 'flac' | 'webm' | 'ogg'

export interface AudioFile {
  id: string
  filename: string
  format: AudioFormat
  duration_ms: number
  sample_rate: number
  file_size_bytes: number
  source: 'upload' | 'recording'
  created_at: string
}

// Request types
export interface STTTranscribeRequest {
  provider: STTProviderName
  language: string
  child_mode?: boolean
  ground_truth?: string
}

// Response types
export interface WordTiming {
  word: string
  start_ms: number
  end_ms: number
  confidence?: number
}

export interface WERAnalysis {
  error_rate: number
  error_type: 'WER' | 'CER'
  insertions: number
  deletions: number
  substitutions: number
  total_reference: number
  alignment?: AlignmentItem[]
}

export interface AlignmentItem {
  ref: string | null
  hyp: string | null
  op: 'match' | 'substitute' | 'insert' | 'delete'
}

export interface TranscriptionResponse {
  id: string
  provider: STTProviderName
  transcript: string
  confidence: number | null
  latency_ms: number
  language: string
  words?: WordTiming[]
  wer_analysis?: WERAnalysis
  audio_duration_ms?: number
  created_at: string
}

// History types
export interface TranscriptionSummary {
  id: string
  provider: STTProviderName
  language: string
  transcript_preview: string
  duration_ms?: number
  confidence: number | null
  has_ground_truth: boolean
  error_rate?: number
  created_at: string
}

export interface TranscriptionHistoryPage {
  items: TranscriptionSummary[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface TranscriptionDetail extends TranscriptionResponse {
  audio_file?: {
    id: string
    filename: string
    duration_ms: number
    format: AudioFormat
    download_url: string
  }
  ground_truth?: string
  child_mode: boolean
}

// Comparison types
export interface ComparisonResult {
  provider: STTProviderName
  transcript: string
  confidence: number | null
  latency_ms: number
  error_rate?: number
  error_type?: 'WER' | 'CER'
}

export interface ComparisonResponse {
  audio_file_id: string
  results: TranscriptionResponse[]
  ground_truth?: string
  comparison_table: ComparisonResult[]
}

// UI State types
export interface STTTestState {
  // Audio input
  audioFile: File | null
  audioBlob: Blob | null
  audioUrl: string | null
  isRecording: boolean

  // Provider selection
  selectedProvider: STTProviderName
  availableProviders: STTProvider[]

  // Options
  language: string
  childMode: boolean
  groundTruth: string

  // Results
  isTranscribing: boolean
  transcriptionResult: TranscriptionResponse | null
  werAnalysis: WERAnalysis | null
  error: string | null

  // Comparison
  comparisonProviders: STTProviderName[]
  comparisonResults: ComparisonResponse | null
  isComparing: boolean
}

// Error types
export interface STTError {
  error: string
  detail: string
  code: 'INVALID_FORMAT' | 'FILE_TOO_LARGE' | 'PROVIDER_ERROR' | 'QUOTA_EXCEEDED'
}

// Supported languages
export const SUPPORTED_LANGUAGES = [
  { code: 'zh-TW', name: '繁體中文 (台灣)', errorType: 'CER' },
  { code: 'zh-CN', name: '簡體中文', errorType: 'CER' },
  { code: 'en-US', name: 'English (US)', errorType: 'WER' },
  { code: 'ja-JP', name: '日本語', errorType: 'CER' },
  { code: 'ko-KR', name: '한국어', errorType: 'CER' },
] as const

export type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number]['code']
