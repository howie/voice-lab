/**
 * Auth State Store
 * T048: Create auth state store (Zustand)
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authApi } from '@/lib/api'

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
    (set, _get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
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

        try {
          // Get Google OAuth URL and redirect
          const response = await authApi.getGoogleAuthUrl()
          window.location.href = response.data.url
        } catch (error: any) {
          set({
            error: error.message || '登入失敗',
            isLoading: false,
          })
        }
      },

      logout: async () => {
        set({ isLoading: true })

        try {
          await authApi.logout()
        } catch (error) {
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
        const token = localStorage.getItem('auth_token')

        if (!token) {
          set({ isAuthenticated: false, user: null })
          return
        }

        set({ isLoading: true })

        try {
          const response = await authApi.getCurrentUser()
          set({
            user: response.data,
            token,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (error) {
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
