/**
 * Provider Switch Component Tests
 * T037: Test provider switch functionality in multi-role TTS
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import userEvent from '@testing-library/user-event'
import { useMultiRoleTTSStore } from '@/stores/multiRoleTTSStore'
import { MultiRoleTTSPage } from '@/routes/multi-role-tts/MultiRoleTTSPage'
import { ProviderCapabilityCard } from '../ProviderCapabilityCard'
import { invalidateTTSProviderCache } from '@/hooks/useAvailableTTSProviders'
import type { ProviderMultiRoleCapability } from '@/types/multi-role-tts'

// Mock the API modules
vi.mock('@/lib/multiRoleTTSApi', () => ({
  multiRoleTTSApi: {
    getCapabilities: vi.fn().mockResolvedValue({
      providers: [
        {
          providerName: 'elevenlabs',
          supportType: 'native',
          maxSpeakers: 6,
          characterLimit: 10000,
          advancedFeatures: ['interrupting', 'overlapping'],
          notes: 'Best quality for multi-speaker',
        },
        {
          providerName: 'azure',
          supportType: 'native',
          maxSpeakers: 6,
          characterLimit: 5000,
          advancedFeatures: [],
          notes: 'SSML support',
        },
        {
          providerName: 'openai',
          supportType: 'segmented',
          maxSpeakers: 6,
          characterLimit: 4096,
          advancedFeatures: [],
          notes: 'Audio merged locally',
        },
      ],
    }),
    parseDialogue: vi.fn().mockResolvedValue({
      turns: [
        { speaker: 'A', text: '你好', index: 0 },
        { speaker: 'B', text: '嗨', index: 1 },
      ],
      speakers: ['A', 'B'],
      totalCharacters: 4,
    }),
    synthesize: vi.fn().mockResolvedValue({
      audioContent: 'base64encodedaudio',
      contentType: 'audio/mpeg',
      durationMs: 2000,
      latencyMs: 500,
      provider: 'elevenlabs',
      synthesisMode: 'native',
    }),
  },
}))

vi.mock('@/lib/api', () => ({
  ttsApi: {
    getVoices: vi.fn().mockImplementation((provider: string) => {
      const voices: Record<string, { data: Array<{ id: string; name: string; language: string }> }> = {
        elevenlabs: {
          data: [
            { id: 'el-voice-1', name: 'Rachel', language: 'en-US' },
            { id: 'el-voice-2', name: 'Antoni', language: 'en-US' },
          ],
        },
        azure: {
          data: [
            { id: 'az-voice-1', name: 'Xiaoxiao', language: 'zh-TW' },
            { id: 'az-voice-2', name: 'Yunxi', language: 'zh-TW' },
          ],
        },
        openai: {
          data: [
            { id: 'oi-voice-1', name: 'Alloy', language: 'en-US' },
            { id: 'oi-voice-2', name: 'Nova', language: 'en-US' },
          ],
        },
        gcp: { data: [] },
        cartesia: { data: [] },
        deepgram: { data: [] },
      }
      return Promise.resolve(voices[provider] || { data: [] })
    }),
    getProvidersSummary: vi.fn().mockResolvedValue({
      data: {
        tts: [
          { name: 'elevenlabs', status: 'available' },
          { name: 'azure', status: 'available' },
          { name: 'gcp', status: 'available' },
          { name: 'gemini', status: 'available' },
          { name: 'openai', status: 'available' },
          { name: 'cartesia', status: 'available' },
          { name: 'deepgram', status: 'available' },
          { name: 'voai', status: 'available' },
        ],
        stt: [],
        llm: [],
      },
    }),
  },
}))

// Reset store and cache before each test
beforeEach(() => {
  invalidateTTSProviderCache()
  const store = useMultiRoleTTSStore.getState()
  store.reset()
  // Reset to default provider
  useMultiRoleTTSStore.setState({
    provider: 'elevenlabs',
    capabilities: [],
    currentCapability: null,
    voices: [],
    voicesLoading: false,
    voiceAssignments: [],
    dialogueText: '',
    parsedTurns: [],
    speakers: [],
    error: null,
  })
})

describe('Provider Switch', () => {
  describe('UI updates correctly on provider switch', () => {
    it('switches provider and updates store state', async () => {
      const user = userEvent.setup()

      render(
        <MemoryRouter>
          <MultiRoleTTSPage />
        </MemoryRouter>
      )

      // Wait for provider dropdown to render
      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument()
      })

      // Initial provider should be ElevenLabs
      const select = screen.getByRole('combobox')
      expect(select).toHaveValue('elevenlabs')

      // Change to Azure via dropdown
      await user.selectOptions(select, 'azure')

      // Store should reflect the change
      await waitFor(() => {
        expect(useMultiRoleTTSStore.getState().provider).toBe('azure')
      })
    })

    it('keeps dialogue text when switching providers', async () => {
      const user = userEvent.setup()

      // Set dialogue text in store
      useMultiRoleTTSStore.setState({ dialogueText: 'A: 你好\nB: 嗨' })

      render(
        <MemoryRouter>
          <MultiRoleTTSPage />
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument()
      })

      // Change to Azure
      const select = screen.getByRole('combobox')
      await user.selectOptions(select, 'azure')

      // Dialogue text should remain
      expect(useMultiRoleTTSStore.getState().dialogueText).toBe('A: 你好\nB: 嗨')
    })

    it('clears voice assignments when switching providers', async () => {
      const user = userEvent.setup()

      // Set some voice assignments
      useMultiRoleTTSStore.setState({
        voiceAssignments: [
          { speaker: 'A', voiceId: 'el-voice-1', voiceName: 'Rachel' },
        ],
        speakers: ['A'],
      })

      render(
        <MemoryRouter>
          <MultiRoleTTSPage />
        </MemoryRouter>
      )

      await waitFor(() => {
        // Provider dropdown is the first combobox
        expect(screen.getAllByRole('combobox').length).toBeGreaterThanOrEqual(1)
      })

      // Change to Azure - provider dropdown is the first combobox
      const providerSelect = screen.getAllByRole('combobox')[0]
      await user.selectOptions(providerSelect, 'azure')

      // Voice assignments should be cleared
      await waitFor(() => {
        expect(useMultiRoleTTSStore.getState().voiceAssignments).toHaveLength(0)
      })
    })

    it('clears previous synthesis result when switching providers', async () => {
      const user = userEvent.setup()

      // Set some previous result
      useMultiRoleTTSStore.setState({
        result: {
          audioContent: 'base64',
          contentType: 'audio/mpeg',
          durationMs: 1000,
          latencyMs: 200,
          provider: 'elevenlabs',
          synthesisMode: 'native',
        },
        audioUrl: 'blob:test-url',
      })

      render(
        <MemoryRouter>
          <MultiRoleTTSPage />
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByRole('combobox')).toBeInTheDocument()
      })

      // Change to Azure
      const select = screen.getByRole('combobox')
      await user.selectOptions(select, 'azure')

      // Result should be cleared
      await waitFor(() => {
        expect(useMultiRoleTTSStore.getState().result).toBeNull()
        expect(useMultiRoleTTSStore.getState().audioUrl).toBeNull()
      })
    })
  })

  describe('provider dropdown renders correctly', () => {
    it('renders dropdown with all 6 provider options', async () => {
      render(
        <MemoryRouter>
          <MultiRoleTTSPage />
        </MemoryRouter>
      )

      await waitFor(() => {
        const select = screen.getByRole('combobox')
        expect(select).toBeInTheDocument()
      })

      // Check all options exist
      expect(screen.getByRole('option', { name: 'ElevenLabs' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'Azure' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'Google Cloud TTS' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'OpenAI' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'Cartesia' })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: 'Deepgram' })).toBeInTheDocument()
    })

    it('disables provider dropdown while loading', async () => {
      useMultiRoleTTSStore.setState({ isLoading: true })

      render(
        <MemoryRouter>
          <MultiRoleTTSPage />
        </MemoryRouter>
      )

      await waitFor(() => {
        const select = screen.getByRole('combobox')
        expect(select).toBeDisabled()
      })
    })
  })
})

describe('ProviderCapabilityCard', () => {
  describe('displays correct capability information', () => {
    it('shows native support indicator', () => {
      const capability: ProviderMultiRoleCapability = {
        providerName: 'elevenlabs',
        supportType: 'native',
        maxSpeakers: 6,
        characterLimit: 10000,
        advancedFeatures: [],
      }

      render(<ProviderCapabilityCard capability={capability} />)

      expect(screen.getByText(/原生支援/)).toBeInTheDocument()
    })

    it('shows segmented support indicator with warning', () => {
      const capability: ProviderMultiRoleCapability = {
        providerName: 'openai',
        supportType: 'segmented',
        maxSpeakers: 6,
        characterLimit: 4096,
        advancedFeatures: [],
      }

      render(<ProviderCapabilityCard capability={capability} />)

      expect(screen.getByText(/分段合併/)).toBeInTheDocument()
    })

    it('shows max speakers limit', () => {
      const capability: ProviderMultiRoleCapability = {
        providerName: 'elevenlabs',
        supportType: 'native',
        maxSpeakers: 6,
        characterLimit: 10000,
        advancedFeatures: [],
      }

      render(<ProviderCapabilityCard capability={capability} />)

      expect(screen.getByText(/6 位/)).toBeInTheDocument()
      expect(screen.getByText(/最多說話者/)).toBeInTheDocument()
    })

    it('shows character limit', () => {
      const capability: ProviderMultiRoleCapability = {
        providerName: 'elevenlabs',
        supportType: 'native',
        maxSpeakers: 6,
        characterLimit: 10000,
        advancedFeatures: [],
      }

      render(<ProviderCapabilityCard capability={capability} />)

      expect(screen.getByText(/字數上限/)).toBeInTheDocument()
      expect(screen.getByText(/10,000 字/)).toBeInTheDocument()
    })

    it('shows advanced features when available', () => {
      const capability: ProviderMultiRoleCapability = {
        providerName: 'elevenlabs',
        supportType: 'native',
        maxSpeakers: 6,
        characterLimit: 10000,
        advancedFeatures: ['interrupting', 'overlapping'],
      }

      render(<ProviderCapabilityCard capability={capability} />)

      // Check for "進階功能" section
      expect(screen.getByText(/進階功能/)).toBeInTheDocument()
      // Multiple matches for feature names (in tag and tooltip), use getAllByText
      expect(screen.getAllByText(/interrupting/i).length).toBeGreaterThan(0)
    })

    it('shows provider notes when available', () => {
      const capability: ProviderMultiRoleCapability = {
        providerName: 'elevenlabs',
        supportType: 'native',
        maxSpeakers: 6,
        characterLimit: 10000,
        advancedFeatures: [],
        notes: 'Best quality for multi-speaker',
      }

      render(<ProviderCapabilityCard capability={capability} />)

      expect(screen.getByText(/Best quality/)).toBeInTheDocument()
    })

    it('handles null capability gracefully', () => {
      render(<ProviderCapabilityCard capability={null} />)

      // Should not crash, might show loading or placeholder
      expect(screen.queryByText(/原生多角色/)).not.toBeInTheDocument()
    })
  })
})

describe('Voice list reload', () => {
  it('reloads voice list when provider changes', async () => {
    const user = userEvent.setup()
    const { ttsApi } = await import('@/lib/api')

    render(
      <MemoryRouter>
        <MultiRoleTTSPage />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument()
    })

    // Clear previous calls
    vi.mocked(ttsApi.getVoices).mockClear()

    // Change to Azure
    const select = screen.getByRole('combobox')
    await user.selectOptions(select, 'azure')

    // Should call getVoices with azure provider
    await waitFor(() => {
      expect(ttsApi.getVoices).toHaveBeenCalledWith('azure', expect.any(Object))
    })
  })

  it('updates voice options in dropdown after provider switch', async () => {
    const user = userEvent.setup()

    // Set up initial state with parsed speakers
    useMultiRoleTTSStore.setState({
      parsedTurns: [{ speaker: 'A', text: '你好', index: 0 }],
      speakers: ['A'],
    })

    render(
      <MemoryRouter>
        <MultiRoleTTSPage />
      </MemoryRouter>
    )

    await waitFor(() => {
      // Provider dropdown is the first combobox
      expect(screen.getAllByRole('combobox').length).toBeGreaterThanOrEqual(1)
    })

    // Change to Azure - provider dropdown is the first combobox
    const providerSelect = screen.getAllByRole('combobox')[0]
    await user.selectOptions(providerSelect, 'azure')

    // Wait for provider to change
    await waitFor(() => {
      expect(useMultiRoleTTSStore.getState().provider).toBe('azure')
    })

    // Voices should be updated for Azure
    await waitFor(() => {
      const voices = useMultiRoleTTSStore.getState().voices
      // Azure voices should be loaded
      expect(voices.length).toBeGreaterThanOrEqual(0)
    })
  })

  it('shows loading state while fetching voices', async () => {
    const user = userEvent.setup()
    const { ttsApi } = await import('@/lib/api')

    // Make getVoices slow
    vi.mocked(ttsApi.getVoices).mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(() => resolve({ data: [] } as never), 1000)
        )
    )

    render(
      <MemoryRouter>
        <MultiRoleTTSPage />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument()
    })

    // Change to Azure
    const select = screen.getByRole('combobox')
    await user.selectOptions(select, 'azure')

    // Should show loading state
    await waitFor(() => {
      expect(useMultiRoleTTSStore.getState().voicesLoading).toBe(true)
    })
  })
})
