/**
 * Settings Store
 * Manages app settings like theme and language
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'light' | 'dark' | 'system'
type Language = 'zh-TW' | 'en'

interface SettingsState {
  theme: Theme
  language: Language

  // Actions
  setTheme: (theme: Theme) => void
  setLanguage: (language: Language) => void
}

// Apply theme to document
function applyTheme(theme: Theme) {
  const root = document.documentElement
  const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches

  if (theme === 'dark' || (theme === 'system' && systemDark)) {
    root.classList.add('dark')
  } else {
    root.classList.remove('dark')
  }
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      theme: 'system',
      language: 'zh-TW',

      setTheme: (theme) => {
        applyTheme(theme)
        set({ theme })
      },

      setLanguage: (language) => {
        set({ language })
      },
    }),
    {
      name: 'settings-storage',
      onRehydrateStorage: () => (state) => {
        // Apply theme on rehydration
        if (state?.theme) {
          applyTheme(state.theme)
        }
      },
    }
  )
)

// Listen for system theme changes
if (typeof window !== 'undefined') {
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    const { theme } = useSettingsStore.getState()
    if (theme === 'system') {
      applyTheme('system')
    }
  })
}
