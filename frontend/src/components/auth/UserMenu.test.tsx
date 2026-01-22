/**
 * UserMenu Component Tests
 * Tests for null-safety and edge cases in user initials calculation
 */

import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { UserMenu } from './UserMenu'

// Mock the auth store
const mockLogout = vi.fn()
const mockUseAuthStore = vi.fn()

vi.mock('@/stores/authStore', () => ({
  useAuthStore: () => mockUseAuthStore(),
}))

// Mock SettingsDialog
vi.mock('@/components/settings/SettingsDialog', () => ({
  SettingsDialog: () => null,
}))

describe('UserMenu', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('initials calculation', () => {
    it('returns null when user is null', () => {
      mockUseAuthStore.mockReturnValue({
        user: null,
        logout: mockLogout,
        isLoading: false,
      })

      const { container } = render(<UserMenu />)
      expect(container.firstChild).toBeNull()
    })

    it('displays initials from user name when name has multiple words', () => {
      mockUseAuthStore.mockReturnValue({
        user: {
          id: '1',
          email: 'john.doe@example.com',
          name: 'John Doe',
          picture_url: undefined,
        },
        logout: mockLogout,
        isLoading: false,
      })

      render(<UserMenu />)
      expect(screen.getByText('JD')).toBeInTheDocument()
    })

    it('displays first letter of email when name is undefined', () => {
      mockUseAuthStore.mockReturnValue({
        user: {
          id: '1',
          email: 'test@example.com',
          name: undefined,
          picture_url: undefined,
        },
        logout: mockLogout,
        isLoading: false,
      })

      render(<UserMenu />)
      expect(screen.getByText('T')).toBeInTheDocument()
    })

    it('displays first letter of email when name is empty string', () => {
      mockUseAuthStore.mockReturnValue({
        user: {
          id: '1',
          email: 'alice@example.com',
          name: '',
          picture_url: undefined,
        },
        logout: mockLogout,
        isLoading: false,
      })

      render(<UserMenu />)
      expect(screen.getByText('A')).toBeInTheDocument()
    })

    it('displays fallback "U" when email is undefined', () => {
      mockUseAuthStore.mockReturnValue({
        user: {
          id: '1',
          email: undefined,
          name: undefined,
          picture_url: undefined,
        },
        logout: mockLogout,
        isLoading: false,
      })

      render(<UserMenu />)
      expect(screen.getByText('U')).toBeInTheDocument()
    })

    it('displays fallback "U" when email is empty string', () => {
      mockUseAuthStore.mockReturnValue({
        user: {
          id: '1',
          email: '',
          name: '',
          picture_url: undefined,
        },
        logout: mockLogout,
        isLoading: false,
      })

      render(<UserMenu />)
      expect(screen.getByText('U')).toBeInTheDocument()
    })

    it('displays single letter initial for single word name', () => {
      mockUseAuthStore.mockReturnValue({
        user: {
          id: '1',
          email: 'alice@example.com',
          name: 'Alice',
          picture_url: undefined,
        },
        logout: mockLogout,
        isLoading: false,
      })

      render(<UserMenu />)
      expect(screen.getByText('A')).toBeInTheDocument()
    })

    it('handles name with multiple spaces correctly', () => {
      mockUseAuthStore.mockReturnValue({
        user: {
          id: '1',
          email: 'test@example.com',
          name: 'John  Middle  Doe',
          picture_url: undefined,
        },
        logout: mockLogout,
        isLoading: false,
      })

      render(<UserMenu />)
      // Should filter out empty strings from split and take first 2 initials
      expect(screen.getByText('JM')).toBeInTheDocument()
    })

    it('handles name with only spaces (edge case)', () => {
      mockUseAuthStore.mockReturnValue({
        user: {
          id: '1',
          email: 'test@example.com',
          name: '   ',
          picture_url: undefined,
        },
        logout: mockLogout,
        isLoading: false,
      })

      render(<UserMenu />)
      // Empty name after trim should fallback to email initial
      expect(screen.getByText('U')).toBeInTheDocument()
    })

    it('displays user avatar when picture_url is provided', () => {
      mockUseAuthStore.mockReturnValue({
        user: {
          id: '1',
          email: 'test@example.com',
          name: 'Test User',
          picture_url: 'https://example.com/avatar.jpg',
        },
        logout: mockLogout,
        isLoading: false,
      })

      render(<UserMenu />)
      const avatar = screen.getByRole('img')
      expect(avatar).toHaveAttribute('src', 'https://example.com/avatar.jpg')
    })

    it('truncates initials to maximum 2 characters', () => {
      mockUseAuthStore.mockReturnValue({
        user: {
          id: '1',
          email: 'test@example.com',
          name: 'John Michael Smith Jr',
          picture_url: undefined,
        },
        logout: mockLogout,
        isLoading: false,
      })

      render(<UserMenu />)
      expect(screen.getByText('JM')).toBeInTheDocument()
    })
  })
})
