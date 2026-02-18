/**
 * Story Experience Store
 * Feature: 016-story-experience-mvp
 *
 * Zustand store for parent story experience state management.
 */

import { create } from 'zustand'

import { storyExperienceApi } from '@/services/storyExperienceApi'
import type {
  StoryExperienceState,
  StoryExperienceStep,
  StoryFormData,
} from '@/types/story-experience'
import { DEFAULT_FORM_DATA, DEFAULT_STORY_EXPERIENCE_STATE } from '@/types/story-experience'

// =============================================================================
// Store Interface
// =============================================================================

interface StoryExperienceStoreActions {
  // Step management
  setStep: (step: StoryExperienceStep) => void

  // Form actions
  setFormData: (data: Partial<StoryFormData>) => void
  resetForm: () => void

  // Content generation
  generateContent: () => Promise<void>
  regenerateContent: () => Promise<void>
  confirmContent: () => void
  setEditedContent: (content: string) => void

  // TTS
  fetchVoices: () => Promise<void>
  setSelectedVoice: (voiceId: string) => void
  generateTTS: () => Promise<void>

  // Branch
  generateBranches: () => Promise<void>
  selectBranch: (branchId: string) => Promise<void>

  // QA
  generateQuestions: () => Promise<void>
  askQuestion: (question: string) => Promise<void>
  generateQAAudio: (text: string) => Promise<void>

  // Reset
  reset: () => void
  clearError: () => void
}

type StoryExperienceStore = StoryExperienceState & StoryExperienceStoreActions

// =============================================================================
// Store Implementation
// =============================================================================

export const useStoryExperienceStore = create<StoryExperienceStore>((set, get) => ({
  ...DEFAULT_STORY_EXPERIENCE_STATE,

  // === Step Management ===

  setStep: (step) => set({ currentStep: step }),

  // === Form Actions ===

  setFormData: (data) =>
    set((state) => ({
      formData: { ...state.formData, ...data },
    })),

  resetForm: () => set({ formData: { ...DEFAULT_FORM_DATA } }),

  // === Content Generation ===

  generateContent: async () => {
    const { formData } = get()
    if (!formData.age) return

    set({ isGenerating: true, error: null })
    try {
      const response = await storyExperienceApi.generateContent({
        age: formData.age,
        educational_content: formData.educational_content,
        values: formData.values,
        emotions: formData.emotions,
        favorite_character: formData.favorite_character,
        content_type: formData.content_type,
      })
      const content = response.data
      set({
        generatedContent: content,
        editedContent: content.text_content,
        fullStoryContent: content.text_content,
        currentStep: 'preview',
        isGenerating: false,
        // Reset branch/QA state on new generation
        branches: [],
        qaQuestions: [],
        qaAnswers: [],
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : '內容生成失敗，請重試'
      set({ isGenerating: false, error: message })
    }
  },

  regenerateContent: async () => {
    // Same as generateContent - uses current formData
    await get().generateContent()
  },

  confirmContent: () => {
    const { editedContent, fullStoryContent } = get()
    // Update fullStoryContent with any edits the user made
    set({
      fullStoryContent: editedContent || fullStoryContent,
      currentStep: 'tts',
    })
  },

  setEditedContent: (content) => set({ editedContent: content }),

  // === TTS ===

  fetchVoices: async () => {
    set({ isLoadingVoices: true })
    try {
      const response = await storyExperienceApi.listVoices()
      const voices = response.data
      set({
        voices,
        selectedVoiceId: voices.length > 0 ? voices[0].id : null,
        isLoadingVoices: false,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : '載入語音列表失敗'
      set({ isLoadingVoices: false, error: message })
    }
  },

  setSelectedVoice: (voiceId) => set({ selectedVoiceId: voiceId }),

  generateTTS: async () => {
    const { fullStoryContent, editedContent, selectedVoiceId } = get()
    if (!selectedVoiceId) return

    const textContent = editedContent || fullStoryContent
    if (!textContent) return

    set({ isGeneratingTTS: true, error: null, audioContent: null })
    try {
      const response = await storyExperienceApi.generateTTS({
        text_content: textContent,
        voice_id: selectedVoiceId,
      })
      set({
        audioContent: response.data.audio_content,
        audioDurationMs: response.data.duration_ms,
        isGeneratingTTS: false,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'TTS 音頻生成失敗，請重試'
      set({ isGeneratingTTS: false, error: message })
    }
  },

  // === Branch ===

  generateBranches: async () => {
    const { generatedContent, fullStoryContent } = get()
    if (!generatedContent) return

    set({ isGeneratingBranches: true, error: null })
    try {
      const response = await storyExperienceApi.generateBranch({
        content_id: generatedContent.content_id,
        story_context: fullStoryContent,
      })
      set({
        branches: response.data.branches || [],
        isGeneratingBranches: false,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : '故事走向生成失敗'
      set({ isGeneratingBranches: false, error: message })
    }
  },

  selectBranch: async (branchId) => {
    const { generatedContent, fullStoryContent } = get()
    if (!generatedContent) return

    set({ isGeneratingBranches: true, error: null })
    try {
      const response = await storyExperienceApi.generateBranch({
        content_id: generatedContent.content_id,
        story_context: fullStoryContent,
        selected_branch: branchId,
      })
      if (response.data.text_content) {
        const updatedContent = fullStoryContent + '\n\n' + response.data.text_content
        set({
          fullStoryContent: updatedContent,
          editedContent: updatedContent,
          branches: [],
          isGeneratingBranches: false,
        })
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : '故事延伸生成失敗'
      set({ isGeneratingBranches: false, error: message })
    }
  },

  // === QA ===

  generateQuestions: async () => {
    const { generatedContent, fullStoryContent } = get()
    if (!generatedContent) return

    set({ isGeneratingQA: true, error: null })
    try {
      const response = await storyExperienceApi.generateQA({
        content_id: generatedContent.content_id,
        story_context: fullStoryContent,
      })
      set({
        qaQuestions: response.data.questions || [],
        isGeneratingQA: false,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Q&A 問題生成失敗'
      set({ isGeneratingQA: false, error: message })
    }
  },

  askQuestion: async (question) => {
    const { generatedContent, fullStoryContent } = get()
    if (!generatedContent) return

    set({ isGeneratingQA: true, error: null })
    try {
      const response = await storyExperienceApi.generateQA({
        content_id: generatedContent.content_id,
        story_context: fullStoryContent,
        question,
      })
      if (response.data.answer) {
        set((state) => ({
          qaAnswers: [
            ...state.qaAnswers,
            { question, answer: response.data.answer! },
          ],
          isGeneratingQA: false,
        }))
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : '回答生成失敗'
      set({ isGeneratingQA: false, error: message })
    }
  },

  generateQAAudio: async (text) => {
    // Reuse the TTS generation for Q&A text
    const { selectedVoiceId } = get()
    if (!selectedVoiceId) return

    set({ isGeneratingTTS: true, error: null })
    try {
      const response = await storyExperienceApi.generateTTS({
        text_content: text,
        voice_id: selectedVoiceId,
      })
      set({
        audioContent: response.data.audio_content,
        audioDurationMs: response.data.duration_ms,
        isGeneratingTTS: false,
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Q&A 音頻生成失敗'
      set({ isGeneratingTTS: false, error: message })
    }
  },

  // === Reset ===

  reset: () => set({ ...DEFAULT_STORY_EXPERIENCE_STATE }),

  clearError: () => set({ error: null }),
}))
