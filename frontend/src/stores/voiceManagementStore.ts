/**
 * Voice Management Store
 *
 * Feature: 013-tts-role-mgmt
 * T010: Zustand store for voice management page state
 */

import { create } from 'zustand'
import { voiceCustomizationApi } from '@/lib/voiceCustomizationApi'
import type {
  VoiceWithCustomization,
  VoiceFilterParams,
  BulkUpdateItem,
} from '@/types/voice-customization'

interface VoiceManagementState {
  // Voice list
  voices: VoiceWithCustomization[]
  total: number
  isLoading: boolean
  error: string | null

  // Filters
  filters: VoiceFilterParams

  // Pagination
  page: number
  pageSize: number

  // Selection (for bulk operations)
  selectedVoiceIds: Set<string>

  // Actions - Filters
  setFilter: <K extends keyof VoiceFilterParams>(key: K, value: VoiceFilterParams[K]) => void
  resetFilters: () => void
  setPage: (page: number) => void
  setPageSize: (pageSize: number) => void

  // Actions - Data
  loadVoices: () => Promise<void>
  refreshVoice: (voiceCacheId: string) => void

  // Actions - Customization
  updateCustomName: (voiceCacheId: string, customName: string | null) => Promise<void>
  toggleFavorite: (voiceCacheId: string) => Promise<void>
  toggleHidden: (voiceCacheId: string) => Promise<void>
  bulkUpdate: (updates: BulkUpdateItem[]) => Promise<void>
  resetCustomization: (voiceCacheId: string) => Promise<void>

  // Actions - Selection
  toggleSelection: (voiceCacheId: string) => void
  selectAll: () => void
  clearSelection: () => void

  // Actions - Preview
  updatePreviewUrl: (voiceCacheId: string, previewUrl: string) => void

  // Actions - Helpers
  getVoiceById: (voiceCacheId: string) => VoiceWithCustomization | undefined
}

const DEFAULT_FILTERS: VoiceFilterParams = {
  excludeHidden: false, // Show all in management page
  favoritesOnly: false,
}

const DEFAULT_PAGE_SIZE = 50

