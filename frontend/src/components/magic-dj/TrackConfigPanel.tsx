/**
 * Track Config Panel
 * Feature: 010-magic-dj-controller
 *
 * T055: TrackConfigExport - exports track configuration as JSON.
 * T056: TrackConfigImport - imports track configuration from JSON.
 * T057: Add track config export/import buttons to UI.
 */

import { useRef } from 'react'
import { Download, Upload, Settings2 } from 'lucide-react'

import { useMagicDJStore } from '@/stores/magicDJStore'
import type { Track } from '@/types/magic-dj'

// =============================================================================
// Types
// =============================================================================

interface TrackConfigExport {
  version: '1.0'
  exportedAt: string
  tracks: Track[]
}

// =============================================================================
// Helpers
// =============================================================================

function downloadFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * Convert base64 audio data to blob URL
 */
function base64ToBlobUrl(base64: string): string {
  try {
    let mimeType = 'audio/mpeg'
    let data = base64

    if (base64.startsWith('data:')) {
      const matches = base64.match(/^data:([^;]+);base64,(.+)$/)
      if (matches) {
        mimeType = matches[1]
        data = matches[2]
      }
    }

    const byteCharacters = atob(data)
    const byteNumbers = new Array(byteCharacters.length)
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i)
    }
    const byteArray = new Uint8Array(byteNumbers)
    const blob = new Blob([byteArray], { type: mimeType })
    return URL.createObjectURL(blob)
  } catch (error) {
    console.error('Failed to convert base64 to blob URL:', error)
    return ''
  }
}

/**
 * Validate imported track configuration
 */
function validateTrackConfig(data: unknown): data is TrackConfigExport {
  if (typeof data !== 'object' || data === null) return false

  const config = data as Record<string, unknown>

  if (config.version !== '1.0') return false
  if (!Array.isArray(config.tracks)) return false

  // Validate each track has required fields
  for (const track of config.tracks) {
    if (typeof track !== 'object' || track === null) return false
    const t = track as Record<string, unknown>
    if (typeof t.id !== 'string') return false
    if (typeof t.name !== 'string') return false
    if (typeof t.type !== 'string') return false
  }

  return true
}

// =============================================================================
// Component
// =============================================================================

export function TrackConfigPanel() {
  const { tracks, setTracks } = useMagicDJStore()
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Count custom tracks
  const customTrackCount = tracks.filter((t) => t.isCustom).length

  const handleExport = () => {
    const config: TrackConfigExport = {
      version: '1.0',
      exportedAt: new Date().toISOString(),
      tracks: tracks.map((track) => ({
        ...track,
        // Don't export blob URLs, they're ephemeral
        url: track.isCustom ? '' : track.url,
      })),
    }

    const content = JSON.stringify(config, null, 2)
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
    const filename = `magic-dj-tracks-${timestamp}.json`
    downloadFile(content, filename, 'application/json')
  }

  const handleImportClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    try {
      const text = await file.text()
      const data = JSON.parse(text)

      if (!validateTrackConfig(data)) {
        alert('無效的音軌設定檔格式')
        return
      }

      // Restore tracks with blob URLs for custom tracks
      const restoredTracks = data.tracks.map((track: Track) => {
        if (track.isCustom && track.audioBase64) {
          return {
            ...track,
            url: base64ToBlobUrl(track.audioBase64),
          }
        }
        return track
      })

      // Confirm before replacing
      const customCount = restoredTracks.filter((t: Track) => t.isCustom).length
      const confirmed = confirm(
        `確定要匯入 ${restoredTracks.length} 個音軌（含 ${customCount} 個自訂音軌）？\n\n這將取代目前的音軌設定。`
      )

      if (confirmed) {
        setTracks(restoredTracks)
      }
    } catch (error) {
      console.error('Failed to import track config:', error)
      alert('匯入失敗：檔案格式錯誤')
    }

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Settings2 className="h-4 w-4" />
        <span>音軌設定</span>
        <span className="rounded bg-muted px-2 py-0.5">
          {tracks.length} 軌 / {customTrackCount} 自訂
        </span>
      </div>

      <div className="flex gap-2">
        <button
          onClick={handleExport}
          className="flex items-center gap-2 rounded-lg border bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-accent"
        >
          <Download className="h-4 w-4" />
          <span>匯出設定</span>
        </button>

        <button
          onClick={handleImportClick}
          className="flex items-center gap-2 rounded-lg border bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-accent"
        >
          <Upload className="h-4 w-4" />
          <span>匯入設定</span>
        </button>

        <input
          ref={fileInputRef}
          type="file"
          accept=".json"
          onChange={handleFileChange}
          className="hidden"
        />
      </div>
    </div>
  )
}

export default TrackConfigPanel
