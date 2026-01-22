/**
 * SettingsDialog Component
 * Modal dialog for app settings (theme)
 */

import { useSettingsStore } from '@/stores/settingsStore'
import { X, Sun, Moon, Monitor } from 'lucide-react'

interface SettingsDialogProps {
  isOpen: boolean
  onClose: () => void
}

export function SettingsDialog({ isOpen, onClose }: SettingsDialogProps) {
  const { theme, setTheme } = useSettingsStore()

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
      />

      {/* Dialog */}
      <div className="relative z-10 w-full max-w-md rounded-lg border bg-card p-6 shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold">設定</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1 hover:bg-accent"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Theme Setting */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-3">
            外觀主題
          </label>
          <div className="grid grid-cols-3 gap-2">
            <button
              onClick={() => setTheme('light')}
              className={`flex flex-col items-center gap-2 rounded-lg border p-3 transition-colors ${
                theme === 'light'
                  ? 'border-primary bg-primary/10'
                  : 'hover:bg-accent'
              }`}
            >
              <Sun className="h-5 w-5" />
              <span className="text-xs">淺色</span>
            </button>
            <button
              onClick={() => setTheme('dark')}
              className={`flex flex-col items-center gap-2 rounded-lg border p-3 transition-colors ${
                theme === 'dark'
                  ? 'border-primary bg-primary/10'
                  : 'hover:bg-accent'
              }`}
            >
              <Moon className="h-5 w-5" />
              <span className="text-xs">深色</span>
            </button>
            <button
              onClick={() => setTheme('system')}
              className={`flex flex-col items-center gap-2 rounded-lg border p-3 transition-colors ${
                theme === 'system'
                  ? 'border-primary bg-primary/10'
                  : 'hover:bg-accent'
              }`}
            >
              <Monitor className="h-5 w-5" />
              <span className="text-xs">系統</span>
            </button>
          </div>
        </div>

        {/* Close button */}
        <button
          onClick={onClose}
          className="w-full rounded-lg bg-primary py-2 text-sm text-primary-foreground hover:bg-primary/90"
        >
          完成
        </button>
      </div>
    </div>
  )
}
