/**
 * StoryPal State Store
 * Feature: StoryPal — AI Interactive Story Companion
 *
 * Zustand store for interactive story session state management.
 */

import { create } from 'zustand'

import * as storypalApi from '@/services/storypalApi'
import type {
  CreateStorySessionRequest,
  SceneChangeData,
  StoryCategory,
  StoryCharacter,
  StorySession,
  StorySessionStatus,
  StorySegmentData,
  StoryTemplate,
  StoryTurn,
  StoryWSMessage,
  ChoicePromptData,
} from '@/types/storypal'

// =============================================================================
// State Interface
// =============================================================================

type StoryPlayState = 'idle' | 'loading' | 'playing' | 'waiting_choice' | 'listening' | 'paused' | 'ended'

interface StoryPalStoreState {
  // Templates
  templates: StoryTemplate[]
  selectedTemplate: StoryTemplate | null
  isLoadingTemplates: boolean

  // Session
  session: StorySession | null
  sessions: StorySession[]
  isLoadingSessions: boolean

  // Playback state
  playState: StoryPlayState
  turns: StoryTurn[]
  currentSegment: StorySegmentData | null

  // Scene & BGM
  currentScene: SceneChangeData | null
  bgmPlaying: boolean

  // Choice
  currentChoice: ChoicePromptData | null

  // Characters
  characters: StoryCharacter[]
  speakingCharacter: string | null

  // WebSocket
  ws: WebSocket | null
  isConnected: boolean

  // Settings
  language: string
  categoryFilter: StoryCategory | null

  // Error
  error: string | null
  isLoading: boolean

  // === Template Actions ===
  fetchTemplates: (params?: { category?: string; language?: string }) => Promise<void>
  selectTemplate: (template: StoryTemplate | null) => void

  // === Session Actions ===
  fetchSessions: (params?: { status?: StorySessionStatus }) => Promise<void>
  createSession: (request: CreateStorySessionRequest) => Promise<StorySession | null>
  loadSession: (sessionId: string) => Promise<void>
  deleteSession: (sessionId: string) => Promise<void>

  // === WebSocket Actions ===
  connectWS: () => void
  disconnectWS: () => void
  sendStoryConfig: (config: {
    template_id?: string
    language: string
    characters_config?: StoryCharacter[]
  }) => void
  sendChoice: (choice: string) => void
  sendAudioChunk: (data: string) => void
  sendTextInput: (text: string) => void
  sendInterrupt: () => void

  // === Playback Actions ===
  setPlayState: (state: StoryPlayState) => void
  addTurn: (turn: StoryTurn) => void
  setCurrentSegment: (segment: StorySegmentData | null) => void
  setCurrentChoice: (choice: ChoicePromptData | null) => void
  setCurrentScene: (scene: SceneChangeData | null) => void
  setSpeakingCharacter: (name: string | null) => void
  setBgmPlaying: (playing: boolean) => void

  // === Settings Actions ===
  setLanguage: (language: string) => void
  setCategoryFilter: (category: StoryCategory | null) => void

  // === General Actions ===
  clearError: () => void
  reset: () => void
}

// =============================================================================
// Store Implementation
// =============================================================================

