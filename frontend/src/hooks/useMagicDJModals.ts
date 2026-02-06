/**
 * Magic DJ Modals Hook
 * Feature: 010-magic-dj-controller
 *
 * Encapsulates all modal state management for MagicDJPage:
 * - Track Editor (add/edit/save/close)
 * - BGM Generator (open/save/close)
 * - Prompt Template Editor (add/edit/save/close/delete)
 */

import { useCallback, useState } from 'react'

import { useMagicDJStore } from '@/stores/magicDJStore'
import { blobToBase64DataUrl } from '@/lib/audioUtils'
import type { PromptTemplate, PromptTemplateColor, Track } from '@/types/magic-dj'

interface ConfirmOptions {
  title: string
  message: string
  confirmLabel?: string
}

interface UseMagicDJModalsOptions {
  loadTrack: (track: Track) => Promise<void>
  showNotification: (message: string, durationMs?: number, severity?: 'info' | 'warning' | 'error') => void
  confirm: (options: ConfirmOptions) => Promise<boolean>
}

export function useMagicDJModals({ loadTrack, showNotification, confirm }: UseMagicDJModalsOptions) {
  // Track Editor Modal state
  const [isEditorOpen, setIsEditorOpen] = useState(false)
  const [editingTrack, setEditingTrack] = useState<Track | null>(null)

  // BGM Generator Modal state
  const [isBGMGeneratorOpen, setIsBGMGeneratorOpen] = useState(false)

  // Prompt Template Editor Modal state (015)
  const [isPromptEditorOpen, setIsPromptEditorOpen] = useState(false)
  const [editingPromptTemplate, setEditingPromptTemplate] = useState<PromptTemplate | null>(null)

  // Store actions
  const addTrack = useMagicDJStore(s => s.addTrack)
  const updateTrack = useMagicDJStore(s => s.updateTrack)
  const saveAudioToStorage = useMagicDJStore(s => s.saveAudioToStorage)
  const addPromptTemplate = useMagicDJStore(s => s.addPromptTemplate)
  const updatePromptTemplate = useMagicDJStore(s => s.updatePromptTemplate)
  const removePromptTemplate = useMagicDJStore(s => s.removePromptTemplate)

  // === Track Editor Handlers ===

  const handleAddTrack = useCallback(() => {
    setEditingTrack(null)
    setIsEditorOpen(true)
  }, [])

  const handleEditTrack = useCallback((track: Track) => {
    setEditingTrack(track)
    setIsEditorOpen(true)
  }, [])

  const handleSaveTrack = useCallback(
    async (track: Track, audioBlob: Blob) => {
      try {
        if (editingTrack?.url?.startsWith('blob:')) {
          URL.revokeObjectURL(editingTrack.url)
        }

        const blobUrl = URL.createObjectURL(audioBlob)
        const audioBase64 = await blobToBase64DataUrl(audioBlob)
        await saveAudioToStorage(track.id, audioBlob)

        if (editingTrack) {
          updateTrack(track.id, {
            ...track,
            url: blobUrl,
            isCustom: true,
            audioBase64,
            hasLocalAudio: true,
          })
          await loadTrack({
            ...track,
            url: blobUrl,
            isCustom: true,
            audioBase64,
            hasLocalAudio: true,
          })
        } else {
          const newTrack: Track = {
            ...track,
            url: blobUrl,
            isCustom: true,
            audioBase64,
            hasLocalAudio: true,
          }
          addTrack(newTrack)
          await loadTrack(newTrack)
        }
      } catch (err) {
        console.error('Failed to save track:', err)
        showNotification('儲存音軌失敗，請重試', 3000, 'error')
      }
    },
    [editingTrack, updateTrack, addTrack, loadTrack, saveAudioToStorage, showNotification]
  )

  const handleCloseEditor = useCallback(() => {
    setIsEditorOpen(false)
    setEditingTrack(null)
  }, [])

  // === BGM Generator Handlers ===

  const handleOpenBGMGenerator = useCallback(() => {
    setIsBGMGeneratorOpen(true)
  }, [])

  const handleCloseBGMGenerator = useCallback(() => {
    setIsBGMGeneratorOpen(false)
  }, [])

  const handleSaveBGMTrack = useCallback(
    async (track: Track, audioBlob: Blob) => {
      try {
        const tracks = useMagicDJStore.getState().tracks
        const existingTrack = tracks.find((t) => t.id === track.id)
        if (existingTrack?.url?.startsWith('blob:')) {
          URL.revokeObjectURL(existingTrack.url)
        }

        const blobUrl = URL.createObjectURL(audioBlob)
        const audioBase64 = await blobToBase64DataUrl(audioBlob)
        await saveAudioToStorage(track.id, audioBlob)

        const newTrack: Track = {
          ...track,
          url: blobUrl,
          isCustom: true,
          audioBase64,
        }
        addTrack(newTrack)
        updateTrack(track.id, { hasLocalAudio: true })
        await loadTrack(newTrack)
      } catch (err) {
        console.error('Failed to save BGM track:', err)
        showNotification('儲存背景音樂失敗，請重試', 3000, 'error')
      }
    },
    [addTrack, loadTrack, saveAudioToStorage, updateTrack, showNotification]
  )

  // === Prompt Template Handlers (015) ===

  const handleAddPromptTemplate = useCallback(() => {
    setEditingPromptTemplate(null)
    setIsPromptEditorOpen(true)
  }, [])

  const handleEditPromptTemplate = useCallback((template: PromptTemplate) => {
    setEditingPromptTemplate(template)
    setIsPromptEditorOpen(true)
  }, [])

  const handleDeletePromptTemplate = useCallback(
    async (template: PromptTemplate) => {
      if (template.isDefault) return
      const confirmed = await confirm({
        title: '刪除提示模板',
        message: `確定要刪除「${template.name}」嗎？`,
        confirmLabel: '刪除',
      })
      if (confirmed) {
        removePromptTemplate(template.id)
      }
    },
    [removePromptTemplate, confirm]
  )

  const handleSavePromptTemplate = useCallback(
    (data: { name: string; prompt: string; color: PromptTemplateColor }) => {
      if (editingPromptTemplate) {
        updatePromptTemplate(editingPromptTemplate.id, data)
      } else {
        addPromptTemplate({
          name: data.name,
          prompt: data.prompt,
          color: data.color,
          order: useMagicDJStore.getState().promptTemplates.length + 1,
          isDefault: false,
        })
      }
    },
    [editingPromptTemplate, updatePromptTemplate, addPromptTemplate]
  )

  const handleClosePromptEditor = useCallback(() => {
    setIsPromptEditorOpen(false)
    setEditingPromptTemplate(null)
  }, [])

  return {
    // Track Editor
    isEditorOpen,
    editingTrack,
    handleAddTrack,
    handleEditTrack,
    handleSaveTrack,
    handleCloseEditor,

    // BGM Generator
    isBGMGeneratorOpen,
    handleOpenBGMGenerator,
    handleCloseBGMGenerator,
    handleSaveBGMTrack,

    // Prompt Template Editor
    isPromptEditorOpen,
    editingPromptTemplate,
    handleAddPromptTemplate,
    handleEditPromptTemplate,
    handleDeletePromptTemplate,
    handleSavePromptTemplate,
    handleClosePromptEditor,
  }
}
