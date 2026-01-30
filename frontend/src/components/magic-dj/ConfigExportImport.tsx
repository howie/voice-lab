/**
 * Config Export/Import Components
 * Feature: 010-magic-dj-controller
 *
 * T063: Export sound library configuration as JSON (FR-023)
 * T064: Import sound library configuration from JSON file (FR-023)
 */

import { useRef, useState } from 'react'
import { Download, Upload, AlertCircle } from 'lucide-react'

import { useMagicDJStore } from '@/stores/magicDJStore'
import type { Track, CueList } from '@/types/magic-dj'

// =============================================================================
// Types
// =============================================================================

interface ExportedConfig {
  version: 1
  exportedAt: string
  tracks: Track[]
  cueList: CueList
}

// =============================================================================
// ConfigExport Component (T063)
// =============================================================================

export function ConfigExport() {
  const { tracks, cueList } = useMagicDJStore()

  const handleExport = () => {
    const config: ExportedConfig = {
      version: 1,
      exportedAt: new Date().toISOString(),
      tracks: tracks.map((t) => ({
        ...t,
        // Don't export blob URLs
        url: t.isCustom || t.source === 'upload' ? '' : t.url,
        audioBase64: undefined,
      })),
      cueList,
    }

    const blob = new Blob([JSON.stringify(config, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `magic-dj-config-${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <button
      onClick={handleExport}
      className="flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm transition-colors hover:bg-accent"
      title="匯出設定"
    >
      <Download className="h-3.5 w-3.5" />
      匯出
    </button>
  )
}

// =============================================================================
// ConfigImport Component (T064)
// =============================================================================

export function ConfigImport() {
  const { setTracks, setCueList } = useMagicDJStore()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [error, setError] = useState<string | null>(null)

  const handleImport = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setError(null)
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const raw = JSON.parse(e.target?.result as string)

        if (raw.version !== 1 || !Array.isArray(raw.tracks)) {
          setError('不支援的設定檔格式')
          return
        }

        const config = raw as ExportedConfig

        // Validate tracks have required fields
        const validTracks = config.tracks.filter(
          (t) => t.id && t.name && t.type,
        )

        if (validTracks.length === 0) {
          setError('設定檔中沒有有效的音軌')
          return
        }

        setTracks(validTracks)

        if (config.cueList) {
          setCueList(config.cueList)
        }

        setError(null)
      } catch {
        setError('無法解析設定檔')
      }
    }
    reader.readAsText(file)

    // Reset input so the same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="flex items-center gap-2">
      <input
        ref={fileInputRef}
        type="file"
        accept=".json"
        onChange={handleImport}
        className="hidden"
      />
      <button
        onClick={() => fileInputRef.current?.click()}
        className="flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm transition-colors hover:bg-accent"
        title="匯入設定"
      >
        <Upload className="h-3.5 w-3.5" />
        匯入
      </button>
      {error && (
        <span className="flex items-center gap-1 text-xs text-destructive">
          <AlertCircle className="h-3 w-3" />
          {error}
        </span>
      )}
    </div>
  )
}
