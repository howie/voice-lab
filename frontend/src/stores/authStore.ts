/**
 * Auth State Store
 * T048: Create auth state store (Zustand)
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authApi } from '@/lib/api'

// Development mode: disable authentication
const DISABLE_AUTH = import.meta.env.VITE_DISABLE_AUTH === 'true'

// Development user (must be valid UUID for backend compatibility)
const DEV_USER = {
  id: '00000000-0000-0000-0000-000000000001',
  email: 'dev@localhost',
  name: 'Development User',
  picture_url: undefined,
}

interface User {
  id: string
  email: string
  name?: string
  picture_url?: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  // Actions
  setToken: (token: string) => void
  setUser: (user: User | null) => void
  login: () => Promise<void>
  logout: () => Promise<void>
  checkAuth: () => Promise<void>
  clearError: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: true, // Start with loading to prevent redirect race condition
      error: null,

      setToken: (token) => {
        localStorage.setItem('auth_token', token)
        set({ token, isAuthenticated: true })
      },

      setUser: (user) => {
        set({ user, isAuthenticated: !!user })
      },

      login: async () => {
        set({ isLoading: true, error: null })

        // Directly navigate to backend OAuth endpoint (not through Vite proxy)
        // This avoids CORS issues with Google OAuth redirect
        // Check runtime config first, then build-time env, then fallback
        const runtimeConfig = (window as { __RUNTIME_CONFIG__?: { VITE_API_BASE_URL?: string } }).__RUNTIME_CONFIG__
        const backendUrl = runtimeConfig?.VITE_API_BASE_URL
          || import.meta.env.VITE_API_BASE_URL
          || '/api/v1'
        const currentUrl = window.location.origin
        window.location.href = `${backendUrl}/auth/google?redirect_uri=${encodeURIComponent(currentUrl)}`
      },

      logout: async () => {
        set({ isLoading: true })

        try {
          await authApi.logout()
        } catch {
          // Ignore logout errors
        } finally {
          localStorage.removeItem('auth_token')
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          })
        }
      },

      checkAuth: async () => {
        // Development mode: skip authentication
        if (DISABLE_AUTH) {
          set({
            user: DEV_USER,
            token: 'dev-token',
            isAuthenticated: true,
            isLoading: false,
          })
          return
        }

        const token = localStorage.getItem('auth_token')

        if (!token) {
          set({ isAuthenticated: false, user: null, isLoading: false })
          return
        }

        // If we already have a valid user and token, skip the API call
        // This prevents unnecessary loading states that unmount children
        const currentState = get()
        if (currentState.user && currentState.isAuthenticated && currentState.token === token) {
          set({ isLoading: false })
          return
        }

        // Only set loading if we don't have user data yet
        // This prevents unmounting children during auth re-checks
        if (!currentState.user) {
          set({ isLoading: true })
        }

        try {
          const response = await authApi.getCurrentUser()
          set({
            user: response.data,
            token,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch {
          localStorage.removeItem('auth_token')
          set({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          })
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
      }),
    }
  )
)