export const useStoryPalStore = create<StoryPalStoreState>((set, get) => ({
  // Initial state
  templates: [],
  selectedTemplate: null,
  isLoadingTemplates: false,
  session: null,
  sessions: [],
  isLoadingSessions: false,
  playState: 'idle',
  turns: [],
  currentSegment: null,
  currentScene: null,
  bgmPlaying: false,
  currentChoice: null,
  characters: [],
  speakingCharacter: null,
  ws: null,
  isConnected: false,
  language: 'zh-TW',
  categoryFilter: null,
  error: null,
  isLoading: false,

  // === Template Actions ===
  fetchTemplates: async (params) => {
    set({ isLoadingTemplates: true, error: null })
    try {
      const response = await storypalApi.listTemplates(params)
      set({ templates: response.templates, isLoadingTemplates: false })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '載入故事範本失敗', isLoadingTemplates: false })
    }
  },

  selectTemplate: (template) => {
    set({
      selectedTemplate: template,
      characters: template?.characters ?? [],
    })
  },

  // === Session Actions ===
  fetchSessions: async (params) => {
    set({ isLoadingSessions: true, error: null })
    try {
      const response = await storypalApi.listSessions(params)
      set({ sessions: response.sessions, isLoadingSessions: false })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '載入故事列表失敗', isLoadingSessions: false })
    }
  },

  createSession: async (request) => {
    set({ isLoading: true, error: null })
    try {
      const response = await storypalApi.createSession(request)
      set({
        session: response,
        turns: response.turns ?? [],
        characters: response.characters_config ?? [],
        playState: 'loading',
        isLoading: false,
      })
      return response
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '建立故事失敗', isLoading: false })
      return null
    }
  },

  loadSession: async (sessionId) => {
    set({ isLoading: true, error: null })
    try {
      const response = await storypalApi.getSession(sessionId)
      set({
        session: response,
        turns: response.turns ?? [],
        characters: response.characters_config ?? [],
        playState: response.status === 'completed' ? 'ended' : 'paused',
        isLoading: false,
      })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '載入故事失敗', isLoading: false })
    }
  },

  deleteSession: async (sessionId) => {
    try {
      await storypalApi.deleteSession(sessionId)
      const { sessions } = get()
      set({ sessions: sessions.filter((s) => s.id !== sessionId) })
      if (get().session?.id === sessionId) {
        set({ session: null, turns: [], playState: 'idle' })
      }
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '刪除故事失敗' })
    }
  },

  // === WebSocket Actions ===
  connectWS: () => {
    const { ws } = get()
    if (ws) ws.close()

    const token = localStorage.getItem('auth_token')
    const url = storypalApi.getStoryWSUrl() + (token ? `?token=${token}` : '')
    const socket = new WebSocket(url)

    socket.onopen = () => {
      set({ isConnected: true, error: null })
    }

    socket.onclose = () => {
      set({ isConnected: false, ws: null })
    }

    socket.onerror = () => {
      set({ error: '故事連線失敗', isConnected: false })
    }

    socket.onmessage = (event) => {
      try {
        const msg: StoryWSMessage = JSON.parse(event.data)
        handleWSMessage(msg, set, get)
      } catch {
        // Ignore parse errors
      }
    }

    set({ ws: socket })
  },

  disconnectWS: () => {
    const { ws } = get()
    if (ws) {
      ws.close()
      set({ ws: null, isConnected: false })
    }
  },

  sendStoryConfig: (config) => {
    const { ws } = get()
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'story_configure', data: config }))
      set({ playState: 'loading' })
    }
  },

  sendChoice: (choice) => {
    const { ws } = get()
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'story_choice', data: { choice } }))
      set({ currentChoice: null, playState: 'loading' })
    }
  },

  sendAudioChunk: (data) => {
    const { ws } = get()
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'audio_chunk', data: { audio: data } }))
    }
  },

  sendTextInput: (text) => {
    const { ws } = get()
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'text_input', data: { text } }))
      set({ playState: 'loading' })
    }
  },

  sendInterrupt: () => {
    const { ws } = get()
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'interrupt', data: {} }))
    }
  },

  // === Playback Actions ===
  setPlayState: (state) => set({ playState: state }),
  addTurn: (turn) => set((s) => ({ turns: [...s.turns, turn] })),
  setCurrentSegment: (segment) => set({ currentSegment: segment }),
  setCurrentChoice: (choice) => set({ currentChoice: choice, playState: choice ? 'waiting_choice' : get().playState }),
  setCurrentScene: (scene) => set({ currentScene: scene }),
  setSpeakingCharacter: (name) => set({ speakingCharacter: name }),
  setBgmPlaying: (playing) => set({ bgmPlaying: playing }),

  // === Settings Actions ===
  setLanguage: (language) => set({ language }),
  setCategoryFilter: (category) => set({ categoryFilter: category }),

  // === General Actions ===
  clearError: () => set({ error: null }),
  reset: () => {
    const { ws } = get()
    if (ws) ws.close()
    set({
      session: null,
      turns: [],
      playState: 'idle',
      currentSegment: null,
      currentScene: null,
      currentChoice: null,
      speakingCharacter: null,
      bgmPlaying: false,
      ws: null,
      isConnected: false,
      error: null,
    })
  },
}))

// =============================================================================
// WebSocket Message Handler
// =============================================================================

type SetFn = (partial: Partial<StoryPalStoreState> | ((state: StoryPalStoreState) => Partial<StoryPalStoreState>)) => void
type GetFn = () => StoryPalStoreState

function handleWSMessage(msg: StoryWSMessage, set: SetFn, _get: GetFn) {
  switch (msg.type) {
    case 'story_segment': {
      const segment = msg.data as unknown as StorySegmentData
      set({
        currentSegment: segment,
        playState: 'playing',
        speakingCharacter: segment.character_name,
      })
      break
    }

    case 'choice_prompt': {
      const choice = msg.data as unknown as ChoicePromptData
      set({ currentChoice: choice, playState: 'waiting_choice' })
      break
    }

    case 'scene_change': {
      const scene = msg.data as unknown as SceneChangeData
      set({ currentScene: scene })
      break
    }

    case 'audio': {
      // Audio chunk handled by audio playback hook
      break
    }

    case 'story_end': {
      set({ playState: 'ended' })
      break
    }

    case 'error': {
      const errorMsg = (msg.data as { message?: string }).message ?? '故事發生錯誤'
      set({ error: errorMsg })
      break
    }
  }
}
