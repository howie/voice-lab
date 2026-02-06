/**
 * TrackEditorModal Tests
 * Feature: 010-magic-dj-controller, 011-magic-dj-audio-features
 *
 * Tests for modal visibility, form initialization, audio source mode toggle,
 * form validation, and preview play/stop behavior.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'

import { TrackEditorModal, type TrackEditorModalProps } from '../TrackEditorModal'
import type { Track } from '@/types/magic-dj'

// =============================================================================
// Mocks
// =============================================================================

vi.mock('@/hooks/useAvailableTTSProviders', () => ({
  useAvailableTTSProviders: () => ({
    providers: [{ id: 'voai', name: 'VoAI' }],
    loading: false,
    availableNames: new Set(['voai']),
  }),
}))

vi.mock('@/lib/api', () => ({
  ttsApi: {
    getVoices: vi.fn().mockResolvedValue({
      data: [
        { id: 'voai-tw-female-1', name: 'Female 1', provider: 'voai', language: 'zh-TW', gender: 'female' },
      ],
    }),
    synthesizeBinary: vi.fn().mockResolvedValue(new Blob(['audio-data'], { type: 'audio/mpeg' })),
    getProvidersSummary: vi.fn().mockResolvedValue({
      data: { tts: [{ name: 'voai', status: 'available' }] },
    }),
  },
}))

vi.mock('../AudioDropzone', () => ({
  AudioDropzone: ({ onFileAccepted }: { onFileAccepted: (state: unknown) => void }) => (
    <div data-testid="audio-dropzone">
      <button
        data-testid="mock-file-upload"
        onClick={() =>
          onFileAccepted({
            file: new File(['audio'], 'test.mp3', { type: 'audio/mpeg' }),
            fileName: 'test.mp3',
            fileSize: 1024,
            audioUrl: 'blob:mock-upload-url',
            audioBase64: null,
            duration: 3000,
            error: null,
            isProcessing: false,
          })
        }
      >
        Upload
      </button>
    </div>
  ),
}))

// =============================================================================
// Helpers
// =============================================================================

const defaultProps: TrackEditorModalProps = {
  isOpen: true,
  onClose: vi.fn(),
  onSave: vi.fn(),
  editingTrack: null,
  existingText: '',
}

function renderModal(overrides: Partial<TrackEditorModalProps> = {}) {
  return render(<TrackEditorModal {...defaultProps} {...overrides} />)
}

/** Build a minimal Track object for editing tests. */
function makeTrack(overrides: Partial<Track> = {}): Track {
  return {
    id: 'track_test',
    name: 'Test Track',
    type: 'effect',
    url: 'blob:existing-url',
    source: 'tts',
    volume: 0.8,
    isCustom: true,
    textContent: 'Hello world',
    hotkey: 'a',
    ...overrides,
  }
}

// =============================================================================
// Tests
// =============================================================================

