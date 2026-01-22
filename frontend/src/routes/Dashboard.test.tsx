/**
 * Dashboard Component Tests
 * Tests for null-safety in provider data display
 */

import { render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { BrowserRouter } from 'react-router-dom'
import { Dashboard } from './Dashboard'

// Mock the API
const mockGetProvidersSummary = vi.fn()

vi.mock('@/lib/api', () => ({
  ttsApi: {
    getProvidersSummary: () => mockGetProvidersSummary(),
  },
}))

const renderDashboard = () => {
  return render(
    <BrowserRouter>
      <Dashboard />
    </BrowserRouter>
  )
}

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('provider data display', () => {
    it('renders loading state initially', () => {
      mockGetProvidersSummary.mockReturnValue(new Promise(() => {})) // Never resolves

      renderDashboard()
      expect(screen.getByText('載入中...')).toBeInTheDocument()
    })

    it('renders error state when API fails', async () => {
      mockGetProvidersSummary.mockRejectedValue(new Error('API Error'))

      renderDashboard()

      await waitFor(() => {
        expect(screen.getByText('無法載入 Provider 資訊')).toBeInTheDocument()
      })
    })

    it('renders provider with complete data', async () => {
      mockGetProvidersSummary.mockResolvedValue({
        data: {
          tts: [
            {
              name: 'azure',
              display_name: 'Azure TTS',
              supported_formats: ['mp3', 'wav'],
              supported_languages: ['en-US', 'zh-TW', 'ja-JP', 'ko-KR'],
              status: 'available',
            },
          ],
          stt: [],
          llm: [],
        },
      })

      renderDashboard()

      await waitFor(() => {
        expect(screen.getByText('Azure TTS')).toBeInTheDocument()
        expect(screen.getByText('en-US, zh-TW, ja-JP...')).toBeInTheDocument()
      })
    })

    it('handles provider with undefined supported_languages', async () => {
      mockGetProvidersSummary.mockResolvedValue({
        data: {
          tts: [
            {
              name: 'test-provider',
              display_name: 'Test Provider',
              supported_formats: ['mp3'],
              supported_languages: undefined,
              status: 'available',
            },
          ],
          stt: [],
          llm: [],
        },
      })

      renderDashboard()

      await waitFor(() => {
        expect(screen.getByText('Test Provider')).toBeInTheDocument()
        // Should show '-' for undefined supported_languages
        const cells = screen.getAllByRole('cell')
        const languageCell = cells.find((cell) => cell.textContent === '-')
        expect(languageCell).toBeInTheDocument()
      })
    })

    it('handles provider with null supported_languages', async () => {
      mockGetProvidersSummary.mockResolvedValue({
        data: {
          tts: [
            {
              name: 'test-provider',
              display_name: 'Test Provider',
              supported_formats: ['mp3'],
              supported_languages: null,
              status: 'unavailable',
            },
          ],
          stt: [],
          llm: [],
        },
      })

      renderDashboard()

      await waitFor(() => {
        expect(screen.getByText('Test Provider')).toBeInTheDocument()
      })
    })

    it('handles provider with empty supported_languages array', async () => {
      mockGetProvidersSummary.mockResolvedValue({
        data: {
          tts: [
            {
              name: 'test-provider',
              display_name: 'Test Provider',
              supported_formats: ['mp3'],
              supported_languages: [],
              status: 'available',
            },
          ],
          stt: [],
          llm: [],
        },
      })

      renderDashboard()

      await waitFor(() => {
        expect(screen.getByText('Test Provider')).toBeInTheDocument()
        // Empty array should show '-'
        const cells = screen.getAllByRole('cell')
        const languageCell = cells.find((cell) => cell.textContent === '-')
        expect(languageCell).toBeInTheDocument()
      })
    })

    it('shows ellipsis when more than 3 languages', async () => {
      mockGetProvidersSummary.mockResolvedValue({
        data: {
          tts: [
            {
              name: 'test-provider',
              display_name: 'Test Provider',
              supported_formats: ['mp3'],
              supported_languages: ['en-US', 'zh-TW', 'ja-JP', 'ko-KR', 'fr-FR'],
              status: 'available',
            },
          ],
          stt: [],
          llm: [],
        },
      })

      renderDashboard()

      await waitFor(() => {
        expect(screen.getByText('en-US, zh-TW, ja-JP...')).toBeInTheDocument()
      })
    })

    it('does not show ellipsis when exactly 3 languages', async () => {
      mockGetProvidersSummary.mockResolvedValue({
        data: {
          tts: [
            {
              name: 'test-provider',
              display_name: 'Test Provider',
              supported_formats: ['mp3'],
              supported_languages: ['en-US', 'zh-TW', 'ja-JP'],
              status: 'available',
            },
          ],
          stt: [],
          llm: [],
        },
      })

      renderDashboard()

      await waitFor(() => {
        expect(screen.getByText('en-US, zh-TW, ja-JP')).toBeInTheDocument()
        // No ellipsis
        expect(screen.queryByText('en-US, zh-TW, ja-JP...')).not.toBeInTheDocument()
      })
    })

    it('renders multiple provider types', async () => {
      mockGetProvidersSummary.mockResolvedValue({
        data: {
          tts: [
            {
              name: 'azure',
              display_name: 'Azure TTS',
              supported_formats: ['mp3'],
              supported_languages: ['en-US'],
              status: 'available',
            },
          ],
          stt: [
            {
              name: 'google',
              display_name: 'Google STT',
              supported_formats: ['wav'],
              supported_languages: ['zh-TW'],
              status: 'available',
            },
          ],
          llm: [
            {
              name: 'openai',
              display_name: 'OpenAI',
              supported_formats: [],
              supported_languages: [],
              status: 'unavailable',
            },
          ],
        },
      })

      renderDashboard()

      await waitFor(() => {
        expect(screen.getByText('Azure TTS')).toBeInTheDocument()
        expect(screen.getByText('Google STT')).toBeInTheDocument()
        expect(screen.getByText('OpenAI')).toBeInTheDocument()
      })
    })
  })

  describe('status display', () => {
    it('displays correct status labels', async () => {
      mockGetProvidersSummary.mockResolvedValue({
        data: {
          tts: [
            {
              name: 'provider1',
              display_name: 'Available Provider',
              supported_formats: [],
              supported_languages: [],
              status: 'available',
            },
            {
              name: 'provider2',
              display_name: 'Unavailable Provider',
              supported_formats: [],
              supported_languages: [],
              status: 'unavailable',
            },
            {
              name: 'provider3',
              display_name: 'Degraded Provider',
              supported_formats: [],
              supported_languages: [],
              status: 'degraded',
            },
          ],
          stt: [],
          llm: [],
        },
      })

      renderDashboard()

      await waitFor(() => {
        expect(screen.getByText('已連接')).toBeInTheDocument()
        expect(screen.getByText('未設定')).toBeInTheDocument()
        expect(screen.getByText('降級')).toBeInTheDocument()
      })
    })
  })
})
