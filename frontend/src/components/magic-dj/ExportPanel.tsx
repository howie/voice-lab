/**
 * Export Panel
 * Feature: 010-magic-dj-controller
 *
 * T042: ExportPanel component with JSON and CSV export buttons.
 * T043: JSON export function generating downloadable session file.
 * T044: CSV export function generating spreadsheet-compatible observation data.
 */

import { Download, FileJson, FileSpreadsheet } from 'lucide-react'

import { useMagicDJStore } from '@/stores/magicDJStore'
import type { SessionRecord } from '@/types/magic-dj'

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

function exportToJSON(session: SessionRecord) {
  const content = JSON.stringify(session, null, 2)
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
  const filename = `magic-dj-session-${timestamp}.json`
  downloadFile(content, filename, 'application/json')
}

function exportToCSV(session: SessionRecord) {
  // Create CSV header
  const headers = [
    'Timestamp',
    'Elapsed (sec)',
    'Action',
    'Data',
  ]

  // Convert operation logs to CSV rows
  const rows = session.operationLogs.map((log) => {
    const elapsed = Math.floor(
      (new Date(log.timestamp).getTime() - new Date(session.startTime).getTime()) / 1000
    )
    return [
      log.timestamp,
      elapsed.toString(),
      log.action,
      log.data ? JSON.stringify(log.data) : '',
    ]
  })

  // Build CSV content
  const csvContent = [
    // Session metadata
    `# Session ID: ${session.id}`,
    `# Start Time: ${session.startTime}`,
    `# End Time: ${session.endTime || 'N/A'}`,
    `# Duration: ${session.durationSeconds} seconds`,
    `# Mode Switches: ${session.modeSwitchCount}`,
    `# AI Interactions: ${session.aiInteractionCount}`,
    '',
    headers.join(','),
    ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
  ].join('\n')

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
  const filename = `magic-dj-session-${timestamp}.csv`
  downloadFile(csvContent, filename, 'text/csv')
}

// =============================================================================
// Component
// =============================================================================

export function ExportPanel() {
  const { currentSession, isSessionActive } = useMagicDJStore()

  const hasSession = currentSession !== null
  const canExport = hasSession && !isSessionActive

  const handleExportJSON = () => {
    if (currentSession) {
      exportToJSON(currentSession)
    }
  }

  const handleExportCSV = () => {
    if (currentSession) {
      exportToCSV(currentSession)
    }
  }

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Download className="h-4 w-4" />
        <span>匯出測試資料</span>
        {currentSession && (
          <span className="rounded bg-muted px-2 py-0.5">
            {currentSession.operationLogs.length} 筆操作
          </span>
        )}
      </div>

      <div className="flex gap-2">
        <button
          onClick={handleExportJSON}
          disabled={!canExport}
          className="flex items-center gap-2 rounded-lg border bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50"
        >
          <FileJson className="h-4 w-4" />
          <span>匯出 JSON</span>
        </button>

        <button
          onClick={handleExportCSV}
          disabled={!canExport}
          className="flex items-center gap-2 rounded-lg border bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-accent disabled:cursor-not-allowed disabled:opacity-50"
        >
          <FileSpreadsheet className="h-4 w-4" />
          <span>匯出 CSV</span>
        </button>
      </div>

      {isSessionActive && hasSession && (
        <div className="text-sm text-muted-foreground">
          測試進行中，結束後可匯出
        </div>
      )}
    </div>
  )
}

export default ExportPanel
