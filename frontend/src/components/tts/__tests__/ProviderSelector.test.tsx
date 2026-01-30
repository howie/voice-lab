/**
 * ProviderSelector Component Tests
 * T036: Create frontend component tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ProviderSelector, PROVIDERS } from '../ProviderSelector'
import { invalidateTTSProviderCache } from '@/hooks/useAvailableTTSProviders'

// Mock the ttsApi
vi.mock('@/lib/api', () => ({
  ttsApi: {
    getProvidersSummary: vi.fn(),
  },
}))

import { ttsApi } from '@/lib/api'

const mockGetProvidersSummary = vi.mocked(ttsApi.getProvidersSummary)

/** Helper: build a mock summary response with given available provider names */
function mockSummaryResponse(availableNames: string[]) {
  const allNames = ['azure', 'gcp', 'gemini', 'elevenlabs', 'voai']
  return {
    data: {
      tts: allNames.map((name) => ({
        name,
        display_name: name,
        type: 'tts',
        supported_formats: [],
        supported_languages: [],
        supported_params: {},
        status: availableNames.includes(name) ? 'available' : 'unavailable',
      })),
      stt: [],
      llm: [],
    },
  }
}

describe('ProviderSelector', () => {
  const defaultProps = {
    value: 'azure',
    onChange: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
    invalidateTTSProviderCache()
    // Default: all providers available
    mockGetProvidersSummary.mockResolvedValue(
      mockSummaryResponse(['azure', 'gcp', 'gemini', 'elevenlabs', 'voai']) as never
    )
  })

  describe('rendering', () => {
    it('shows loading state then renders select', async () => {
      render(<ProviderSelector {...defaultProps} />)

      // Loading state
      expect(screen.getByText('載入可用 Provider...')).toBeInTheDocument()

      // After loading
      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument()
      })
      expect(screen.getByText('選擇 Provider')).toBeInTheDocument()
    })

    it('renders all provider options when all are available', async () => {
      render(<ProviderSelector {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument()
      })

      PROVIDERS.forEach((provider) => {
        expect(screen.getByText(provider.displayName)).toBeInTheDocument()
      })
    })

    it('selects the correct initial value', async () => {
      render(<ProviderSelector {...defaultProps} value="elevenlabs" />)

      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument()
      })

      const select = screen.getByRole('combobox')
      expect(select).toHaveValue('elevenlabs')
    })

    it('displays provider description for selected value', async () => {
      render(<ProviderSelector {...defaultProps} value="azure" />)

      await waitFor(() => {
        expect(screen.getByText('Microsoft Azure 語音服務')).toBeInTheDocument()
      })
    })
  })

  describe('availability filtering', () => {
    it('only shows available providers', async () => {
      mockGetProvidersSummary.mockResolvedValue(
        mockSummaryResponse(['azure', 'gemini']) as never
      )

      render(<ProviderSelector {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument()
      })

      const options = screen.getAllByRole('option')
      expect(options).toHaveLength(2)
      expect(screen.getByText('Azure Speech')).toBeInTheDocument()
      expect(screen.getByText('Gemini TTS')).toBeInTheDocument()
      expect(screen.queryByText('ElevenLabs')).not.toBeInTheDocument()
      expect(screen.queryByText('VoAI 台灣語音')).not.toBeInTheDocument()
    })

    it('auto-switches to first available when current is unavailable', async () => {
      const onChange = vi.fn()
      mockGetProvidersSummary.mockResolvedValue(
        mockSummaryResponse(['gemini', 'elevenlabs']) as never
      )

      render(<ProviderSelector value="azure" onChange={onChange} />)

      await waitFor(() => {
        expect(onChange).toHaveBeenCalledWith('gemini')
      })
    })

    it('does not auto-switch when current provider is available', async () => {
      const onChange = vi.fn()
      mockGetProvidersSummary.mockResolvedValue(
        mockSummaryResponse(['azure', 'gemini']) as never
      )

      render(<ProviderSelector value="azure" onChange={onChange} />)

      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument()
      })

      expect(onChange).not.toHaveBeenCalled()
    })

    it('falls back to full list when no providers are available', async () => {
      mockGetProvidersSummary.mockResolvedValue(
        mockSummaryResponse([]) as never
      )

      render(<ProviderSelector {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument()
      })

      const options = screen.getAllByRole('option')
      expect(options).toHaveLength(PROVIDERS.length)
    })

    it('falls back to full list on API error', async () => {
      mockGetProvidersSummary.mockRejectedValue(new Error('Network error'))

      render(<ProviderSelector {...defaultProps} />)

      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument()
      })

      const options = screen.getAllByRole('option')
      expect(options).toHaveLength(PROVIDERS.length)
    })
  })

  describe('user interaction', () => {
    it('calls onChange when selection changes', async () => {
      const onChange = vi.fn()
      render(<ProviderSelector {...defaultProps} onChange={onChange} />)

      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument()
      })

      const select = screen.getByRole('combobox')
      await userEvent.selectOptions(select, 'gcp')

      expect(onChange).toHaveBeenCalledWith('gcp')
    })

    it('updates description when selection changes', async () => {
      const { rerender } = render(
        <ProviderSelector {...defaultProps} value="azure" />
      )

      await waitFor(() => {
        expect(screen.getByText('Microsoft Azure 語音服務')).toBeInTheDocument()
      })

      rerender(<ProviderSelector {...defaultProps} value="gcp" />)

      expect(
        screen.getByText('Google Cloud Platform 傳統 TTS 服務')
      ).toBeInTheDocument()
    })
  })

  describe('disabled state', () => {
    it('disables select when disabled prop is true', async () => {
      render(<ProviderSelector {...defaultProps} disabled />)

      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument()
      })

      const select = screen.getByRole('combobox')
      expect(select).toBeDisabled()
    })
  })

  describe('PROVIDERS constant', () => {
    it('exports PROVIDERS array with 5 providers', () => {
      expect(PROVIDERS).toHaveLength(5)
    })

    it('each provider has required properties', () => {
      PROVIDERS.forEach((provider) => {
        expect(provider).toHaveProperty('id')
        expect(provider).toHaveProperty('name')
        expect(provider).toHaveProperty('displayName')
      })
    })
  })
})
