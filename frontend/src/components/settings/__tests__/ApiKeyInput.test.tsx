/**
 * ApiKeyInput Component Tests
 * T080: Frontend tests for ProviderSettings components
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ApiKeyInput } from '../ApiKeyInput'

describe('ApiKeyInput', () => {
  const defaultProps = {
    value: '',
    onChange: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('rendering', () => {
    it('renders input with default placeholder', () => {
      render(<ApiKeyInput {...defaultProps} />)

      const input = screen.getByPlaceholderText('Enter your API key')
      expect(input).toBeInTheDocument()
    })

    it('renders with custom placeholder', () => {
      render(<ApiKeyInput {...defaultProps} placeholder="Custom placeholder" />)

      const input = screen.getByPlaceholderText('Custom placeholder')
      expect(input).toBeInTheDocument()
    })

    it('displays current value', () => {
      render(<ApiKeyInput {...defaultProps} value="test-api-key" />)

      const input = screen.getByDisplayValue('test-api-key')
      expect(input).toBeInTheDocument()
    })

    it('shows password type by default', () => {
      render(<ApiKeyInput {...defaultProps} value="secret" />)

      const input = screen.getByDisplayValue('secret')
      expect(input).toHaveAttribute('type', 'password')
    })

    it('shows security message', () => {
      render(<ApiKeyInput {...defaultProps} />)

      expect(
        screen.getByText('Your API key is encrypted and stored securely.')
      ).toBeInTheDocument()
    })
  })

  describe('show/hide toggle', () => {
    it('toggles input type when clicking show button', async () => {
      render(<ApiKeyInput {...defaultProps} value="secret-key" />)

      const input = screen.getByDisplayValue('secret-key')
      expect(input).toHaveAttribute('type', 'password')

      const toggleButton = screen.getByRole('button', { name: /show api key/i })
      await userEvent.click(toggleButton)

      expect(input).toHaveAttribute('type', 'text')
    })

    it('changes aria-label when toggled', async () => {
      render(<ApiKeyInput {...defaultProps} />)

      const toggleButton = screen.getByRole('button', { name: /show api key/i })
      await userEvent.click(toggleButton)

      expect(toggleButton).toHaveAttribute('aria-label', 'Hide API key')
    })
  })

  describe('user interaction', () => {
    it('calls onChange when typing', async () => {
      const onChange = vi.fn()
      render(<ApiKeyInput {...defaultProps} onChange={onChange} />)

      const input = screen.getByPlaceholderText('Enter your API key')
      await userEvent.type(input, 'a')

      expect(onChange).toHaveBeenCalledWith('a')
    })

    it('enforces max length', () => {
      const onChange = vi.fn()
      render(
        <ApiKeyInput {...defaultProps} value="ab" onChange={onChange} maxLength={2} />
      )

      const input = screen.getByDisplayValue('ab')
      fireEvent.change(input, { target: { value: 'abc' } })

      expect(onChange).not.toHaveBeenCalled()
    })

    it('calls onSubmit when pressing Enter', async () => {
      const onSubmit = vi.fn()
      render(<ApiKeyInput {...defaultProps} value="key" onSubmit={onSubmit} />)

      const input = screen.getByDisplayValue('key')
      await userEvent.type(input, '{enter}')

      expect(onSubmit).toHaveBeenCalled()
    })

    it('does not call onSubmit when disabled', async () => {
      const onSubmit = vi.fn()
      render(
        <ApiKeyInput {...defaultProps} value="key" onSubmit={onSubmit} disabled />
      )

      const input = screen.getByDisplayValue('key')
      fireEvent.keyDown(input, { key: 'Enter' })

      expect(onSubmit).not.toHaveBeenCalled()
    })

    it('does not call onSubmit when validating', async () => {
      const onSubmit = vi.fn()
      render(
        <ApiKeyInput
          {...defaultProps}
          value="key"
          onSubmit={onSubmit}
          isValidating
        />
      )

      const input = screen.getByDisplayValue('key')
      fireEvent.keyDown(input, { key: 'Enter' })

      expect(onSubmit).not.toHaveBeenCalled()
    })
  })

  describe('error state', () => {
    it('displays error message', () => {
      render(<ApiKeyInput {...defaultProps} error="Invalid API key" />)

      expect(screen.getByText('Invalid API key')).toBeInTheDocument()
    })

    it('applies error styling to input', () => {
      render(<ApiKeyInput {...defaultProps} error="Error" />)

      const input = screen.getByPlaceholderText('Enter your API key')
      expect(input).toHaveClass('border-destructive')
    })
  })

  describe('loading state', () => {
    it('shows loading indicator when validating', () => {
      render(<ApiKeyInput {...defaultProps} isValidating />)

      // Loader2 component renders with animate-spin class
      const loader = document.querySelector('.animate-spin')
      expect(loader).toBeInTheDocument()
    })

    it('disables input when validating', () => {
      render(<ApiKeyInput {...defaultProps} isValidating />)

      const input = screen.getByPlaceholderText('Enter your API key')
      expect(input).toBeDisabled()
    })
  })

  describe('disabled state', () => {
    it('disables input when disabled prop is true', () => {
      render(<ApiKeyInput {...defaultProps} disabled />)

      const input = screen.getByPlaceholderText('Enter your API key')
      expect(input).toBeDisabled()
    })

    it('disables toggle button when disabled', () => {
      render(<ApiKeyInput {...defaultProps} disabled />)

      const toggleButton = screen.getByRole('button')
      expect(toggleButton).toBeDisabled()
    })
  })

  describe('accessibility', () => {
    it('input is focusable', () => {
      render(<ApiKeyInput {...defaultProps} />)

      const input = screen.getByPlaceholderText('Enter your API key')
      input.focus()

      expect(document.activeElement).toBe(input)
    })

    it('has correct autocomplete attribute', () => {
      render(<ApiKeyInput {...defaultProps} />)

      const input = screen.getByPlaceholderText('Enter your API key')
      expect(input).toHaveAttribute('autocomplete', 'off')
    })

    it('has spellcheck disabled', () => {
      render(<ApiKeyInput {...defaultProps} />)

      const input = screen.getByPlaceholderText('Enter your API key')
      expect(input).toHaveAttribute('spellcheck', 'false')
    })
  })
})
