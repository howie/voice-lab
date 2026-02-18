/**
 * Story Experience API Service
 * Feature: 016-story-experience-mvp
 *
 * API calls for parent story experience interface.
 */

import { api } from '@/lib/api'
import type {
  BranchRequest,
  BranchResponse,
  GenerateContentRequest,
  GenerateContentResponse,
  QARequest,
  QAResponse,
  TTSGenerateRequest,
  TTSGenerateResponse,
  VoiceOption,
} from '@/types/story-experience'

// =============================================================================
// Story Experience API
// =============================================================================

export const storyExperienceApi = {
  /**
   * Generate story or song content from parent input parameters
   */
  generateContent: (data: GenerateContentRequest) =>
    api.post<GenerateContentResponse>('/story-experience/generate', data),

  /**
   * Generate story branch options or continue from selected branch
   */
  generateBranch: (data: BranchRequest) =>
    api.post<BranchResponse>('/story-experience/branch', data),

  /**
   * Generate Q&A questions or answer a question based on story context
   */
  generateQA: (data: QARequest) =>
    api.post<QAResponse>('/story-experience/qa', data),

  /**
   * Generate TTS audio from confirmed text content
   */
  generateTTS: (data: TTSGenerateRequest) =>
    api.post<TTSGenerateResponse>('/story-experience/tts', data),

  /**
   * List available Chinese TTS voices
   */
  listVoices: () =>
    api.get<VoiceOption[]>('/story-experience/voices'),
}
