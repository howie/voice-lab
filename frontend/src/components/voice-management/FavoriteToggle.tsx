/**
 * Favorite Toggle Component
 *
 * Feature: 013-tts-role-mgmt
 * T028: Toggle button for favorite status
 */

import { Star } from 'lucide-react'
import { cn } from '@/lib/utils'

interface FavoriteToggleProps {
  isFavorite: boolean
  isHidden: boolean
  onToggle: () => Promise<void>
  disabled?: boolean
}

export function FavoriteToggle({
  isFavorite,
  isHidden,
  onToggle,
  disabled = false,
}: FavoriteToggleProps) {
  const handleClick = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (!disabled && !isHidden) {
      await onToggle()
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={disabled || isHidden}
      className={cn(
        'p-1.5 rounded transition-colors',
        isHidden
          ? 'text-gray-300 cursor-not-allowed dark:text-gray-600'
          : isFavorite
            ? 'text-yellow-500 hover:text-yellow-600 hover:bg-yellow-50 dark:hover:bg-yellow-900/20'
            : 'text-gray-400 hover:text-yellow-500 hover:bg-gray-100 dark:hover:bg-gray-700'
      )}
      title={isHidden ? '隱藏的角色無法收藏' : isFavorite ? '取消收藏' : '加入收藏'}
    >
      <Star
        className={cn('w-4 h-4', isFavorite && 'fill-current')}
      />
    </button>
  )
}
