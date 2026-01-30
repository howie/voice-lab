/**
 * Voice Management Table Component
 *
 * Feature: 013-tts-role-mgmt
 * T019: Main table for voice management
 */

import { useEffect } from 'react'
import { Loader2 } from 'lucide-react'
import { useVoiceManagementStore } from '@/stores/voiceManagementStore'
import { VoiceCustomizationRow } from './VoiceCustomizationRow'
import { VoiceFilters } from './VoiceFilters'

export function VoiceManagementTable() {
  const {
    voices,
    total,
    isLoading,
    error,
    page,
    pageSize,
    selectedVoiceIds,
    loadVoices,
    setPage,
    toggleSelection,
    selectAll,
    clearSelection,
    updateCustomName,
    toggleFavorite,
    toggleHidden,
  } = useVoiceManagementStore()

  // Load voices on mount
  useEffect(() => {
    loadVoices()
  }, [loadVoices])

  const totalPages = Math.ceil(total / pageSize)
  const allSelected = voices.length > 0 && voices.every((v) => selectedVoiceIds.has(v.id))
  const someSelected = selectedVoiceIds.size > 0

  const handleSelectAll = () => {
    if (allSelected) {
      clearSelection()
    } else {
      selectAll()
    }
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <VoiceFilters />

      {/* Error message */}
      {error && (
        <div className="flex items-center justify-between p-4 bg-red-50 text-red-700 rounded-lg dark:bg-red-900/20 dark:text-red-300">
          <span>{error}</span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => loadVoices()}
              className="text-sm font-medium text-red-700 hover:text-red-900 underline dark:text-red-300 dark:hover:text-red-100"
            >
              重試
            </button>
          </div>
        </div>
      )}

      {/* Bulk actions bar */}
      {someSelected && (
        <div className="flex items-center gap-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <span className="text-sm text-blue-700 dark:text-blue-300">
            已選擇 {selectedVoiceIds.size} 個角色
          </span>
          <button
            onClick={clearSelection}
            className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200"
          >
            取消選擇
          </button>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-4 py-3 text-left">
                <input
                  type="checkbox"
                  checked={allSelected}
                  onChange={handleSelectAll}
                  className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">
                名稱
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">
                提供者
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">
                語言
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">
                性別
              </th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">
                操作
              </th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={6} className="px-4 py-12 text-center">
                  <Loader2 className="w-6 h-6 animate-spin mx-auto text-gray-400" />
                  <p className="mt-2 text-sm text-gray-500">載入中...</p>
                </td>
              </tr>
            ) : voices.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-12 text-center text-gray-500">
                  沒有符合條件的角色
                </td>
              </tr>
            ) : (
              voices.map((voice) => (
                <VoiceCustomizationRow
                  key={voice.id}
                  voice={voice}
                  isSelected={selectedVoiceIds.has(voice.id)}
                  onToggleSelect={() => toggleSelection(voice.id)}
                  onUpdateCustomName={(customName) => updateCustomName(voice.id, customName)}
                  onToggleFavorite={() => toggleFavorite(voice.id)}
                  onToggleHidden={() => toggleHidden(voice.id)}
                />
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div className="text-sm text-gray-600 dark:text-gray-400">
            共 {total} 個角色，第 {page} / {totalPages} 頁
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(page - 1)}
              disabled={page === 1}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed dark:border-gray-600 dark:hover:bg-gray-700"
            >
              上一頁
            </button>
            <button
              onClick={() => setPage(page + 1)}
              disabled={page === totalPages}
              className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed dark:border-gray-600 dark:hover:bg-gray-700"
            >
              下一頁
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
