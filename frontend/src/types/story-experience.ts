/**
 * Story Experience Types
 * Feature: 016-story-experience-mvp
 *
 * TypeScript type definitions for the parent story experience interface.
 */

// =============================================================================
// Enums & Constants
// =============================================================================

export type ContentType = 'story' | 'song'

export type StoryExperienceStep = 'input' | 'preview' | 'tts'

export const VALUES_OPTIONS = [
  '勇氣', '善良', '分享', '誠實', '尊重', '感恩', '合作', '耐心',
] as const

export const EMOTIONS_OPTIONS = [
  '快樂', '悲傷', '憤怒', '恐懼', '驚訝', '同理心',
] as const

// =============================================================================
// Request / Response Types
// =============================================================================

export interface GenerateContentRequest {
  age: number
  educational_content: string
  values: string[]
  emotions: string[]
  favorite_character: string
  content_type: ContentType
}

export interface GenerateContentResponse {
  content_id: string
  content_type: ContentType
  text_content: string
  parameters_summary: {
    age: number
    educational_content: string
    values: string[]
    emotions: string[]
    favorite_character: string
  }
}

export interface BranchRequest {
  content_id: string
  story_context: string
  selected_branch?: string
}

export interface BranchOption {
  id: string
  description: string
}

export interface BranchResponse {
  branches?: BranchOption[]
  content_id?: string
  text_content?: string
}

export interface QARequest {
  content_id: string
  story_context: string
  question?: string
}

export interface QAQuestion {
  id: string
  text: string
}

export interface QAResponse {
  questions?: QAQuestion[]
  question?: string
  answer?: string
}

export interface TTSGenerateRequest {
  text_content: string
  voice_id: string
}

export interface TTSGenerateResponse {
  audio_content: string  // base64 encoded
  content_type: string
  duration_ms: number
}

export interface VoiceOption {
  id: string
  name: string
  language: string
  gender?: string
}

// =============================================================================
// Form State
// =============================================================================

export interface StoryFormData {
  age: number | null
  educational_content: string
  values: string[]
  emotions: string[]
  favorite_character: string
  content_type: ContentType
}

export const DEFAULT_FORM_DATA: StoryFormData = {
  age: null,
  educational_content: '',
  values: [],
  emotions: [],
  favorite_character: '',
  content_type: 'story',
}

// =============================================================================
// Store State
// =============================================================================

export interface StoryExperienceState {
  // Step management
  currentStep: StoryExperienceStep

  // Form data
  formData: StoryFormData

  // Generated content
  generatedContent: GenerateContentResponse | null
  editedContent: string  // content after user edits in textarea

  // TTS
  voices: VoiceOption[]
  selectedVoiceId: string | null
  audioContent: string | null  // base64
  audioDurationMs: number | null

  // Branch
  branches: BranchOption[]
  fullStoryContent: string  // accumulated content with branches

  // QA
  qaQuestions: QAQuestion[]
  qaAnswers: Array<{ question: string; answer: string }>

  // Loading states
  isGenerating: boolean
  isGeneratingTTS: boolean
  isLoadingVoices: boolean
  isGeneratingBranches: boolean
  isGeneratingQA: boolean

  // Error
  error: string | null
}

export const DEFAULT_STORY_EXPERIENCE_STATE: StoryExperienceState = {
  currentStep: 'input',
  formData: { ...DEFAULT_FORM_DATA },
  generatedContent: null,
  editedContent: '',
  voices: [],
  selectedVoiceId: null,
  audioContent: null,
  audioDurationMs: null,
  branches: [],
  fullStoryContent: '',
  qaQuestions: [],
  qaAnswers: [],
  isGenerating: false,
  isGeneratingTTS: false,
  isLoadingVoices: false,
  isGeneratingBranches: false,
  isGeneratingQA: false,
  error: null,
}
