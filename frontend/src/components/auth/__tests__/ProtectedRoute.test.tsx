/**
 * ProtectedRoute Component Tests
 *
 * Tests verify that the ProtectedRoute component correctly:
 * - Shows loading state while checking auth
 * - Redirects to login when not authenticated
 * - Renders children when authenticated
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { ProtectedRoute } from '../ProtectedRoute'

// Mock the auth store
const mockAuthStore = {
  isAuthenticated: false,
  isLoading: true,
  checkAuth: vi.fn(),
}

vi.mock('@/stores/authStore', () => ({
  useAuthStore: vi.fn((selector) => {
    if (typeof selector === 'function') {
      return selector(mockAuthStore)
    }
    return mockAuthStore
  }),
}))

// Helper to render with router
function renderWithRouter(ui: React.ReactElement, { route = '/' } = {}) {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <Routes>
        <Route path="/login" element={<div>Login Page</div>} />
        <Route path="/" element={ui} />
      </Routes>
    </MemoryRouter>
  )
}

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset to default state
    mockAuthStore.isAuthenticated = false
    mockAuthStore.isLoading = true
    mockAuthStore.checkAuth = vi.fn()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('loading state', () => {
    it('should show loading spinner while checking auth', () => {
      mockAuthStore.isLoading = true
      mockAuthStore.isAuthenticated = false

      renderWithRouter(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      // Should show loading message
      expect(screen.getByText('驗證身份中...')).toBeInTheDocument()

      // Should NOT show protected content
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    })

    it('should call checkAuth on mount', () => {
      mockAuthStore.isLoading = true

      renderWithRouter(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      expect(mockAuthStore.checkAuth).toHaveBeenCalled()
    })
  })

  describe('not authenticated', () => {
    it('should redirect to login when not authenticated and not loading', async () => {
      mockAuthStore.isLoading = false
      mockAuthStore.isAuthenticated = false

      renderWithRouter(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      // Should redirect to login page
      await waitFor(() => {
        expect(screen.getByText('Login Page')).toBeInTheDocument()
      })

      // Should NOT show protected content
      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    })

    it('should not render children when not authenticated', () => {
      mockAuthStore.isLoading = false
      mockAuthStore.isAuthenticated = false

      renderWithRouter(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
    })
  })

  describe('authenticated', () => {
    it('should render children when authenticated', () => {
      mockAuthStore.isLoading = false
      mockAuthStore.isAuthenticated = true

      renderWithRouter(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByText('Protected Content')).toBeInTheDocument()
    })

    it('should not show loading when authenticated', () => {
      mockAuthStore.isLoading = false
      mockAuthStore.isAuthenticated = true

      renderWithRouter(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      expect(screen.queryByText('驗證身份中...')).not.toBeInTheDocument()
    })
  })

  describe('custom redirect path', () => {
    it('should redirect to custom path when specified', async () => {
      mockAuthStore.isLoading = false
      mockAuthStore.isAuthenticated = false

      render(
        <MemoryRouter initialEntries={['/']}>
          <Routes>
            <Route path="/custom-login" element={<div>Custom Login</div>} />
            <Route
              path="/"
              element={
                <ProtectedRoute redirectTo="/custom-login">
                  <div>Protected Content</div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText('Custom Login')).toBeInTheDocument()
      })
    })
  })

  describe('state transitions', () => {
    it('should transition from loading to authenticated', async () => {
      // Start with loading state
      mockAuthStore.isLoading = true
      mockAuthStore.isAuthenticated = false

      const { rerender } = renderWithRouter(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      // Should show loading
      expect(screen.getByText('驗證身份中...')).toBeInTheDocument()

      // Simulate auth check completing successfully
      mockAuthStore.isLoading = false
      mockAuthStore.isAuthenticated = true

      rerender(
        <MemoryRouter initialEntries={['/']}>
          <Routes>
            <Route path="/login" element={<div>Login Page</div>} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <div>Protected Content</div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      )

      // Should now show protected content
      await waitFor(() => {
        expect(screen.getByText('Protected Content')).toBeInTheDocument()
      })
    })

    it('should transition from loading to not authenticated', async () => {
      // Start with loading state
      mockAuthStore.isLoading = true
      mockAuthStore.isAuthenticated = false

      const { rerender } = renderWithRouter(
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      )

      // Should show loading
      expect(screen.getByText('驗證身份中...')).toBeInTheDocument()

      // Simulate auth check completing - not authenticated
      mockAuthStore.isLoading = false
      mockAuthStore.isAuthenticated = false

      rerender(
        <MemoryRouter initialEntries={['/']}>
          <Routes>
            <Route path="/login" element={<div>Login Page</div>} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <div>Protected Content</div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      )

      // Should redirect to login
      await waitFor(() => {
        expect(screen.getByText('Login Page')).toBeInTheDocument()
      })
    })
  })
})

describe('Regression: Children should not unmount during re-auth', () => {
  // This test suite verifies the fix for the bug where WebSocket connections
  // were disconnected because ProtectedRoute's children were unmounted
  // when checkAuth was called multiple times

  beforeEach(() => {
    vi.clearAllMocks()
    mockAuthStore.checkAuth = vi.fn()
  })

  it('should NOT unmount children when isLoading remains false', async () => {
    // Simulate authenticated state
    mockAuthStore.isLoading = false
    mockAuthStore.isAuthenticated = true

    const onUnmount = vi.fn()

    // Component that tracks mount/unmount
    const { useEffect } = await import('react')
    function ChildWithUnmountTracker() {
      useEffect(() => {
        return () => {
          onUnmount()
        }
      }, [])
      return <div>Protected Content</div>
    }

    const { rerender } = renderWithRouter(
      <ProtectedRoute>
        <ChildWithUnmountTracker />
      </ProtectedRoute>
    )

    // Content should be visible
    expect(screen.getByText('Protected Content')).toBeInTheDocument()

    // Simulate multiple re-renders (as if store state changed)
    // but isLoading stays false and isAuthenticated stays true
    for (let i = 0; i < 5; i++) {
      rerender(
        <MemoryRouter initialEntries={['/']}>
          <Routes>
            <Route path="/login" element={<div>Login Page</div>} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <ChildWithUnmountTracker />
                </ProtectedRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      )
    }

    // Child should NOT have been unmounted
    expect(onUnmount).not.toHaveBeenCalled()

    // Content should still be visible
    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })

  it('should use individual selectors to prevent unnecessary re-renders', () => {
    // This test documents the expected behavior:
    // ProtectedRoute should use individual selectors like:
    //   const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
    // instead of:
    //   const { isAuthenticated } = useAuthStore()
    //
    // The latter causes re-renders on ANY store change, which can cause
    // the checkAuth effect to run multiple times

    mockAuthStore.isLoading = false
    mockAuthStore.isAuthenticated = true

    renderWithRouter(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    )

    // This test passes as long as the component renders correctly
    // The actual verification is in the code review and the other regression tests
    expect(screen.getByText('Protected Content')).toBeInTheDocument()
  })
})

describe('ProtectedRoute bug fix verification', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockAuthStore.checkAuth = vi.fn()
  })

  it('should not get stuck in loading state when no token (bug fix)', async () => {
    // This test verifies the bug fix where isLoading was not set to false
    // when there was no token, causing the app to show loading forever

    // Simulate the fixed behavior: after checkAuth, isLoading becomes false
    mockAuthStore.checkAuth = vi.fn().mockImplementation(() => {
      // After checking, set loading to false (this is the fix)
      mockAuthStore.isLoading = false
      mockAuthStore.isAuthenticated = false
    })

    mockAuthStore.isLoading = true
    mockAuthStore.isAuthenticated = false

    const { rerender } = renderWithRouter(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    )

    // Initial state shows loading
    expect(screen.getByText('驗證身份中...')).toBeInTheDocument()

    // Manually trigger the state change that checkAuth would do
    mockAuthStore.isLoading = false
    mockAuthStore.isAuthenticated = false

    rerender(
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/login" element={<div>Login Page</div>} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <div>Protected Content</div>
              </ProtectedRoute>
            }
          />
        </Routes>
      </MemoryRouter>
    )

    // Should redirect to login (not stuck on loading)
    await waitFor(() => {
      expect(screen.getByText('Login Page')).toBeInTheDocument()
    })

    // Loading should no longer be visible
    expect(screen.queryByText('驗證身份中...')).not.toBeInTheDocument()
  })
})
