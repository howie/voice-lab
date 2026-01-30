/**
 * Hidden Toggle Component
 *
 * Feature: 013-tts-role-mgmt
 * T043: Toggle button for hidden status
 */

import { Eye, EyeOff } from 'lucide-react'
import { cn } from '@/lib/utils'

interface HiddenToggleProps {
  isHidden: boolean
  onToggle: () => Promise<void>
  disabled?: boolean
}

export function HiddenToggle({
  isHidden,
  onToggle,
  disabled = false,
}: HiddenToggleProps) {
  const handleClick = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (!disabled) {
      await onToggle()
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={disabled}
      className={cn(
        'p-1.5 rounded transition-colors',
        isHidden
          ? 'text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700'
          : 'text-green-600 hover:text-red-500 hover:bg-gray-100 dark:hover:bg-gray-700'
      )}
      title={isHidden ? '取消隱藏' : '隱藏此角色'}
    >
      {isHidden ? (
        <EyeOff className="w-4 h-4" />
      ) : (
        <Eye className="w-4 h-4" />
      )}
    </button>
  )
}
