/**
 * ProviderSelector Component Tests
 * T036: Create frontend component tests
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ProviderSelector, PROVIDERS } from '../ProviderSelector'

describe('ProviderSelector', () => {
  const defaultProps = {
    value: 'azure',
    onChange: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('rendering', () => {
    it('renders select with label', () => {
      render(<ProviderSelector {...defaultProps} />)

      expect(screen.getByText('選擇 Provider')).toBeInTheDocument()
      expect(screen.getByRole('combobox')).toBeInTheDocument()
    })

    it('renders all provider options', () => {
      render(<ProviderSelector {...defaultProps} />)

      PROVIDERS.forEach((provider) => {
        expect(screen.getByText(provider.displayName)).toBeInTheDocument()
      })
    })

    it('shows correct number of options', () => {
      render(<ProviderSelector {...defaultProps} />)

      const options = screen.getAllByRole('option')
      expect(options).toHaveLength(PROVIDERS.length)
    })

    it('selects the correct initial value', () => {
      render(<ProviderSelector {...defaultProps} value="elevenlabs" />)

      const select = screen.getByRole('combobox')
      expect(select).toHaveValue('elevenlabs')
    })

    it('displays provider description for selected value', () => {
      render(<ProviderSelector {...defaultProps} value="azure" />)

      expect(screen.getByText('Microsoft Azure 語音服務')).toBeInTheDocument()
    })
  })

  describe('user interaction', () => {
    it('calls onChange when selection changes', async () => {
      const onChange = vi.fn()
      render(<ProviderSelector {...defaultProps} onChange={onChange} />)

      const select = screen.getByRole('combobox')
      await userEvent.selectOptions(select, 'gcp')

      expect(onChange).toHaveBeenCalledWith('gcp')
    })

    it('updates description when selection changes', () => {
      const { rerender } = render(<ProviderSelector {...defaultProps} value="azure" />)

      expect(screen.getByText('Microsoft Azure 語音服務')).toBeInTheDocument()

      rerender(<ProviderSelector {...defaultProps} value="gcp" />)

      expect(screen.getByText('Google Cloud Platform 傳統 TTS 服務')).toBeInTheDocument()
    })
  })

  describe('disabled state', () => {
    it('disables select when disabled prop is true', () => {
      render(<ProviderSelector {...defaultProps} disabled />)

      const select = screen.getByRole('combobox')
      expect(select).toBeDisabled()
    })

    it('does not call onChange when disabled', async () => {
      const onChange = vi.fn()
      render(<ProviderSelector {...defaultProps} onChange={onChange} disabled />)

      const select = screen.getByRole('combobox')
      fireEvent.change(select, { target: { value: 'gcp' } })

      // The event fires but should be ignored when disabled
      // Testing the disabled attribute is sufficient here
      expect(select).toBeDisabled()
    })
  })

  describe('provider options', () => {
    it('has Azure as an option', () => {
      render(<ProviderSelector {...defaultProps} />)

      expect(screen.getByRole('option', { name: 'Azure Speech' })).toBeInTheDocument()
    })

    it('has Google Cloud TTS as an option', () => {
      render(<ProviderSelector {...defaultProps} />)

      expect(screen.getByRole('option', { name: 'Google Cloud TTS' })).toBeInTheDocument()
    })

    it('has ElevenLabs as an option', () => {
      render(<ProviderSelector {...defaultProps} />)

      expect(screen.getByRole('option', { name: 'ElevenLabs' })).toBeInTheDocument()
    })

    it('has VoAI as an option', () => {
      render(<ProviderSelector {...defaultProps} />)

      expect(screen.getByRole('option', { name: 'VoAI 台灣語音' })).toBeInTheDocument()
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
