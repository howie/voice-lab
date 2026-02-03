/**
 * Preview Button Component
 *
 * Feature: 013-tts-role-mgmt
 * US5: 播放聲音預覽 (Voice Preview Playback)
 */

import { Play, Square, Loader2, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useVoicePreview } from '@/hooks/useVoicePreview'

interface PreviewButtonProps {
  voiceCacheId: string
  sampleAudioUrl?: string | null
  disabled?: boolean
}

export function PreviewButton({
  voiceCacheId,
  sampleAudioUrl,
  disabled = false,
}: PreviewButtonProps) {
  const { state, error, togglePreview } = useVoicePreview(voiceCacheId, sampleAudioUrl)

  const handleClick = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (!disabled) {
      await togglePreview()
    }
  }

  const icon = {
    idle: <Play className="w-4 h-4" />,
    loading: <Loader2 className="w-4 h-4 animate-spin" />,
    playing: <Square className="w-4 h-4 fill-current" />,
    error: <AlertCircle className="w-4 h-4" />,
  }[state]

  const title = {
    idle: '播放預覽',
    loading: '產生預覽中...',
    playing: '停止播放',
    error: error || '播放失敗',
  }[state]

  return (
    <button
      onClick={handleClick}
      disabled={disabled || state === 'loading'}
      className={cn(
        'p-1.5 rounded transition-colors',
        state === 'error'
          ? 'text-red-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20'
          : state === 'playing'
            ? 'text-blue-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20'
            : 'text-gray-400 hover:text-blue-500 hover:bg-gray-100 dark:hover:bg-gray-700',
        (disabled || state === 'loading') && 'cursor-not-allowed opacity-50'
      )}
      title={title}
    >
      {icon}
    </button>
  )
}
