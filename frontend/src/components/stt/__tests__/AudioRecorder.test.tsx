/**
 * AudioRecorder Component Tests
 * Feature: 003-stt-testing-module
 * T037: Unit test for AudioRecorder component
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AudioRecorder } from '../AudioRecorder'

// Mock MediaRecorder
const mockMediaRecorder = {
  start: vi.fn(),
  stop: vi.fn(),
  pause: vi.fn(),
  resume: vi.fn(),
  ondataavailable: null as ((event: { data: Blob }) => void) | null,
  onstop: null as (() => void) | null,
  onerror: null as (() => void) | null,
  state: 'inactive' as RecordingState,
}

// Mock MediaStream
const mockMediaStream = {
  getTracks: vi.fn(() => [
    {
      stop: vi.fn(),
      kind: 'audio',
    },
  ]),
}

// Mock AudioContext
const mockAudioContext = {
  createAnalyser: vi.fn(() => ({
    fftSize: 2048,
    frequencyBinCount: 1024,
    getByteTimeDomainData: vi.fn((array) => {
      // Fill with silence (128 is center)
      array.fill(128)
    }),
  })),
  createMediaStreamSource: vi.fn(() => ({
    connect: vi.fn(),
  })),
  close: vi.fn(),
  state: 'running',
}

// Setup global mocks
beforeEach(() => {
  vi.clearAllMocks()

  // Reset mock state
  mockMediaRecorder.state = 'inactive'

  // Mock navigator.mediaDevices.getUserMedia
  Object.defineProperty(navigator, 'mediaDevices', {
    value: {
      getUserMedia: vi.fn().mockResolvedValue(mockMediaStream),
    },
    writable: true,
  })

  // Mock navigator.permissions.query
  Object.defineProperty(navigator, 'permissions', {
    value: {
      query: vi.fn().mockResolvedValue({
        state: 'prompt',
        addEventListener: vi.fn(),
      }),
    },
    writable: true,
  })

  // Mock MediaRecorder
  global.MediaRecorder = vi.fn().mockImplementation(() => {
    return {
      ...mockMediaRecorder,
      start: vi.fn(() => {
        mockMediaRecorder.state = 'recording'
      }),
      stop: vi.fn(() => {
        mockMediaRecorder.state = 'inactive'
        if (mockMediaRecorder.onstop) {
          mockMediaRecorder.onstop()
        }
      }),
    }
  }) as unknown as typeof MediaRecorder

  // Mock MediaRecorder.isTypeSupported
  ;(MediaRecorder as unknown as { isTypeSupported: (type: string) => boolean }).isTypeSupported =
    vi.fn((type: string) => {
      return ['audio/webm', 'audio/webm;codecs=opus', 'audio/mp4'].includes(type)
    })

  // Mock AudioContext
  global.AudioContext = vi.fn().mockImplementation(() => mockAudioContext) as unknown as typeof AudioContext

  // Mock requestAnimationFrame
  global.requestAnimationFrame = vi.fn((cb) => {
    return setTimeout(cb, 16) as unknown as number
  })

  global.cancelAnimationFrame = vi.fn((id) => {
    clearTimeout(id)
  })
})

afterEach(() => {
  vi.clearAllMocks()
})

describe('AudioRecorder', () => {
  describe('rendering', () => {
    it('renders record button', () => {
      render(<AudioRecorder />)

      const recordButton = screen.getByRole('button', { name: /start recording/i })
      expect(recordButton).toBeInTheDocument()
    })

    it('renders canvas for waveform', () => {
      const { container } = render(<AudioRecorder />)

      const canvas = container.querySelector('canvas')
      expect(canvas).toBeInTheDocument()
    })

    it('renders initial duration as 0:00', () => {
      render(<AudioRecorder />)

      expect(screen.getByText(/0:00/)).toBeInTheDocument()
    })

    it('shows instruction text when idle', () => {
      render(<AudioRecorder />)

      expect(screen.getByText(/click the button to start recording/i)).toBeInTheDocument()
    })
  })

  describe('disabled state', () => {
    it('disables record button when disabled prop is true', () => {
      render(<AudioRecorder disabled />)

      const recordButton = screen.getByRole('button', { name: /start recording/i })
      expect(recordButton).toBeDisabled()
    })
  })

  describe('recording flow', () => {
    it('requests microphone permission on record click', async () => {
      render(<AudioRecorder />)

      const recordButton = screen.getByRole('button', { name: /start recording/i })
      fireEvent.click(recordButton)

      await waitFor(() => {
        expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith(
          expect.objectContaining({
            audio: expect.any(Object),
          })
        )
      })
    })

    it('calls onRecordingStart callback when recording begins', async () => {
      const onRecordingStart = vi.fn()
      render(<AudioRecorder onRecordingStart={onRecordingStart} />)

      const recordButton = screen.getByRole('button', { name: /start recording/i })
      fireEvent.click(recordButton)

      await waitFor(() => {
        expect(onRecordingStart).toHaveBeenCalled()
      })
    })

    it('shows REC indicator when recording', async () => {
      render(<AudioRecorder />)

      const recordButton = screen.getByRole('button', { name: /start recording/i })
      fireEvent.click(recordButton)

      await waitFor(() => {
        expect(screen.getByText('REC')).toBeInTheDocument()
      })
    })

    it('changes button to stop icon when recording', async () => {
      render(<AudioRecorder />)

      const recordButton = screen.getByRole('button', { name: /start recording/i })
      fireEvent.click(recordButton)

      await waitFor(() => {
        const stopButton = screen.getByRole('button', { name: /stop recording/i })
        expect(stopButton).toBeInTheDocument()
      })
    })
  })

  describe('stopping recording', () => {
    it('calls stop on MediaRecorder when stop button is clicked', async () => {
      const stopMock = vi.fn()

      // Setup mock that tracks stop calls
      global.MediaRecorder = vi.fn().mockImplementation(() => {
        return {
          start: vi.fn(),
          stop: stopMock,
          state: 'recording',
          ondataavailable: null,
          onstop: null,
          onerror: null,
        }
      }) as unknown as typeof MediaRecorder
      ;(MediaRecorder as unknown as { isTypeSupported: (type: string) => boolean }).isTypeSupported =
        vi.fn(() => true)

      render(<AudioRecorder />)

      // Start recording
      const recordButton = screen.getByRole('button', { name: /start recording/i })
      fireEvent.click(recordButton)

      await waitFor(() => {
        expect(screen.getByText('REC')).toBeInTheDocument()
      })

      // Stop recording
      const stopButton = screen.getByRole('button', { name: /stop recording/i })
      fireEvent.click(stopButton)

      // Verify stop was called on MediaRecorder
      expect(stopMock).toHaveBeenCalled()
    })
  })

  describe('permission handling', () => {
    it('shows error when microphone access is denied', async () => {
      const onError = vi.fn()

      // Mock getUserMedia to reject
      vi.mocked(navigator.mediaDevices.getUserMedia).mockRejectedValueOnce(
        new DOMException('Permission denied', 'NotAllowedError')
      )

      render(<AudioRecorder onError={onError} />)

      const recordButton = screen.getByRole('button', { name: /start recording/i })
      fireEvent.click(recordButton)

      await waitFor(() => {
        expect(onError).toHaveBeenCalledWith(
          expect.stringContaining('Microphone access denied')
        )
      })
    })

    it('shows error when no microphone found', async () => {
      const onError = vi.fn()

      vi.mocked(navigator.mediaDevices.getUserMedia).mockRejectedValueOnce(
        new DOMException('No microphone', 'NotFoundError')
      )

      render(<AudioRecorder onError={onError} />)

      const recordButton = screen.getByRole('button', { name: /start recording/i })
      fireEvent.click(recordButton)

      await waitFor(() => {
        expect(onError).toHaveBeenCalledWith(
          expect.stringContaining('No microphone found')
        )
      })
    })

    it('shows permission denied message after error', async () => {
      vi.mocked(navigator.mediaDevices.getUserMedia).mockRejectedValueOnce(
        new DOMException('Permission denied', 'NotAllowedError')
      )

      // Also update permission status
      vi.mocked(navigator.permissions.query).mockResolvedValueOnce({
        state: 'denied',
        addEventListener: vi.fn(),
      } as unknown as PermissionStatus)

      render(<AudioRecorder />)

      const recordButton = screen.getByRole('button', { name: /start recording/i })
      fireEvent.click(recordButton)

      await waitFor(() => {
        expect(screen.getByText(/Microphone access is blocked/i)).toBeInTheDocument()
      })
    })
  })

  describe('max duration', () => {
    it('displays max duration from props', () => {
      render(<AudioRecorder maxDuration={60} />)

      expect(screen.getByText(/1:00/)).toBeInTheDocument()
    })

    it('uses default max duration of 300 seconds', () => {
      render(<AudioRecorder />)

      expect(screen.getByText(/5:00/)).toBeInTheDocument()
    })
  })

  describe('callbacks', () => {
    it('passes blob to onRecordingComplete', async () => {
      const onRecordingComplete = vi.fn()

      // Create a mock that captures the ondataavailable and onstop callbacks
      let capturedOnStop: (() => void) | null = null

      global.MediaRecorder = vi.fn().mockImplementation(() => {
        const recorder = {
          start: vi.fn(() => {
            recorder.state = 'recording'
          }),
          stop: vi.fn(() => {
            recorder.state = 'inactive'
            if (capturedOnStop) {
              capturedOnStop()
            }
          }),
          state: 'inactive',
          ondataavailable: null,
          onstop: null,
          onerror: null,
        }

        // Capture the onstop callback when it's set
        Object.defineProperty(recorder, 'onstop', {
          set: (fn) => {
            capturedOnStop = fn
          },
          get: () => capturedOnStop,
        })

        return recorder
      }) as unknown as typeof MediaRecorder
      ;(MediaRecorder as unknown as { isTypeSupported: (type: string) => boolean }).isTypeSupported =
        vi.fn(() => true)

      render(<AudioRecorder onRecordingComplete={onRecordingComplete} />)

      // Start recording
      const recordButton = screen.getByRole('button', { name: /start recording/i })
      fireEvent.click(recordButton)

      await waitFor(() => {
        expect(screen.getByText('REC')).toBeInTheDocument()
      })

      // Stop recording
      const stopButton = screen.getByRole('button', { name: /stop recording/i })
      fireEvent.click(stopButton)

      await waitFor(() => {
        expect(onRecordingComplete).toHaveBeenCalledWith(expect.any(Blob))
      })
    })
  })

  describe('MIME type selection', () => {
    it('selects supported MIME type', async () => {
      ;(MediaRecorder as unknown as { isTypeSupported: (type: string) => boolean }).isTypeSupported =
        vi.fn((type: string) => type === 'audio/webm')

      render(<AudioRecorder />)

      const recordButton = screen.getByRole('button', { name: /start recording/i })
      fireEvent.click(recordButton)

      await waitFor(() => {
        expect(global.MediaRecorder).toHaveBeenCalledWith(
          expect.anything(),
          expect.objectContaining({
            mimeType: 'audio/webm',
          })
        )
      })
    })
  })

  describe('accessibility', () => {
    it('record button has accessible name', () => {
      render(<AudioRecorder />)

      expect(
        screen.getByRole('button', { name: /start recording/i })
      ).toBeInTheDocument()
    })

    it('stop button has accessible name when recording', async () => {
      render(<AudioRecorder />)

      const recordButton = screen.getByRole('button', { name: /start recording/i })
      fireEvent.click(recordButton)

      await waitFor(() => {
        expect(
          screen.getByRole('button', { name: /stop recording/i })
        ).toBeInTheDocument()
      })
    })
  })
})
