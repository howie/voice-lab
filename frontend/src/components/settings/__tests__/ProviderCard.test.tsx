/**
 * ProviderCard Component Tests
 * T080: Frontend tests for ProviderSettings components
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ProviderCard } from '../ProviderCard'
import type { Provider, CredentialSummary } from '../../../services/credentialService'

// Mock the child components
vi.mock('../ModelSelector', () => ({
  ModelSelector: vi.fn(({ onSelect }) => (
    <div data-testid="model-selector">
      <button onClick={() => onSelect('model-1')}>Select Model</button>
    </div>
  )),
}))

describe('ProviderCard', () => {
  const mockProvider: Provider = {
    id: 'elevenlabs',
    name: 'elevenlabs',
    display_name: 'ElevenLabs',
    type: ['tts'],
    is_active: true,
  }

  const mockCredential: CredentialSummary = {
    id: 'cred-123',
    provider: 'elevenlabs',
    provider_display_name: 'ElevenLabs',
    masked_key: '****abc1',
    is_valid: true,
    selected_model_id: null,
    last_validated_at: '2024-01-15T10:30:00Z',
    created_at: '2024-01-01T00:00:00Z',
  }

  const defaultProps = {
    provider: mockProvider,
    credential: null,
    onAddKey: vi.fn().mockResolvedValue(undefined),
    onUpdateKey: vi.fn().mockResolvedValue(undefined),
    onDeleteKey: vi.fn().mockResolvedValue(undefined),
    onValidateKey: vi.fn().mockResolvedValue(null),
    onSelectModel: vi.fn().mockResolvedValue(undefined),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('rendering without credential', () => {
    it('renders provider name and type', () => {
      render(<ProviderCard {...defaultProps} />)

      expect(screen.getByText('ElevenLabs')).toBeInTheDocument()
      // Type is rendered in lowercase with uppercase CSS class
      expect(screen.getByText('tts')).toBeInTheDocument()
    })

    it('shows "Not configured" status', () => {
      render(<ProviderCard {...defaultProps} />)

      expect(screen.getByText('Not configured')).toBeInTheDocument()
    })

    it('renders provider badge with first letter', () => {
      render(<ProviderCard {...defaultProps} />)

      expect(screen.getByText('E')).toBeInTheDocument()
    })
  })

  describe('rendering with valid credential', () => {
    it('shows "Connected" status badge', () => {
      render(<ProviderCard {...defaultProps} credential={mockCredential} />)

      expect(screen.getByText('Connected')).toBeInTheDocument()
    })

    it('shows masked API key when expanded', async () => {
      render(<ProviderCard {...defaultProps} credential={mockCredential} />)

      // Click to expand
      const header = screen.getByText('ElevenLabs')
      await userEvent.click(header)

      expect(screen.getByText('****abc1')).toBeInTheDocument()
    })

    it('shows action buttons when expanded', async () => {
      render(<ProviderCard {...defaultProps} credential={mockCredential} />)

      await userEvent.click(screen.getByText('ElevenLabs'))

      expect(screen.getByText('Validate')).toBeInTheDocument()
      expect(screen.getByText('Update Key')).toBeInTheDocument()
      expect(screen.getByText('Delete')).toBeInTheDocument()
    })

    it('shows model selector when valid', async () => {
      render(<ProviderCard {...defaultProps} credential={mockCredential} />)

      await userEvent.click(screen.getByText('ElevenLabs'))

      expect(screen.getByTestId('model-selector')).toBeInTheDocument()
    })
  })

  describe('rendering with invalid credential', () => {
    const invalidCredential = { ...mockCredential, is_valid: false }

    it('shows "Invalid" status badge', () => {
      render(<ProviderCard {...defaultProps} credential={invalidCredential} />)

      expect(screen.getByText('Invalid')).toBeInTheDocument()
    })

    it('does not show model selector', async () => {
      render(<ProviderCard {...defaultProps} credential={invalidCredential} />)

      await userEvent.click(screen.getByText('ElevenLabs'))

      expect(screen.queryByTestId('model-selector')).not.toBeInTheDocument()
    })
  })

  describe('expand/collapse behavior', () => {
    it('expands when clicking header', async () => {
      render(<ProviderCard {...defaultProps} />)

      // Initially collapsed - API key input should not be visible
      expect(screen.queryByPlaceholderText(/enter your/i)).not.toBeInTheDocument()

      await userEvent.click(screen.getByText('ElevenLabs'))

      // Now expanded - API key input should be visible
      expect(
        screen.getByPlaceholderText('Enter your ElevenLabs API key')
      ).toBeInTheDocument()
    })

    it('collapses when clicking header again', async () => {
      render(<ProviderCard {...defaultProps} />)

      // Expand
      await userEvent.click(screen.getByText('ElevenLabs'))
      expect(
        screen.getByPlaceholderText('Enter your ElevenLabs API key')
      ).toBeInTheDocument()

      // Collapse
      await userEvent.click(screen.getByText('ElevenLabs'))
      expect(
        screen.queryByPlaceholderText('Enter your ElevenLabs API key')
      ).not.toBeInTheDocument()
    })
  })

  describe('add API key flow', () => {
    it('calls onAddKey when submitting new key', async () => {
      const onAddKey = vi.fn().mockResolvedValue(undefined)
      render(<ProviderCard {...defaultProps} onAddKey={onAddKey} />)

      // Expand
      await userEvent.click(screen.getByText('ElevenLabs'))

      // Enter API key
      const input = screen.getByPlaceholderText('Enter your ElevenLabs API key')
      await userEvent.type(input, 'new-api-key')

      // Submit
      await userEvent.click(screen.getByText('Save & Validate'))

      await waitFor(() => {
        expect(onAddKey).toHaveBeenCalledWith('elevenlabs', 'new-api-key')
      })
    })

    it('disables submit button when key is empty', async () => {
      render(<ProviderCard {...defaultProps} />)

      // Expand
      await userEvent.click(screen.getByText('ElevenLabs'))

      // Submit button should be disabled when input is empty
      const submitButton = screen.getByText('Save & Validate')
      expect(submitButton).toBeDisabled()
    })
  })

  describe('validate credential', () => {
    it('calls onValidateKey when clicking Validate', async () => {
      const onValidateKey = vi.fn().mockResolvedValue({ tier: 'free' })
      render(
        <ProviderCard
          {...defaultProps}
          credential={mockCredential}
          onValidateKey={onValidateKey}
        />
      )

      await userEvent.click(screen.getByText('ElevenLabs'))
      await userEvent.click(screen.getByText('Validate'))

      await waitFor(() => {
        expect(onValidateKey).toHaveBeenCalledWith('cred-123')
      })
    })

    it('displays quota info after validation', async () => {
      const onValidateKey = vi.fn().mockResolvedValue({
        tier: 'free',
        character_limit: 10000,
        character_count: 5000,
      })
      render(
        <ProviderCard
          {...defaultProps}
          credential={mockCredential}
          onValidateKey={onValidateKey}
        />
      )

      await userEvent.click(screen.getByText('ElevenLabs'))
      await userEvent.click(screen.getByText('Validate'))

      await waitFor(() => {
        expect(screen.getByText('Usage Quota')).toBeInTheDocument()
        expect(screen.getByText('free')).toBeInTheDocument()
      })
    })
  })

  describe('update API key flow', () => {
    it('shows update form when clicking Update Key', async () => {
      render(<ProviderCard {...defaultProps} credential={mockCredential} />)

      await userEvent.click(screen.getByText('ElevenLabs'))
      await userEvent.click(screen.getByText('Update Key'))

      expect(
        screen.getByPlaceholderText('Enter your ElevenLabs API key')
      ).toBeInTheDocument()
      expect(screen.getByText('Update')).toBeInTheDocument()
      expect(screen.getByText('Cancel')).toBeInTheDocument()
    })

    it('calls onUpdateKey when submitting updated key', async () => {
      const onUpdateKey = vi.fn().mockResolvedValue(undefined)
      render(
        <ProviderCard
          {...defaultProps}
          credential={mockCredential}
          onUpdateKey={onUpdateKey}
        />
      )

      await userEvent.click(screen.getByText('ElevenLabs'))
      await userEvent.click(screen.getByText('Update Key'))

      const input = screen.getByPlaceholderText('Enter your ElevenLabs API key')
      await userEvent.type(input, 'updated-key')
      await userEvent.click(screen.getByText('Update'))

      await waitFor(() => {
        expect(onUpdateKey).toHaveBeenCalledWith('cred-123', 'updated-key')
      })
    })

    it('cancels update when clicking Cancel', async () => {
      render(<ProviderCard {...defaultProps} credential={mockCredential} />)

      await userEvent.click(screen.getByText('ElevenLabs'))
      await userEvent.click(screen.getByText('Update Key'))

      // Verify we're in edit mode
      expect(screen.getByText('Cancel')).toBeInTheDocument()

      await userEvent.click(screen.getByText('Cancel'))

      // Should be back to view mode
      expect(screen.queryByText('Cancel')).not.toBeInTheDocument()
      expect(screen.getByText('Update Key')).toBeInTheDocument()
    })
  })

  describe('delete credential', () => {
    it('shows confirmation when clicking Delete', async () => {
      render(<ProviderCard {...defaultProps} credential={mockCredential} />)

      await userEvent.click(screen.getByText('ElevenLabs'))
      await userEvent.click(screen.getByText('Delete'))

      expect(screen.getByText('Delete this key?')).toBeInTheDocument()
      expect(screen.getByText('Yes')).toBeInTheDocument()
      expect(screen.getByText('No')).toBeInTheDocument()
    })

    it('calls onDeleteKey when confirming delete', async () => {
      const onDeleteKey = vi.fn().mockResolvedValue(undefined)
      render(
        <ProviderCard
          {...defaultProps}
          credential={mockCredential}
          onDeleteKey={onDeleteKey}
        />
      )

      await userEvent.click(screen.getByText('ElevenLabs'))
      await userEvent.click(screen.getByText('Delete'))
      await userEvent.click(screen.getByText('Yes'))

      await waitFor(() => {
        expect(onDeleteKey).toHaveBeenCalledWith('cred-123')
      })
    })

    it('cancels delete when clicking No', async () => {
      render(<ProviderCard {...defaultProps} credential={mockCredential} />)

      await userEvent.click(screen.getByText('ElevenLabs'))
      await userEvent.click(screen.getByText('Delete'))

      // Verify confirmation is shown
      expect(screen.getByText('Delete this key?')).toBeInTheDocument()

      await userEvent.click(screen.getByText('No'))

      // Confirmation should be hidden
      expect(screen.queryByText('Delete this key?')).not.toBeInTheDocument()
      expect(screen.getByText('Delete')).toBeInTheDocument()
    })
  })

  describe('model selection', () => {
    it('calls onSelectModel when selecting a model', async () => {
      const onSelectModel = vi.fn().mockResolvedValue(undefined)
      render(
        <ProviderCard
          {...defaultProps}
          credential={mockCredential}
          onSelectModel={onSelectModel}
        />
      )

      await userEvent.click(screen.getByText('ElevenLabs'))
      await userEvent.click(screen.getByText('Select Model'))

      await waitFor(() => {
        expect(onSelectModel).toHaveBeenCalledWith('cred-123', 'model-1')
      })
    })
  })

  describe('loading state', () => {
    it('applies loading styles when isLoading is true', () => {
      render(<ProviderCard {...defaultProps} isLoading />)

      const card = screen.getByText('ElevenLabs').closest('div[class*="rounded-lg"]')
      expect(card).toHaveClass('opacity-50')
    })
  })
})
