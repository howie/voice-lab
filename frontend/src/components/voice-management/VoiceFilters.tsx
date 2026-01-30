/**
 * Voice Filters Component
 *
 * Feature: 013-tts-role-mgmt
 * T035: Filter toolbar for voice management
 */

import { Search, X } from 'lucide-react'
import { useVoiceManagementStore } from '@/stores/voiceManagementStore'

const PROVIDERS = [
  { value: '', label: '全部提供者' },
  { value: 'voai', label: 'VoAI' },
  { value: 'gemini', label: 'Gemini' },
  { value: 'azure', label: 'Azure' },
  { value: 'elevenlabs', label: 'ElevenLabs' },
]

const GENDERS = [
  { value: '', label: '全部性別' },
  { value: 'male', label: '男聲' },
  { value: 'female', label: '女聲' },
  { value: 'neutral', label: '中性' },
]

export function VoiceFilters() {
  const { filters, setFilter, resetFilters } = useVoiceManagementStore()

  const hasActiveFilters = !!(
    filters.provider ||
    filters.language ||
    filters.gender ||
    filters.search ||
    filters.favoritesOnly
  )

  return (
    <div className="flex flex-wrap items-center gap-3 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
      {/* Search */}
      <div className="relative flex-1 min-w-[200px]">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={filters.search || ''}
          onChange={(e) => setFilter('search', e.target.value || undefined)}
          placeholder="搜尋角色名稱..."
          className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
        />
      </div>

      {/* Provider filter */}
      <select
        value={filters.provider || ''}
        onChange={(e) => setFilter('provider', e.target.value || undefined)}
        className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
      >
        {PROVIDERS.map((p) => (
          <option key={p.value} value={p.value}>
            {p.label}
          </option>
        ))}
      </select>

      {/* Gender filter */}
      <select
        value={filters.gender || ''}
        onChange={(e) => setFilter('gender', (e.target.value as 'male' | 'female' | 'neutral') || undefined)}
        className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
      >
        {GENDERS.map((g) => (
          <option key={g.value} value={g.value}>
            {g.label}
          </option>
        ))}
      </select>

      {/* Favorites only toggle */}
      <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
        <input
          type="checkbox"
          checked={filters.favoritesOnly || false}
          onChange={(e) => setFilter('favoritesOnly', e.target.checked || undefined)}
          className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        僅顯示收藏
      </label>

      {/* Show hidden toggle */}
      <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
        <input
          type="checkbox"
          checked={filters.excludeHidden === false}
          onChange={(e) => setFilter('excludeHidden', e.target.checked ? false : undefined)}
          className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        顯示隱藏
      </label>

      {/* Reset button */}
      {hasActiveFilters && (
        <button
          onClick={resetFilters}
          className="flex items-center gap-1 px-3 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-200 rounded-lg transition-colors dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-700"
        >
          <X className="w-4 h-4" />
          清除篩選
        </button>
      )}
    </div>
  )
}
