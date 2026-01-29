/**
 * Preset Selector
 * Feature: 011-magic-dj-audio-features
 * Phase 3: Frontend Integration
 *
 * Component for selecting and managing DJ presets from backend.
 */

import { useEffect, useState } from 'react'
import {
  ChevronDown,
  Cloud,
  HardDrive,
  Loader2,
  Plus,
  RefreshCw,
  Trash2,
  Upload,
} from 'lucide-react'

import { useMagicDJStore } from '@/stores/magicDJStore'
import { cn } from '@/lib/utils'

// =============================================================================
// Types
// =============================================================================

export interface PresetSelectorProps {
  className?: string
}

// =============================================================================
// Component
// =============================================================================

export function PresetSelector({ className }: PresetSelectorProps) {
  const {
    currentPresetId,
    presets,
    isAuthenticated,
    isLoading,
    isSyncing,
    syncError,
    fetchPresets,
    loadPreset,
    createNewPreset,
    deleteCurrentPreset,
    importToBackend,
    switchToLocalStorage,
  } = useMagicDJStore()

  const [isOpen, setIsOpen] = useState(false)
  const [showNewPresetDialog, setShowNewPresetDialog] = useState(false)
  const [showImportDialog, setShowImportDialog] = useState(false)
  const [newPresetName, setNewPresetName] = useState('')
  const [importPresetName, setImportPresetName] = useState('')
  const [error, setError] = useState<string | null>(null)

  // Fetch presets on mount if authenticated
  useEffect(() => {
    if (isAuthenticated) {
      fetchPresets()
    }
  }, [isAuthenticated, fetchPresets])

  // Current preset info
  const currentPreset = presets.find((p) => p.id === currentPresetId)
  const isLocalMode = !currentPresetId

  // Handle preset selection
  const handleSelectPreset = async (presetId: string) => {
    setError(null)
    try {
      await loadPreset(presetId)
      setIsOpen(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load preset')
    }
  }

  // Handle create new preset
  const handleCreatePreset = async () => {
    if (!newPresetName.trim()) return
    setError(null)
    try {
      const presetId = await createNewPreset(newPresetName.trim())
      await loadPreset(presetId)
      setShowNewPresetDialog(false)
      setNewPresetName('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create preset')
    }
  }

  // Handle import to backend
  const handleImport = async () => {
    if (!importPresetName.trim()) return
    setError(null)
    try {
      const presetId = await importToBackend(importPresetName.trim())
      await loadPreset(presetId)
      setShowImportDialog(false)
      setImportPresetName('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to import')
    }
  }

  // Handle delete current preset
  const handleDelete = async () => {
    if (!currentPresetId) return
    if (!confirm('確定要刪除此預設組？此操作無法復原。')) return

    setError(null)
    try {
      await deleteCurrentPreset()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete preset')
    }
  }

  // Handle switch to local storage
  const handleSwitchToLocal = () => {
    switchToLocalStorage()
    setIsOpen(false)
  }

  if (!isAuthenticated) {
    // Show local mode indicator only
    return (
      <div className={cn('flex items-center gap-2 text-sm text-muted-foreground', className)}>
        <HardDrive className="h-4 w-4" />
        <span>本機模式</span>
      </div>
    )
  }

  return (
    <div className={cn('relative', className)}>
      {/* Main Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isLoading}
        className={cn(
          'flex items-center gap-2 rounded-lg border px-3 py-2 text-sm transition-colors',
          'hover:bg-muted focus:outline-none focus:ring-2 focus:ring-primary/50',
          isLoading && 'opacity-50 cursor-not-allowed'
        )}
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : isLocalMode ? (
          <HardDrive className="h-4 w-4 text-amber-500" />
        ) : (
          <Cloud className="h-4 w-4 text-blue-500" />
        )}

        <span className="max-w-32 truncate">
          {isLocalMode ? '本機模式' : currentPreset?.name || '選擇預設組'}
        </span>

        {isSyncing && <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />}

        <ChevronDown
          className={cn('h-4 w-4 transition-transform', isOpen && 'rotate-180')}
        />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 z-50 mt-1 w-64 rounded-lg border bg-background shadow-lg">
          {/* Error Message */}
          {(error || syncError) && (
            <div className="border-b bg-destructive/10 px-3 py-2 text-xs text-destructive">
              {error || syncError}
            </div>
          )}

          {/* Local Storage Option */}
          <div
            onClick={handleSwitchToLocal}
            className={cn(
              'flex cursor-pointer items-center gap-2 px-3 py-2 text-sm transition-colors',
              'hover:bg-muted',
              isLocalMode && 'bg-muted'
            )}
          >
            <HardDrive className="h-4 w-4 text-amber-500" />
            <span>本機模式（localStorage）</span>
          </div>

          {/* Divider */}
          <div className="border-t" />

          {/* Preset List */}
          <div className="max-h-48 overflow-y-auto">
            {presets.length === 0 ? (
              <div className="px-3 py-4 text-center text-sm text-muted-foreground">
                尚無雲端預設組
              </div>
            ) : (
              presets.map((preset) => (
                <div
                  key={preset.id}
                  onClick={() => handleSelectPreset(preset.id)}
                  className={cn(
                    'flex cursor-pointer items-center gap-2 px-3 py-2 text-sm transition-colors',
                    'hover:bg-muted',
                    preset.id === currentPresetId && 'bg-muted'
                  )}
                >
                  <Cloud className="h-4 w-4 text-blue-500" />
                  <span className="flex-1 truncate">{preset.name}</span>
                  {preset.is_default && (
                    <span className="text-xs text-muted-foreground">預設</span>
                  )}
                </div>
              ))
            )}
          </div>

          {/* Divider */}
          <div className="border-t" />

          {/* Actions */}
          <div className="p-2 space-y-1">
            <button
              onClick={() => setShowNewPresetDialog(true)}
              className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-muted"
            >
              <Plus className="h-4 w-4" />
              <span>新增預設組</span>
            </button>

            {isLocalMode && (
              <button
                onClick={() => setShowImportDialog(true)}
                className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-muted"
              >
                <Upload className="h-4 w-4" />
                <span>上傳至雲端</span>
              </button>
            )}

            {currentPresetId && (
              <button
                onClick={handleDelete}
                className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-sm text-destructive hover:bg-destructive/10"
              >
                <Trash2 className="h-4 w-4" />
                <span>刪除預設組</span>
              </button>
            )}

            <button
              onClick={() => {
                fetchPresets()
                setIsOpen(false)
              }}
              className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-muted"
            >
              <RefreshCw className="h-4 w-4" />
              <span>重新整理</span>
            </button>
          </div>
        </div>
      )}

      {/* New Preset Dialog */}
      {showNewPresetDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-80 rounded-lg bg-background p-4 shadow-xl">
            <h3 className="mb-4 text-lg font-semibold">新增預設組</h3>
            <input
              type="text"
              value={newPresetName}
              onChange={(e) => setNewPresetName(e.target.value)}
              placeholder="預設組名稱"
              className="mb-4 w-full rounded border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              autoFocus
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setShowNewPresetDialog(false)
                  setNewPresetName('')
                }}
                className="rounded px-3 py-1.5 text-sm hover:bg-muted"
              >
                取消
              </button>
              <button
                onClick={handleCreatePreset}
                disabled={!newPresetName.trim() || isLoading}
                className="rounded bg-primary px-3 py-1.5 text-sm text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {isLoading ? '建立中...' : '建立'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Import Dialog */}
      {showImportDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-80 rounded-lg bg-background p-4 shadow-xl">
            <h3 className="mb-2 text-lg font-semibold">上傳至雲端</h3>
            <p className="mb-4 text-sm text-muted-foreground">
              將目前的本機設定上傳至雲端儲存
            </p>
            <input
              type="text"
              value={importPresetName}
              onChange={(e) => setImportPresetName(e.target.value)}
              placeholder="預設組名稱"
              className="mb-4 w-full rounded border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
              autoFocus
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setShowImportDialog(false)
                  setImportPresetName('')
                }}
                className="rounded px-3 py-1.5 text-sm hover:bg-muted"
              >
                取消
              </button>
              <button
                onClick={handleImport}
                disabled={!importPresetName.trim() || isLoading}
                className="rounded bg-primary px-3 py-1.5 text-sm text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {isLoading ? '上傳中...' : '上傳'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Click outside to close */}
      {isOpen && (
        <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
      )}
    </div>
  )
}

export default PresetSelector
