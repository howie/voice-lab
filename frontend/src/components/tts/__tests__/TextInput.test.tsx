/**
 * TextInput Component Tests
 * T036: Create frontend component tests
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { TextInput } from '../TextInput'

describe('TextInput', () => {
  const defaultProps = {
    value: '',
    onChange: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('rendering', () => {
    it('renders textarea with placeholder', () => {
      render(<TextInput {...defaultProps} />)

      const textarea = screen.getByPlaceholderText('請輸入要轉換成語音的文字...')
      expect(textarea).toBeInTheDocument()
    })

    it('renders with custom placeholder', () => {
      render(<TextInput {...defaultProps} placeholder="Custom placeholder" />)

      const textarea = screen.getByPlaceholderText('Custom placeholder')
      expect(textarea).toBeInTheDocument()
    })

    it('displays current value', () => {
      render(<TextInput {...defaultProps} value="Hello world" />)

      const textarea = screen.getByRole('textbox')
      expect(textarea).toHaveValue('Hello world')
    })

    it('shows character count', () => {
      render(<TextInput {...defaultProps} value="Hello" />)

      expect(screen.getByText(/5 \/ 5,000 字/)).toBeInTheDocument()
    })

    it('shows helper text when empty', () => {
      render(<TextInput {...defaultProps} value="" />)

      expect(screen.getByText('輸入文字開始合成')).toBeInTheDocument()
    })
  })

  describe('user interaction', () => {
    it('calls onChange when typing', async () => {
      const onChange = vi.fn()
      render(<TextInput {...defaultProps} onChange={onChange} />)

      const textarea = screen.getByRole('textbox')
      await userEvent.type(textarea, 'a')

      expect(onChange).toHaveBeenCalledWith('a')
    })

    it('prevents input when max length is reached', () => {
      const onChange = vi.fn()
      const maxValue = 'ab' // 2 characters
      render(<TextInput {...defaultProps} value={maxValue} onChange={onChange} maxLength={2} />)

      const textarea = screen.getByRole('textbox')
      fireEvent.change(textarea, { target: { value: 'abc' } }) // Try to add one more

      expect(onChange).not.toHaveBeenCalled()
    })

    it('allows input when under max length', () => {
      const onChange = vi.fn()
      render(<TextInput {...defaultProps} value="" onChange={onChange} maxLength={10} />)

      const textarea = screen.getByRole('textbox')
      fireEvent.change(textarea, { target: { value: 'test' } })

      expect(onChange).toHaveBeenCalledWith('test')
    })
  })

  describe('character limit indicators', () => {
    it('applies warning style near limit (90%)', () => {
      // 90% of 100 = 90 characters
      const nearLimitText = 'a'.repeat(90)
      render(<TextInput {...defaultProps} value={nearLimitText} maxLength={100} />)

      const countElement = screen.getByText(/90 \/ 100 字/)
      expect(countElement).toHaveClass('text-yellow-600')
    })

    it('applies error style at limit', () => {
      const atLimitText = 'a'.repeat(100)
      render(<TextInput {...defaultProps} value={atLimitText} maxLength={100} />)

      const countElement = screen.getByText(/100 \/ 100 字/)
      expect(countElement).toHaveClass('text-destructive')
    })

    it('applies normal style under 90%', () => {
      const normalText = 'a'.repeat(50)
      render(<TextInput {...defaultProps} value={normalText} maxLength={100} />)

      const countElement = screen.getByText(/50 \/ 100 字/)
      expect(countElement).toHaveClass('text-muted-foreground')
    })
  })

  describe('disabled state', () => {
    it('disables textarea when disabled prop is true', () => {
      render(<TextInput {...defaultProps} disabled />)

      const textarea = screen.getByRole('textbox')
      expect(textarea).toBeDisabled()
    })

    it('does not call onChange when disabled', async () => {
      const onChange = vi.fn()
      render(<TextInput {...defaultProps} onChange={onChange} disabled />)

      const textarea = screen.getByRole('textbox')
      await userEvent.type(textarea, 'test')

      expect(onChange).not.toHaveBeenCalled()
    })
  })

  describe('accessibility', () => {
    it('textarea is focusable', () => {
      render(<TextInput {...defaultProps} />)

      const textarea = screen.getByRole('textbox')
      textarea.focus()

      expect(document.activeElement).toBe(textarea)
    })
  })
})
