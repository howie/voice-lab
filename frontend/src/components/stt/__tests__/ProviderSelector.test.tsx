/**
 * ProviderSelector Component Tests (Dropdown)
 * Feature: 003-stt-testing-module
 * T079: Write failing tests for dropdown ProviderSelector
 *
 * Tests the dropdown-based provider selector that filters by credential status.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { STTProvider, STTProviderName } from '@/types/stt'

// Mock the sttStore
const mockLoadProviders = vi.fn()
const mockSetSelectedProvider = vi.fn()

vi.mock('@/stores/sttStore', () => ({
  useSTTStore: vi.fn(() => ({
    selectedProvider: 'azure' as STTProviderName,
    setSelectedProvider: mockSetSelectedProvider,
    availableProviders: [] as STTProvider[],
    providersLoading: false,
    loadProviders: mockLoadProviders,
  })),
}))

import { useSTTStore } from '@/stores/sttStore'
import { ProviderSelector } from '../ProviderSelector'

const mockedUseSTTStore = vi.mocked(useSTTStore)

// Test data
const azureProvider: STTProvider = {
  name: 'azure',
  display_name: 'Azure Speech Services',
  supports_streaming: true,
  supports_child_mode: true,
  max_duration_sec: 600,
  max_file_size_mb: 200,
  supported_formats: ['mp3', 'wav', 'ogg', 'flac', 'webm'],
  supported_languages: ['zh-TW', 'en-US'],
  has_credentials: true,
  is_valid: true,
}

const gcpProvider: STTProvider = {
  name: 'gcp',
  display_name: 'Google Cloud STT',
  supports_streaming: true,
  supports_child_mode: true,
  max_duration_sec: 600,
  max_file_size_mb: 480,
  supported_formats: ['mp3', 'wav', 'ogg', 'flac', 'webm'],
  supported_languages: ['zh-TW', 'en-US'],
  has_credentials: true,
  is_valid: true,
}

const whisperProviderNoCredentials: STTProvider = {
  name: 'whisper',
  display_name: 'OpenAI Whisper',
  supports_streaming: false,
  supports_child_mode: false,
  max_duration_sec: 600,
  max_file_size_mb: 25,
  supported_formats: ['mp3', 'wav', 'webm'],
  supported_languages: ['zh-TW', 'en-US'],
  has_credentials: false,
  is_valid: false,
}

const whisperProviderInvalidKey: STTProvider = {
  ...whisperProviderNoCredentials,
  has_credentials: true,
  is_valid: false,
}

function setupStore(overrides: Partial<ReturnType<typeof useSTTStore>>) {
  mockedUseSTTStore.mockReturnValue({
    selectedProvider: 'azure',
    setSelectedProvider: mockSetSelectedProvider,
    availableProviders: [],
    providersLoading: false,
    loadProviders: mockLoadProviders,
    ...overrides,
  } as ReturnType<typeof useSTTStore>)
}

describe('ProviderSelector (Dropdown)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('rendering', () => {
    it('renders a <select> dropdown element (not cards)', () => {
      setupStore({
        availableProviders: [azureProvider, gcpProvider],
      })
      render(<ProviderSelector />)

      expect(screen.getByRole('combobox')).toBeInTheDocument()
      // Should NOT have any card-style buttons
      expect(screen.queryAllByRole('button')).toHaveLength(0)
    })

    it('renders label text', () => {
      setupStore({
        availableProviders: [azureProvider],
      })
      render(<ProviderSelector />)

      expect(screen.getByText('選擇 Provider')).toBeInTheDocument()
    })

    it('renders loading skeleton when providers are loading', () => {
      setupStore({
        providersLoading: true,
        availableProviders: [],
      })
      render(<ProviderSelector />)

      // Should not show select while loading
      expect(screen.queryByRole('combobox')).not.toBeInTheDocument()
    })
  })

  describe('credential filtering', () => {
    it('only shows providers with has_credentials=true AND is_valid=true', () => {
      setupStore({
        availableProviders: [azureProvider, gcpProvider, whisperProviderNoCredentials],
      })
      render(<ProviderSelector />)

      const options = screen.getAllByRole('option')
      expect(options).toHaveLength(2)
      expect(screen.getByRole('option', { name: 'Azure Speech Services' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'Google Cloud STT' })).toBeInTheDocument()
    })

    it('hides providers with has_credentials=false', () => {
      setupStore({
        availableProviders: [azureProvider, whisperProviderNoCredentials],
      })
      render(<ProviderSelector />)

      expect(screen.queryByText('OpenAI Whisper')).not.toBeInTheDocument()
    })

    it('hides providers with has_credentials=true but is_valid=false', () => {
      setupStore({
        availableProviders: [azureProvider, whisperProviderInvalidKey],
      })
      render(<ProviderSelector />)

      const options = screen.getAllByRole('option')
      expect(options).toHaveLength(1)
      expect(screen.queryByText('OpenAI Whisper')).not.toBeInTheDocument()
    })
  })

  describe('empty state', () => {
    it('shows empty state message when no providers have valid credentials', () => {
      setupStore({
        availableProviders: [whisperProviderNoCredentials],
      })
      render(<ProviderSelector />)

      expect(screen.getByText(/請先至 Provider 管理頁面設定 API Key/)).toBeInTheDocument()
      expect(screen.queryByRole('combobox')).not.toBeInTheDocument()
    })

    it('shows empty state when provider list is empty', () => {
      setupStore({
        availableProviders: [],
      })
      render(<ProviderSelector />)

      expect(screen.getByText(/請先至 Provider 管理頁面設定 API Key/)).toBeInTheDocument()
    })
  })

  describe('selection interaction', () => {
    it('calls setSelectedProvider when user selects a different provider', async () => {
      setupStore({
        selectedProvider: 'azure',
        availableProviders: [azureProvider, gcpProvider],
      })
      render(<ProviderSelector />)

      const select = screen.getByRole('combobox')
      await userEvent.selectOptions(select, 'gcp')

      expect(mockSetSelectedProvider).toHaveBeenCalledWith('gcp')
    })

    it('calls onProviderChange callback when provided', async () => {
      const onProviderChange = vi.fn()
      setupStore({
        selectedProvider: 'azure',
        availableProviders: [azureProvider, gcpProvider],
      })
      render(<ProviderSelector onProviderChange={onProviderChange} />)

      const select = screen.getByRole('combobox')
      await userEvent.selectOptions(select, 'gcp')

      expect(onProviderChange).toHaveBeenCalledWith('gcp')
    })

    it('disables select when disabled prop is true', () => {
      setupStore({
        availableProviders: [azureProvider, gcpProvider],
      })
      render(<ProviderSelector disabled />)

      expect(screen.getByRole('combobox')).toBeDisabled()
    })
  })

  describe('ProviderCapabilities display', () => {
    it('shows provider capabilities for selected provider', () => {
      setupStore({
        selectedProvider: 'azure',
        availableProviders: [azureProvider, gcpProvider],
      })
      render(<ProviderSelector />)

      expect(screen.getByText(/200 MB/)).toBeInTheDocument()
      expect(screen.getByText(/10 min/)).toBeInTheDocument()
    })

    it('shows child mode status for selected provider', () => {
      setupStore({
        selectedProvider: 'azure',
        availableProviders: [azureProvider],
      })
      render(<ProviderSelector />)

      expect(screen.getByText('Yes')).toBeInTheDocument()
    })

    it('hides capabilities when showCapabilities is false', () => {
      setupStore({
        selectedProvider: 'azure',
        availableProviders: [azureProvider],
      })
      render(<ProviderSelector showCapabilities={false} />)

      expect(screen.queryByText(/200 MB/)).not.toBeInTheDocument()
    })
  })

  describe('auto-load', () => {
    it('calls loadProviders on mount when providers list is empty', () => {
      setupStore({
        availableProviders: [],
      })
      render(<ProviderSelector />)

      expect(mockLoadProviders).toHaveBeenCalledTimes(1)
    })

    it('does not call loadProviders when providers already loaded', () => {
      setupStore({
        availableProviders: [azureProvider],
      })
      render(<ProviderSelector />)

      expect(mockLoadProviders).not.toHaveBeenCalled()
    })
  })
})
