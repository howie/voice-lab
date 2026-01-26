/**
 * AuthStore Unit Tests
 *
 * Tests verify authentication state management in different modes:
 * - VITE_DISABLE_AUTH=true: Skip auth, use dev user
 * - VITE_DISABLE_AUTH=false: Normal auth flow
 * - Token handling and user state management
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { act } from '@testing-library/react'

// Mock localStorage
const createLocalStorageMock = () => {
  let store: Record<string, string> = {}

  return {
    get store() {
      return store
    },
    set store(value: Record<string, string>) {
      store = value
    },
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      store = {}
    }),
  }
}

const localStorageMock = createLocalStorageMock()

Object.defineProperty(window, 'localStorage', { value: localStorageMock })

// Mock the API module
vi.mock('@/lib/api', () => ({
  authApi: {
    getGoogleAuthUrl: vi.fn(),
    getCurrentUser: vi.fn(),
    logout: vi.fn(),
  },
}))

describe('AuthStore', () => {
  beforeEach(() => {
    // Clear localStorage and mocks before each test
    localStorageMock.clear()
    vi.clearAllMocks()

    // Reset module cache to get fresh store
    vi.resetModules()
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  describe('with DISABLE_AUTH=false (normal mode)', () => {
    beforeEach(() => {
      vi.stubEnv('VITE_DISABLE_AUTH', 'false')
    })

    it('should start with isLoading=true', async () => {
      const { useAuthStore } = await import('../authStore')
      const state = useAuthStore.getState()

      expect(state.isLoading).toBe(true)
      expect(state.isAuthenticated).toBe(false)
    })

    it('should set isAuthenticated=false and isLoading=false when no token', async () => {
      const { useAuthStore } = await import('../authStore')

      await act(async () => {
        await useAuthStore.getState().checkAuth()
      })

      const state = useAuthStore.getState()
      expect(state.isAuthenticated).toBe(false)
      expect(state.isLoading).toBe(false)
      expect(state.user).toBeNull()
    })

    it('should fetch user when token exists', async () => {
      // Set up token in localStorage
      localStorageMock.store['auth_token'] = 'valid-token'

      const { authApi } = await import('@/lib/api')
      vi.mocked(authApi.getCurrentUser).mockResolvedValue({
        data: {
          id: 'user-123',
          email: 'test@example.com',
          name: 'Test User',
          picture_url: 'https://example.com/pic.jpg',
        },
      } as never)

      const { useAuthStore } = await import('../authStore')

      await act(async () => {
        await useAuthStore.getState().checkAuth()
      })

      const state = useAuthStore.getState()
      expect(state.isAuthenticated).toBe(true)
      expect(state.isLoading).toBe(false)
      expect(state.user?.email).toBe('test@example.com')
    })

    it('should clear auth state when API call fails', async () => {
      localStorageMock.store['auth_token'] = 'invalid-token'

      const { authApi } = await import('@/lib/api')
      vi.mocked(authApi.getCurrentUser).mockRejectedValue(new Error('Unauthorized'))

      const { useAuthStore } = await import('../authStore')

      await act(async () => {
        await useAuthStore.getState().checkAuth()
      })

      const state = useAuthStore.getState()
      expect(state.isAuthenticated).toBe(false)
      expect(state.isLoading).toBe(false)
      expect(state.user).toBeNull()
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth_token')
    })

    it('should set token and isAuthenticated on setToken', async () => {
      const { useAuthStore } = await import('../authStore')

      act(() => {
        useAuthStore.getState().setToken('new-token')
      })

      const state = useAuthStore.getState()
      expect(state.token).toBe('new-token')
      expect(state.isAuthenticated).toBe(true)
      expect(localStorageMock.setItem).toHaveBeenCalledWith('auth_token', 'new-token')
    })

    it('should clear state on logout', async () => {
      const { authApi } = await import('@/lib/api')
      vi.mocked(authApi.logout).mockResolvedValue(undefined as never)

      const { useAuthStore } = await import('../authStore')

      // Set initial authenticated state
      act(() => {
        useAuthStore.setState({
          user: { id: '123', email: 'test@example.com' },
          token: 'some-token',
          isAuthenticated: true,
          isLoading: false,
        })
      })

      await act(async () => {
        await useAuthStore.getState().logout()
      })

      const state = useAuthStore.getState()
      expect(state.isAuthenticated).toBe(false)
      expect(state.user).toBeNull()
      expect(state.token).toBeNull()
      expect(localStorageMock.removeItem).toHaveBeenCalledWith('auth_token')
    })
  })

  describe('with DISABLE_AUTH=true (dev mode)', () => {
    beforeEach(() => {
      vi.stubEnv('VITE_DISABLE_AUTH', 'true')
    })

    it('should immediately set dev user without API call', async () => {
      const { authApi } = await import('@/lib/api')
      const { useAuthStore } = await import('../authStore')

      await act(async () => {
        await useAuthStore.getState().checkAuth()
      })

      const state = useAuthStore.getState()
      expect(state.isAuthenticated).toBe(true)
      expect(state.isLoading).toBe(false)
      expect(state.user?.email).toBe('dev@localhost')
      expect(state.user?.name).toBe('Development User')
      expect(state.user?.id).toBe('00000000-0000-0000-0000-000000000001')

      // Should NOT call API
      expect(authApi.getCurrentUser).not.toHaveBeenCalled()
    })

    it('should set dev token', async () => {
      const { useAuthStore } = await import('../authStore')

      await act(async () => {
        await useAuthStore.getState().checkAuth()
      })

      const state = useAuthStore.getState()
      expect(state.token).toBe('dev-token')
    })
  })

  describe('isLoading state management', () => {
    beforeEach(() => {
      vi.stubEnv('VITE_DISABLE_AUTH', 'false')
    })

    it('should set isLoading=false when no token (bug fix verification)', async () => {
      // This test verifies the bug fix where isLoading was not set to false
      // when there was no token
      const { useAuthStore } = await import('../authStore')

      // Initial state should have isLoading=true
      expect(useAuthStore.getState().isLoading).toBe(true)

      await act(async () => {
        await useAuthStore.getState().checkAuth()
      })

      // After checkAuth with no token, isLoading should be false
      const state = useAuthStore.getState()
      expect(state.isLoading).toBe(false)
      expect(state.isAuthenticated).toBe(false)
    })

    it('should handle concurrent checkAuth calls', async () => {
      localStorageMock.store['auth_token'] = 'valid-token'

      const { authApi } = await import('@/lib/api')

      // Simulate slow API response
      vi.mocked(authApi.getCurrentUser).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  data: {
                    id: 'user-123',
                    email: 'test@example.com',
                  },
                } as never),
              100
            )
          )
      )

      const { useAuthStore } = await import('../authStore')

      // Call checkAuth multiple times concurrently
      await act(async () => {
        await Promise.all([
          useAuthStore.getState().checkAuth(),
          useAuthStore.getState().checkAuth(),
          useAuthStore.getState().checkAuth(),
        ])
      })

      const state = useAuthStore.getState()
      expect(state.isLoading).toBe(false)
      expect(state.isAuthenticated).toBe(true)
    })
  })
})

describe('Regression: checkAuth should not unmount children', () => {
  // These tests verify the fix for the bug where calling checkAuth() on an
  // already-authenticated user would set isLoading=true, causing ProtectedRoute
  // to unmount children (e.g., WebSocket connections would be disconnected)

  beforeEach(() => {
    vi.stubEnv('VITE_DISABLE_AUTH', 'false')
    localStorageMock.clear()
    vi.clearAllMocks()
    vi.resetModules()
  })

  it('should NOT set isLoading=true when user is already authenticated', async () => {
    // Setup: User is already authenticated
    localStorageMock.store['auth_token'] = 'valid-token'

    const { authApi } = await import('@/lib/api')
    vi.mocked(authApi.getCurrentUser).mockResolvedValue({
      data: { id: 'user-123', email: 'test@example.com' },
    } as never)

    const { useAuthStore } = await import('../authStore')

    // First checkAuth - establishes authenticated state
    await act(async () => {
      await useAuthStore.getState().checkAuth()
    })

    expect(useAuthStore.getState().isAuthenticated).toBe(true)
    expect(useAuthStore.getState().user).not.toBeNull()

    // Track isLoading changes
    const loadingStates: boolean[] = []
    const unsubscribe = useAuthStore.subscribe((state) => {
      loadingStates.push(state.isLoading)
    })

    // Second checkAuth - should NOT set isLoading=true
    await act(async () => {
      await useAuthStore.getState().checkAuth()
    })

    unsubscribe()

    // isLoading should never have become true during the second checkAuth
    // This is critical because isLoading=true causes children to unmount
    expect(loadingStates).not.toContain(true)
    expect(useAuthStore.getState().isLoading).toBe(false)
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
  })

  it('should skip API call when user is already authenticated with same token', async () => {
    localStorageMock.store['auth_token'] = 'valid-token'

    const { authApi } = await import('@/lib/api')
    vi.mocked(authApi.getCurrentUser).mockResolvedValue({
      data: { id: 'user-123', email: 'test@example.com' },
    } as never)

    const { useAuthStore } = await import('../authStore')

    // First checkAuth
    await act(async () => {
      await useAuthStore.getState().checkAuth()
    })

    expect(authApi.getCurrentUser).toHaveBeenCalledTimes(1)

    // Second checkAuth - should skip API call since user is already authenticated
    await act(async () => {
      await useAuthStore.getState().checkAuth()
    })

    // API should NOT be called again
    expect(authApi.getCurrentUser).toHaveBeenCalledTimes(1)
  })

  it('should re-fetch user when token changes', async () => {
    localStorageMock.store['auth_token'] = 'token-1'

    const { authApi } = await import('@/lib/api')
    vi.mocked(authApi.getCurrentUser).mockResolvedValue({
      data: { id: 'user-123', email: 'test@example.com' },
    } as never)

    const { useAuthStore } = await import('../authStore')

    // First checkAuth with token-1
    await act(async () => {
      await useAuthStore.getState().checkAuth()
    })

    expect(authApi.getCurrentUser).toHaveBeenCalledTimes(1)

    // Change token in localStorage (simulates re-login)
    localStorageMock.store['auth_token'] = 'token-2'

    // Clear the stored token in state to simulate token mismatch
    act(() => {
      useAuthStore.setState({ token: 'token-1' }) // Old token
    })

    // Second checkAuth with different token - should fetch user again
    await act(async () => {
      await useAuthStore.getState().checkAuth()
    })

    // API should be called again because token changed
    expect(authApi.getCurrentUser).toHaveBeenCalledTimes(2)
  })
})

describe('ProtectedRoute behavior', () => {
  // These tests verify the integration between authStore and ProtectedRoute
  // Note: Full component tests would be in a separate file

  beforeEach(() => {
    vi.stubEnv('VITE_DISABLE_AUTH', 'false')
    localStorageMock.clear()
    vi.clearAllMocks()
    vi.resetModules()
  })

  it('should redirect when not authenticated and not loading', async () => {
    // This test documents the expected behavior:
    // When isLoading=false AND isAuthenticated=false -> redirect to login

    const { useAuthStore } = await import('../authStore')

    await act(async () => {
      await useAuthStore.getState().checkAuth()
    })

    const state = useAuthStore.getState()

    // These conditions trigger redirect in ProtectedRoute
    const shouldRedirect = !state.isLoading && !state.isAuthenticated
    expect(shouldRedirect).toBe(true)
  })

  it('should not redirect when loading', async () => {
    const { useAuthStore } = await import('../authStore')

    // Initial state - loading
    const initialState = useAuthStore.getState()

    // Should NOT redirect while loading
    const shouldRedirect = !initialState.isLoading && !initialState.isAuthenticated
    expect(shouldRedirect).toBe(false) // isLoading is true, so !isLoading is false
  })

  it('should not redirect when authenticated', async () => {
    localStorageMock.store['auth_token'] = 'valid-token'

    const { authApi } = await import('@/lib/api')
    vi.mocked(authApi.getCurrentUser).mockResolvedValue({
      data: { id: '123', email: 'test@example.com' },
    } as never)

    const { useAuthStore } = await import('../authStore')

    await act(async () => {
      await useAuthStore.getState().checkAuth()
    })

    const state = useAuthStore.getState()

    // Should NOT redirect when authenticated
    const shouldRedirect = !state.isLoading && !state.isAuthenticated
    expect(shouldRedirect).toBe(false)
  })
})
