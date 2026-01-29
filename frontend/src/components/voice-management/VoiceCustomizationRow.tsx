/**
 * Voice Customization Row Component
 *
 * Feature: 013-tts-role-mgmt
 * T018: Single row in the voice management table
 */

import { cn } from '@/lib/utils'
import { VoiceNameEditor } from './VoiceNameEditor'
import { FavoriteToggle } from './FavoriteToggle'
import { HiddenToggle } from './HiddenToggle'
import type { VoiceWithCustomization } from '@/types/voice-customization'

interface VoiceCustomizationRowProps {
  voice: VoiceWithCustomization
  isSelected: boolean
  onToggleSelect: () => void
  onUpdateCustomName: (customName: string | null) => Promise<void>
  onToggleFavorite: () => Promise<void>
  onToggleHidden: () => Promise<void>
}

const PROVIDER_COLORS: Record<string, string> = {
  voai: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
  gemini: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  azure: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-300',
  elevenlabs: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
}

const GENDER_LABELS: Record<string, string> = {
  male: '男',
  female: '女',
  neutral: '中性',
}

export function VoiceCustomizationRow({
  voice,
  isSelected,
  onToggleSelect,
  onUpdateCustomName,
  onToggleFavorite,
  onToggleHidden,
}: VoiceCustomizationRowProps) {
  const providerColor = PROVIDER_COLORS[voice.provider] || 'bg-gray-100 text-gray-800'

  return (
    <tr
      className={cn(
        'border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors',
        voice.isHidden && 'opacity-50',
        isSelected && 'bg-blue-50 dark:bg-blue-900/20'
      )}
    >
      {/* Checkbox */}
      <td className="px-4 py-3">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={onToggleSelect}
          className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
      </td>

      {/* Name */}
      <td className="px-4 py-3">
        <VoiceNameEditor
          voiceCacheId={voice.id}
          originalName={voice.displayName === voice.customization?.customName ? (voice.voice_id || voice.id.split(':')[1]) : voice.displayName}
          customName={voice.customization?.customName || null}
          onSave={onUpdateCustomName}
        />
      </td>

      {/* Provider */}
      <td className="px-4 py-3">
        <span
          className={cn(
            'inline-flex px-2 py-0.5 text-xs font-medium rounded-full',
            providerColor
          )}
        >
          {voice.provider}
        </span>
      </td>

      {/* Language */}
      <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
        {voice.language}
      </td>

      {/* Gender */}
      <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
        {voice.gender ? GENDER_LABELS[voice.gender] || voice.gender : '-'}
      </td>

      {/* Actions */}
      <td className="px-4 py-3">
        <div className="flex items-center gap-1">
          <FavoriteToggle
            isFavorite={voice.isFavorite}
            isHidden={voice.isHidden}
            onToggle={onToggleFavorite}
          />
          <HiddenToggle
            isHidden={voice.isHidden}
            onToggle={onToggleHidden}
          />
        </div>
      </td>
    </tr>
  )
}
