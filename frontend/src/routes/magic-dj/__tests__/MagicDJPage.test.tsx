/**
 * MagicDJPage Tests
 * Feature: 010-magic-dj-controller
 *
 * Tests: initial loading state, loaded state with DJControlPanel, blob URL cleanup on unmount.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'

import { useMagicDJStore } from '@/stores/magicDJStore'

// ---------------------------------------------------------------------------
// Mocks - child components
// ---------------------------------------------------------------------------

vi.mock('@/components/magic-dj/DJControlPanel', () => ({
  DJControlPanel: () => <div data-testid="dj-control-panel" />,
}))
vi.mock('@/components/magic-dj/TrackEditorModal', () => ({
  TrackEditorModal: () => <div data-testid="track-editor-modal" />,
}))
vi.mock('@/components/magic-dj/BGMGeneratorModal', () => ({
  BGMGeneratorModal: () => <div data-testid="bgm-generator-modal" />,
}))
vi.mock('@/components/magic-dj/PromptTemplateEditor', () => ({
  PromptTemplateEditor: () => <div data-testid="prompt-template-editor" />,
}))
vi.mock('@/components/magic-dj/ConfirmDialog', () => ({
  ConfirmDialog: () => null,
}))

// ---------------------------------------------------------------------------
// Mocks - hooks
// ---------------------------------------------------------------------------

const mockLoadTracks = vi.fn().mockResolvedValue(undefined)
const mockGetLoadingProgress = vi.fn().mockReturnValue(1)

vi.mock('@/hooks/useMultiTrackPlayer', () => ({
  useMultiTrackPlayer: () => ({
    loadTracks: mockLoadTracks,
    loadTrack: vi.fn().mockResolvedValue(undefined),
    playTrack: vi.fn(),
    stopTrack: vi.fn(),
    stopAll: vi.fn(),
    getLoadingProgress: mockGetLoadingProgress,
    unloadTrack: vi.fn(),
    canPlayMore: vi.fn().mockReturnValue(true),
  }),
}))

vi.mock('@/hooks/useMagicDJModals', () => ({
  useMagicDJModals: () => ({
    isEditorOpen: false,
    editingTrack: null,
    handleAddTrack: vi.fn(),
    handleEditTrack: vi.fn(),
    handleSaveTrack: vi.fn(),
    handleCloseEditor: vi.fn(),
    isBGMGeneratorOpen: false,
    handleOpenBGMGenerator: vi.fn(),
    handleCloseBGMGenerator: vi.fn(),
    handleSaveBGMTrack: vi.fn(),
    isPromptEditorOpen: false,
    editingPromptTemplate: null,
    handleAddPromptTemplate: vi.fn(),
    handleEditPromptTemplate: vi.fn(),
    handleDeletePromptTemplate: vi.fn(),
    handleSavePromptTemplate: vi.fn(),
    handleClosePromptEditor: vi.fn(),
  }),
}))

vi.mock('@/hooks/useConfirmDialog', () => ({
  useConfirmDialog: () => ({
    confirm: vi.fn(),
    dialogProps: { open: false, title: '', message: '', onConfirm: vi.fn(), onCancel: vi.fn() },
  }),
}))

vi.mock('@/hooks/useDJHotkeys')

vi.mock('@/hooks/useCueList', () => ({
  useCueList: () => ({
    playNextCue: vi.fn(),
    removeFromCueList: vi.fn(),
    resetCuePosition: vi.fn(),
    clearCueList: vi.fn(),
    advanceCuePosition: vi.fn(),
    currentItem: null,
  }),
}))

vi.mock('@/hooks/useWebSocket', () => ({
  useWebSocket: () => ({
    status: 'disconnected' as const,
    connect: vi.fn(),
    disconnect: vi.fn(),
    sendMessage: vi.fn(),
    sendBinary: vi.fn(),
  }),
}))

vi.mock('@/hooks/useAudioPlayback', () => ({
  useAudioPlayback: () => ({
    isPlaying: false,
    hasQueuedAudio: false,
    volume: 1,
    setVolume: vi.fn(),
    playAudio: vi.fn(),
    queueAudioChunk: vi.fn(),
    stop: vi.fn(),
    clearQueue: vi.fn(),
  }),
}))

vi.mock('@/hooks/useMicrophone', () => ({
  useMicrophone: () => ({
    isRecording: false,
    startRecording: vi.fn(),
    stopRecording: vi.fn(),
  }),
}))

// ---------------------------------------------------------------------------
// Mocks - services & stores
// ---------------------------------------------------------------------------

vi.mock('@/services/interactionApi', () => ({
  buildWebSocketUrl: vi.fn().mockReturnValue('ws://localhost:8000/ws'),
}))

vi.mock('@/stores/authStore', () => ({
  useAuthStore: vi.fn((selector: (s: Record<string, unknown>) => unknown) =>
    selector({ user: { id: 'test-user' } }),
  ),
}))

vi.mock('@/stores/interactionStore', () => ({
  useInteractionStore: vi.fn((selector: (s: Record<string, unknown>) => unknown) =>
    selector({ options: { providerConfig: {}, systemPrompt: '' } }),
  ),
}))

// ---------------------------------------------------------------------------
// Import component AFTER mocks
// ---------------------------------------------------------------------------

import { MagicDJPage } from '../MagicDJPage'

// ---------------------------------------------------------------------------
// Test suite
// ---------------------------------------------------------------------------

describe('MagicDJPage', () => {
  beforeEach(() => {
    vi.useFakeTimers()

    // Reset the real zustand store and stub initializeStorage (which accesses
    // IndexedDB, unavailable in jsdom) to resolve immediately.
    act(() => {
      useMagicDJStore.getState().reset()
      useMagicDJStore.setState({
        isStorageReady: true,
        initializeStorage: vi.fn().mockResolvedValue(undefined),
      })
    })

    // Reset mocks
    mockLoadTracks.mockClear()
    mockGetLoadingProgress.mockClear().mockReturnValue(1)
    vi.mocked(URL.revokeObjectURL).mockClear()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  // -------------------------------------------------------------------------
  // 1. Initial loading state
  // -------------------------------------------------------------------------

  it('shows loading skeleton initially', () => {
    // Make progress < 1 so the loading state persists
    mockGetLoadingProgress.mockReturnValue(0)

    render(<MagicDJPage />)

    // The loading skeleton contains the progress text
    expect(screen.getByText(/載入音軌中/)).toBeInTheDocument()

    // DJControlPanel should NOT be rendered while loading
    expect(screen.queryByTestId('dj-control-panel')).not.toBeInTheDocument()
  })

  // -------------------------------------------------------------------------
  // 2. Loaded state
  // -------------------------------------------------------------------------

  it('shows DJControlPanel after loading completes', async () => {
    mockGetLoadingProgress.mockReturnValue(1)

    render(<MagicDJPage />)

    // Flush the async initAndLoad / loadTracks promises
    await act(async () => {
      await Promise.resolve()
    })

    // Now advance timers so the setInterval fires and detects progress >= 1
    await act(async () => {
      vi.advanceTimersByTime(200)
    })

    expect(screen.getByTestId('dj-control-panel')).toBeInTheDocument()
    expect(screen.queryByText(/載入音軌中/)).not.toBeInTheDocument()
  })

  // -------------------------------------------------------------------------
  // 3. Blob URLs are NOT revoked on unmount (handled by initializeStorage)
  // -------------------------------------------------------------------------

  it('does not revoke blob URLs on unmount (initializeStorage handles cleanup)', async () => {
    mockGetLoadingProgress.mockReturnValue(1)

    // Seed the store with tracks that have blob URLs
    act(() => {
      useMagicDJStore.setState({
        tracks: [
          { id: 'track-1', name: 'Track 1', url: 'blob:http://localhost/aaa', type: 'effect' as const, source: 'tts' as const, volume: 1 },
          { id: 'track-2', name: 'Track 2', url: 'blob:http://localhost/bbb', type: 'effect' as const, source: 'tts' as const, volume: 1 },
          { id: 'track-3', name: 'Track 3', url: '/static/sound.mp3', type: 'filler' as const, source: 'tts' as const, volume: 1 },
        ],
      })
    })

    const { unmount } = render(<MagicDJPage />)

    // Flush the async initAndLoad / loadTracks promises
    await act(async () => {
      await Promise.resolve()
    })

    // Let loading complete
    await act(async () => {
      vi.advanceTimersByTime(200)
    })

    // Clear any revokeObjectURL calls that happened during init
    vi.mocked(URL.revokeObjectURL).mockClear()

    // Unmount the component
    unmount()

    // Blob URLs should NOT be revoked on unmount — initializeStorage()
    // handles revoking stale URLs when it creates fresh ones on next mount.
    // Revoking here would break SPA re-navigation.
    expect(URL.revokeObjectURL).not.toHaveBeenCalled()
  })
})