export const useVoiceManagementStore = create<VoiceManagementState>((set, get) => ({
  // Initial state
  voices: [],
  total: 0,
  isLoading: false,
  error: null,
  filters: { ...DEFAULT_FILTERS },
  page: 1,
  pageSize: DEFAULT_PAGE_SIZE,
  selectedVoiceIds: new Set(),

  // Filter actions
  setFilter: (key, value) => {
    set((state) => ({
      filters: { ...state.filters, [key]: value },
      page: 1, // Reset to first page on filter change
    }))
    // Auto-reload on filter change
    get().loadVoices()
  },

  resetFilters: () => {
    set({
      filters: { ...DEFAULT_FILTERS },
      page: 1,
    })
    get().loadVoices()
  },

  setPage: (page) => {
    set({ page })
    get().loadVoices()
  },

  setPageSize: (pageSize) => {
    set({ pageSize, page: 1 })
    get().loadVoices()
  },

  // Data actions
  loadVoices: async () => {
    const { filters, page, pageSize } = get()
    set({ isLoading: true, error: null })

    try {
      const response = await voiceCustomizationApi.listVoicesWithCustomizations({
        ...filters,
        limit: pageSize,
        offset: (page - 1) * pageSize,
      })

      set({
        voices: response.items,
        total: response.total,
        isLoading: false,
      })
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : '載入角色列表失敗'
      set({ error: message, isLoading: false })
    }
  },

  refreshVoice: (voiceCacheId) => {
    // Update a single voice in the list without full reload
    // This is called after individual updates
    const { voices } = get()
    const voiceIndex = voices.findIndex((v) => v.id === voiceCacheId)
    if (voiceIndex === -1) return

    // For now, just trigger a full reload
    // In the future, we could optimize this to only fetch the single voice
    get().loadVoices()
  },

  // Customization actions
  updateCustomName: async (voiceCacheId, customName) => {
    const { voices } = get()
    const voiceIndex = voices.findIndex((v) => v.id === voiceCacheId)
    if (voiceIndex === -1) return

    // Optimistic update
    const updatedVoices = [...voices]
    const voice = { ...updatedVoices[voiceIndex] }
    voice.displayName = customName || voice.displayName
    if (voice.customization) {
      voice.customization = { ...voice.customization, customName }
    }
    updatedVoices[voiceIndex] = voice
    set({ voices: updatedVoices })

    try {
      await voiceCustomizationApi.updateCustomName(voiceCacheId, customName)
      // Refresh to get server state
      get().loadVoices()
    } catch (error: unknown) {
      // Revert on error
      get().loadVoices()
      const message = error instanceof Error ? error.message : '更新名稱失敗'
      set({ error: message })
    }
  },

  toggleFavorite: async (voiceCacheId) => {
    const { voices } = get()
    const voice = voices.find((v) => v.id === voiceCacheId)
    if (!voice) return

    const newFavoriteState = !voice.isFavorite

    // Optimistic update
    const updatedVoices = voices.map((v) =>
      v.id === voiceCacheId ? { ...v, isFavorite: newFavoriteState } : v
    )
    set({ voices: updatedVoices })

    try {
      await voiceCustomizationApi.toggleFavorite(voiceCacheId, newFavoriteState)
    } catch (error: unknown) {
      // Revert on error
      get().loadVoices()
      const message = error instanceof Error ? error.message : '切換收藏狀態失敗'
      set({ error: message })
    }
  },

  toggleHidden: async (voiceCacheId) => {
    const { voices } = get()
    const voice = voices.find((v) => v.id === voiceCacheId)
    if (!voice) return

    const newHiddenState = !voice.isHidden

    // Optimistic update
    // Note: If hiding, also unfavorite (business rule)
    const updatedVoices = voices.map((v) =>
      v.id === voiceCacheId
        ? {
            ...v,
            isHidden: newHiddenState,
            isFavorite: newHiddenState ? false : v.isFavorite,
          }
        : v
    )
    set({ voices: updatedVoices })

    try {
      await voiceCustomizationApi.toggleHidden(voiceCacheId, newHiddenState)
    } catch (error: unknown) {
      // Revert on error
      get().loadVoices()
      const message = error instanceof Error ? error.message : '切換隱藏狀態失敗'
      set({ error: message })
    }
  },

  bulkUpdate: async (updates) => {
    set({ isLoading: true, error: null })

    try {
      const result = await voiceCustomizationApi.bulkUpdate({ updates })

      if (result.failed.length > 0) {
        const failedIds = result.failed.map((f) => f.voiceCacheId).join(', ')
        set({ error: `部分更新失敗: ${failedIds}` })
      }

      // Clear selection and reload
      set({ selectedVoiceIds: new Set() })
      await get().loadVoices()
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : '批量更新失敗'
      set({ error: message, isLoading: false })
    }
  },

  resetCustomization: async (voiceCacheId) => {
    try {
      await voiceCustomizationApi.deleteCustomization(voiceCacheId)
      get().loadVoices()
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : '重設失敗'
      set({ error: message })
    }
  },

  // Selection actions
  toggleSelection: (voiceCacheId) => {
    set((state) => {
      const newSelection = new Set(state.selectedVoiceIds)
      if (newSelection.has(voiceCacheId)) {
        newSelection.delete(voiceCacheId)
      } else {
        newSelection.add(voiceCacheId)
      }
      return { selectedVoiceIds: newSelection }
    })
  },

  selectAll: () => {
    const { voices } = get()
    set({ selectedVoiceIds: new Set(voices.map((v) => v.id)) })
  },

  clearSelection: () => {
    set({ selectedVoiceIds: new Set() })
  },

  // Preview actions
  updatePreviewUrl: (voiceCacheId, previewUrl) => {
    const { voices } = get()
    set({
      voices: voices.map((v) =>
        v.id === voiceCacheId ? { ...v, sampleAudioUrl: previewUrl } : v
      ),
    })
  },

  // Helper actions
  getVoiceById: (voiceCacheId) => {
    return get().voices.find((v) => v.id === voiceCacheId)
  },
}))
