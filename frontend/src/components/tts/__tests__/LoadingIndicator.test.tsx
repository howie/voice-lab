/**
 * LoadingIndicator Component Tests
 * T036: Create frontend component tests
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LoadingIndicator, Spinner } from '../LoadingIndicator'

describe('LoadingIndicator', () => {
  describe('rendering', () => {
    it('renders nothing when isLoading is false', () => {
      const { container } = render(<LoadingIndicator isLoading={false} />)

      expect(container.firstChild).toBeNull()
    })

    it('renders loading UI when isLoading is true', () => {
      render(<LoadingIndicator isLoading={true} />)

      expect(screen.getByText('正在合成語音...')).toBeInTheDocument()
    })

    it('renders custom message', () => {
      render(<LoadingIndicator isLoading={true} message="處理中..." />)

      expect(screen.getByText('處理中...')).toBeInTheDocument()
    })

    it('renders spinner SVG', () => {
      const { container } = render(<LoadingIndicator isLoading={true} />)

      const spinnerSvg = container.querySelector('svg.animate-spin')
      expect(spinnerSvg).toBeInTheDocument()
    })

    it('renders waveform animation bars', () => {
      const { container } = render(<LoadingIndicator isLoading={true} />)

      const animationBars = container.querySelectorAll('.animate-pulse')
      expect(animationBars.length).toBe(5)
    })
  })

  describe('progress bar', () => {
    it('does not render progress bar when progress is undefined', () => {
      const { container } = render(<LoadingIndicator isLoading={true} />)

      const progressBar = container.querySelector('[style*="width"]')
      expect(progressBar).toBeNull()
    })

    it('renders progress bar when progress is provided', () => {
      render(<LoadingIndicator isLoading={true} progress={50} />)

      expect(screen.getByText('50%')).toBeInTheDocument()
    })

    it('shows correct progress percentage', () => {
      render(<LoadingIndicator isLoading={true} progress={75} />)

      expect(screen.getByText('75%')).toBeInTheDocument()
    })

    it('clamps progress to minimum 0%', () => {
      const { container } = render(<LoadingIndicator isLoading={true} progress={-10} />)

      const progressFill = container.querySelector('.bg-primary.h-full')
      expect(progressFill).toHaveStyle({ width: '0%' })
    })

    it('clamps progress to maximum 100%', () => {
      const { container } = render(<LoadingIndicator isLoading={true} progress={150} />)

      const progressFill = container.querySelector('.bg-primary.h-full')
      expect(progressFill).toHaveStyle({ width: '100%' })
    })

    it('rounds progress percentage display', () => {
      render(<LoadingIndicator isLoading={true} progress={33.7} />)

      expect(screen.getByText('34%')).toBeInTheDocument()
    })
  })
})

describe('Spinner', () => {
  describe('rendering', () => {
    it('renders SVG spinner', () => {
      const { container } = render(<Spinner />)

      const svg = container.querySelector('svg')
      expect(svg).toBeInTheDocument()
    })

    it('has animate-spin class', () => {
      const { container } = render(<Spinner />)

      const svg = container.querySelector('svg')
      expect(svg).toHaveClass('animate-spin')
    })

    it('accepts custom className', () => {
      const { container } = render(<Spinner className="h-8 w-8 text-blue-500" />)

      const svg = container.querySelector('svg')
      expect(svg).toHaveClass('h-8')
      expect(svg).toHaveClass('w-8')
      expect(svg).toHaveClass('text-blue-500')
    })

    it('has proper SVG structure', () => {
      const { container } = render(<Spinner />)

      const svg = container.querySelector('svg')
      const circle = svg?.querySelector('circle')
      const path = svg?.querySelector('path')

      expect(circle).toBeInTheDocument()
      expect(path).toBeInTheDocument()
    })
  })
})
