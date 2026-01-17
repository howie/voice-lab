/**
 * Vitest Test Setup
 * Configures testing environment with jest-dom matchers
 */

import '@testing-library/jest-dom'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

// Cleanup after each test
afterEach(() => {
  cleanup()
})

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock ResizeObserver
class ResizeObserverMock {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}

window.ResizeObserver = ResizeObserverMock

// Mock Audio
window.HTMLMediaElement.prototype.load = vi.fn()
window.HTMLMediaElement.prototype.play = vi.fn().mockResolvedValue(undefined)
window.HTMLMediaElement.prototype.pause = vi.fn()

// Mock URL.createObjectURL
URL.createObjectURL = vi.fn(() => 'blob:mock-url')
URL.revokeObjectURL = vi.fn()
