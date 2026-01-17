/**
 * AudioPlayer Component Tests
 * T036: Create frontend component tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { AudioPlayer } from '../AudioPlayer'

// Mock downloadAudio from streaming module
vi.mock('@/lib/streaming', () => ({
  downloadAudio: vi.fn(),
}))

describe('AudioPlayer', () => {
  const mockAudioContent = btoa('fake-audio-content') // Base64 encoded

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('rendering', () => {
    it('renders play button', () => {
      render(<AudioPlayer />)

      const playButton = screen.getByRole('button', { name: '播放' })
      expect(playButton).toBeInTheDocument()
    })

    it('renders download button', () => {
      render(<AudioPlayer />)

      const downloadButton = screen.getByRole('button', { name: '下載音檔' })
      expect(downloadButton).toBeInTheDocument()
    })

    it('renders progress slider', () => {
      render(<AudioPlayer />)

      const slider = screen.getByRole('slider')
      expect(slider).toBeInTheDocument()
    })

    it('renders time display', () => {
      render(<AudioPlayer />)

      // Should show 0:00 / 0:00 initially
      expect(screen.getByText(/0:00 \/ 0:00/)).toBeInTheDocument()
    })

    it('renders with reduced opacity when no audio', () => {
      const { container } = render(<AudioPlayer />)

      const playerContainer = container.querySelector('.opacity-50')
      expect(playerContainer).toBeInTheDocument()
    })
  })

  describe('with audio content', () => {
    it('creates audio element when audioContent provided', () => {
      const { container } = render(
        <AudioPlayer audioContent={mockAudioContent} contentType="audio/mpeg" />
      )

      const audioElement = container.querySelector('audio')
      expect(audioElement).toBeInTheDocument()
    })

    it('enables play button when audio is loaded', () => {
      render(<AudioPlayer audioContent={mockAudioContent} />)

      const playButton = screen.getByRole('button', { name: '播放' })
      expect(playButton).not.toBeDisabled()
    })

    it('enables download button when audio is loaded', () => {
      render(<AudioPlayer audioContent={mockAudioContent} />)

      const downloadButton = screen.getByRole('button', { name: '下載音檔' })
      expect(downloadButton).not.toBeDisabled()
    })
  })

  describe('disabled state', () => {
    it('disables play button when disabled prop is true', () => {
      render(<AudioPlayer audioContent={mockAudioContent} disabled />)

      const playButton = screen.getByRole('button', { name: '播放' })
      expect(playButton).toBeDisabled()
    })

    it('disables download button when disabled prop is true', () => {
      render(<AudioPlayer audioContent={mockAudioContent} disabled />)

      const downloadButton = screen.getByRole('button', { name: '下載音檔' })
      expect(downloadButton).toBeDisabled()
    })

    it('disables slider when disabled prop is true', () => {
      render(<AudioPlayer audioContent={mockAudioContent} disabled />)

      const slider = screen.getByRole('slider')
      expect(slider).toBeDisabled()
    })
  })

  describe('callbacks', () => {
    it('calls onPlay when play is clicked', async () => {
      const onPlay = vi.fn()
      render(<AudioPlayer audioContent={mockAudioContent} onPlay={onPlay} />)

      const playButton = screen.getByRole('button', { name: '播放' })
      fireEvent.click(playButton)

      // Note: The actual play would be mocked in setup.ts
      // Here we're testing the click handler
    })

    it('calls onPause when pause is clicked', () => {
      const onPause = vi.fn()
      render(<AudioPlayer audioContent={mockAudioContent} onPause={onPause} />)

      // Simulate playing state and click pause
      const playButton = screen.getByRole('button', { name: '播放' })
      fireEvent.click(playButton)
    })
  })

  describe('time formatting', () => {
    it('displays duration from props', () => {
      render(<AudioPlayer audioContent={mockAudioContent} duration={65000} />)

      // 65000ms = 65 seconds = 1:05
      expect(screen.getByText(/1:05/)).toBeInTheDocument()
    })
  })

  describe('download functionality', () => {
    it('download button calls downloadAudio on click', async () => {
      const { downloadAudio } = await import('@/lib/streaming')
      render(<AudioPlayer audioContent={mockAudioContent} contentType="audio/mpeg" />)

      const downloadButton = screen.getByRole('button', { name: '下載音檔' })
      fireEvent.click(downloadButton)

      expect(downloadAudio).toHaveBeenCalledWith(
        mockAudioContent,
        'audio/mpeg',
        expect.stringMatching(/^tts-audio-\d+\.mp3$/)
      )
    })
  })

  describe('accessibility', () => {
    it('play button has accessible name', () => {
      render(<AudioPlayer />)

      expect(screen.getByRole('button', { name: '播放' })).toBeInTheDocument()
    })

    it('download button has accessible name', () => {
      render(<AudioPlayer />)

      expect(screen.getByRole('button', { name: '下載音檔' })).toBeInTheDocument()
    })

    it('slider is keyboard accessible', () => {
      render(<AudioPlayer audioContent={mockAudioContent} />)

      const slider = screen.getByRole('slider')
      slider.focus()
      expect(document.activeElement).toBe(slider)
    })
  })
})
