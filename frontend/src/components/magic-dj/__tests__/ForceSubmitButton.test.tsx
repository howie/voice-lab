/**
 * ForceSubmitButton Tests
 * Feature: 010-magic-dj-controller
 *
 * T012: Unit tests for ForceSubmitButton covering click, disabled state, visual feedback.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'

import { ForceSubmitButton } from '../ForceSubmitButton'

describe('ForceSubmitButton', () => {
  describe('rendering', () => {
    it('should render the button with label', () => {
      render(<ForceSubmitButton onClick={vi.fn()} />)
      expect(screen.getByText('強制送出')).toBeInTheDocument()
    })

    it('should show Space hotkey hint', () => {
      render(<ForceSubmitButton onClick={vi.fn()} />)
      expect(screen.getByText('Space')).toBeInTheDocument()
    })
  })

  describe('click handling', () => {
    it('should call onClick when clicked', () => {
      const handleClick = vi.fn()
      render(<ForceSubmitButton onClick={handleClick} />)

      fireEvent.click(screen.getByRole('button'))
      expect(handleClick).toHaveBeenCalledTimes(1)
    })

    it('should not call onClick when disabled', () => {
      const handleClick = vi.fn()
      render(<ForceSubmitButton onClick={handleClick} disabled />)

      fireEvent.click(screen.getByRole('button'))
      expect(handleClick).not.toHaveBeenCalled()
    })
  })

  describe('disabled state', () => {
    it('should have disabled attribute when disabled', () => {
      render(<ForceSubmitButton onClick={vi.fn()} disabled />)
      expect(screen.getByRole('button')).toBeDisabled()
    })

    it('should not have disabled attribute by default', () => {
      render(<ForceSubmitButton onClick={vi.fn()} />)
      expect(screen.getByRole('button')).not.toBeDisabled()
    })
  })
})