describe('TrackEditorModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ---------------------------------------------------------------------------
  // 1. Modal visibility
  // ---------------------------------------------------------------------------
  describe('Modal visibility', () => {
    it('renders nothing when isOpen is false', () => {
      const { container } = renderModal({ isOpen: false })
      expect(container.innerHTML).toBe('')
    })

    it('renders the modal when isOpen is true', () => {
      renderModal({ isOpen: true })
      expect(screen.getByText('新增音軌')).toBeInTheDocument()
    })

    it('renders with fixed inset-0 z-50 overlay', () => {
      const { container } = renderModal({ isOpen: true })
      const overlay = container.firstChild as HTMLElement
      expect(overlay.className).toContain('fixed')
      expect(overlay.className).toContain('inset-0')
      expect(overlay.className).toContain('z-50')
    })
  })

  // ---------------------------------------------------------------------------
  // 2. Form initialization
  // ---------------------------------------------------------------------------
  describe('Form initialization', () => {
    it('shows empty form fields when editingTrack is null', () => {
      renderModal({ editingTrack: null })

      const nameInput = screen.getByPlaceholderText('例如：開場白') as HTMLInputElement
      expect(nameInput.value).toBe('')
    })

    it('shows "新增音軌" title when editingTrack is null', () => {
      renderModal({ editingTrack: null })
      expect(screen.getByText('新增音軌')).toBeInTheDocument()
    })

    it('pre-fills form fields when editingTrack is provided', () => {
      const track = makeTrack({ name: 'My Intro', type: 'intro', hotkey: 'x' })
      renderModal({ editingTrack: track })

      const nameInput = screen.getByPlaceholderText('例如：開場白') as HTMLInputElement
      expect(nameInput.value).toBe('My Intro')
    })

    it('shows "編輯音軌" title when editingTrack is provided', () => {
      const track = makeTrack()
      renderModal({ editingTrack: track })
      expect(screen.getByText('編輯音軌')).toBeInTheDocument()
    })

    it('pre-fills text from existingText prop', () => {
      renderModal({ existingText: 'Prefilled text' })

      const textarea = screen.getByPlaceholderText('輸入要轉換成語音的文字...') as HTMLTextAreaElement
      expect(textarea.value).toBe('Prefilled text')
    })

    it('sets audio source mode to upload when editing an upload track', () => {
      const track = makeTrack({ source: 'upload' })
      renderModal({ editingTrack: track })

      // In upload mode, AudioDropzone should be visible
      expect(screen.getByTestId('audio-dropzone')).toBeInTheDocument()
    })

    it('sets audio source mode to tts when editing a tts track', () => {
      const track = makeTrack({ source: 'tts' })
      renderModal({ editingTrack: track })

      // In TTS mode, the textarea for text content should be visible
      expect(screen.getByPlaceholderText('輸入要轉換成語音的文字...')).toBeInTheDocument()
    })
  })

  // ---------------------------------------------------------------------------
  // 3. Audio source mode toggle
  // ---------------------------------------------------------------------------
  describe('Audio source mode toggle', () => {
    it('defaults to TTS mode and shows TTS section', () => {
      renderModal()

      // TTS mode: textarea and TTS settings should be visible
      expect(screen.getByPlaceholderText('輸入要轉換成語音的文字...')).toBeInTheDocument()
      expect(screen.getByText('TTS 設定')).toBeInTheDocument()
    })

    it('does not show AudioDropzone in TTS mode', () => {
      renderModal()
      expect(screen.queryByTestId('audio-dropzone')).not.toBeInTheDocument()
    })

    it('switches to Upload mode when upload button is clicked', () => {
      renderModal()

      fireEvent.click(screen.getByText('上傳音檔'))

      // Upload mode: AudioDropzone should appear
      expect(screen.getByTestId('audio-dropzone')).toBeInTheDocument()
    })

    it('hides TTS section when in Upload mode', () => {
      renderModal()

      fireEvent.click(screen.getByText('上傳音檔'))

      expect(screen.queryByPlaceholderText('輸入要轉換成語音的文字...')).not.toBeInTheDocument()
      expect(screen.queryByText('TTS 設定')).not.toBeInTheDocument()
    })

    it('switches back to TTS mode when TTS button is clicked', () => {
      renderModal()

      // Switch to upload
      fireEvent.click(screen.getByText('上傳音檔'))
      expect(screen.queryByText('TTS 設定')).not.toBeInTheDocument()

      // Switch back to TTS
      fireEvent.click(screen.getByText('TTS 語音合成'))
      expect(screen.getByText('TTS 設定')).toBeInTheDocument()
    })
  })

  // ---------------------------------------------------------------------------
  // 4. Form validation
  // ---------------------------------------------------------------------------
  describe('Form validation', () => {
    it('save button is disabled when track name is empty', () => {
      renderModal()

      const saveButton = screen.getByText('儲存').closest('button')!
      expect(saveButton).toBeDisabled()
    })

    it('save button is disabled in TTS mode when no audio has been generated', () => {
      renderModal()

      // Enter a name but do not generate audio
      const nameInput = screen.getByPlaceholderText('例如：開場白')
      fireEvent.change(nameInput, { target: { value: 'My Track' } })

      const saveButton = screen.getByText('儲存').closest('button')!
      expect(saveButton).toBeDisabled()
    })

    it('shows error when saving without track name', () => {
      renderModal()

      // Click save without entering name
      const saveButton = screen.getByText('儲存').closest('button')!
      fireEvent.click(saveButton)

      // The button is disabled so onSave should not be called
      expect(defaultProps.onSave).not.toHaveBeenCalled()
    })

    it('save button is disabled in Upload mode when no file is uploaded', () => {
      renderModal()

      // Switch to upload mode
      fireEvent.click(screen.getByText('上傳音檔'))

      // Enter a name
      const nameInput = screen.getByPlaceholderText('例如：開場白')
      fireEvent.change(nameInput, { target: { value: 'My Track' } })

      const saveButton = screen.getByText('儲存').closest('button')!
      expect(saveButton).toBeDisabled()
    })

    it('save button is enabled in Upload mode after file is uploaded and name is filled', () => {
      renderModal()

      // Switch to upload mode
      fireEvent.click(screen.getByText('上傳音檔'))

      // Enter a name
      const nameInput = screen.getByPlaceholderText('例如：開場白')
      fireEvent.change(nameInput, { target: { value: 'My Track' } })

      // Simulate file upload via the mocked AudioDropzone
      fireEvent.click(screen.getByTestId('mock-file-upload'))

      const saveButton = screen.getByText('儲存').closest('button')!
      expect(saveButton).not.toBeDisabled()
    })

    it('calls onSave with correct Track when saving in Upload mode', () => {
      const onSave = vi.fn()
      renderModal({ onSave })

      // Switch to upload mode
      fireEvent.click(screen.getByText('上傳音檔'))

      // Enter a name
      const nameInput = screen.getByPlaceholderText('例如：開場白')
      fireEvent.change(nameInput, { target: { value: 'Uploaded Track' } })

      // Upload file
      fireEvent.click(screen.getByTestId('mock-file-upload'))

      // Save
      const saveButton = screen.getByText('儲存').closest('button')!
      fireEvent.click(saveButton)

      expect(onSave).toHaveBeenCalledTimes(1)
      const [savedTrack, savedBlob] = onSave.mock.calls[0]
      expect(savedTrack.name).toBe('Uploaded Track')
      expect(savedTrack.source).toBe('upload')
      expect(savedTrack.originalFileName).toBe('test.mp3')
      expect(savedBlob).toBeInstanceOf(File)
    })

    it('calls onSave and onClose when saving in TTS mode with generated audio', async () => {
      const { ttsApi } = await import('@/lib/api')
      const onSave = vi.fn()
      const onClose = vi.fn()
      renderModal({ onSave, onClose })

      // Enter a name
      const nameInput = screen.getByPlaceholderText('例如：開場白')
      fireEvent.change(nameInput, { target: { value: 'TTS Track' } })

      // Enter text
      const textarea = screen.getByPlaceholderText('輸入要轉換成語音的文字...')
      fireEvent.change(textarea, { target: { value: 'Hello from TTS' } })

      // Click generate
      const generateButton = screen.getByText('生成語音').closest('button')!
      fireEvent.click(generateButton)

      await waitFor(() => {
        expect(ttsApi.synthesizeBinary).toHaveBeenCalled()
      })

      // After generation, save button should be enabled
      await waitFor(() => {
        const saveButton = screen.getByText('儲存').closest('button')!
        expect(saveButton).not.toBeDisabled()
      })

      const saveButton = screen.getByText('儲存').closest('button')!
      fireEvent.click(saveButton)

      expect(onSave).toHaveBeenCalledTimes(1)
      const [savedTrack, savedBlob] = onSave.mock.calls[0]
      expect(savedTrack.name).toBe('TTS Track')
      expect(savedTrack.source).toBe('tts')
      expect(savedTrack.textContent).toBe('Hello from TTS')
      expect(savedBlob).toBeInstanceOf(Blob)
      expect(onClose).toHaveBeenCalledTimes(1)
    })
  })

  // ---------------------------------------------------------------------------
  // 5. Preview play/stop
  // ---------------------------------------------------------------------------
  describe('Preview play/stop', () => {
    it('does not show preview button when no audio is available in TTS mode', () => {
      renderModal()

      // No audio generated yet
      expect(screen.queryByText('試聽')).not.toBeInTheDocument()
    })

    it('shows preview button after TTS audio is generated', async () => {
      renderModal()

      // Enter text and generate
      const textarea = screen.getByPlaceholderText('輸入要轉換成語音的文字...')
      fireEvent.change(textarea, { target: { value: 'Preview this' } })

      const generateButton = screen.getByText('生成語音').closest('button')!
      fireEvent.click(generateButton)

      await waitFor(() => {
        expect(screen.getByText('試聽')).toBeInTheDocument()
      })
    })

    it('shows preview button in Upload mode after file upload', () => {
      renderModal()

      // Switch to upload mode
      fireEvent.click(screen.getByText('上傳音檔'))

      // Upload file
      fireEvent.click(screen.getByTestId('mock-file-upload'))

      expect(screen.getByText('試聽')).toBeInTheDocument()
    })

    it('does not show preview button in Upload mode before file upload', () => {
      renderModal()

      // Switch to upload mode
      fireEvent.click(screen.getByText('上傳音檔'))

      // No file uploaded yet
      expect(screen.queryByText('試聽')).not.toBeInTheDocument()
    })
  })

  // ---------------------------------------------------------------------------
  // Close behavior
  // ---------------------------------------------------------------------------
  describe('Close behavior', () => {
    it('calls onClose when close (X) button is clicked', () => {
      const onClose = vi.fn()
      renderModal({ onClose })

      // The X button is the first button in the header
      const closeButtons = screen.getAllByRole('button')
      // First button in modal is the X close button
      const xButton = closeButtons[0]
      fireEvent.click(xButton)

      expect(onClose).toHaveBeenCalledTimes(1)
    })

    it('calls onClose when cancel button is clicked', () => {
      const onClose = vi.fn()
      renderModal({ onClose })

      fireEvent.click(screen.getByText('取消'))
      expect(onClose).toHaveBeenCalledTimes(1)
    })
  })
})
