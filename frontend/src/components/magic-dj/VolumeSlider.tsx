/**
 * Volume Slider Component
 * Feature: 011-magic-dj-audio-features
 *
 * T022-T026: Volume slider with mute toggle and dynamic icon.
 */

import { useCallback } from 'react'
import { Volume, Volume1, Volume2, VolumeX } from 'lucide-react'

import { cn } from '@/lib/utils'

// =============================================================================
// Types
// =============================================================================

export interface VolumeSliderProps {
  /** Current volume value (0-1) */
  value: number
  /** Callback when volume changes */
  onChange: (volume: number) => void
  /** Callback when mute is toggled */
  onMuteToggle?: () => void
  /** Whether the track is muted */
  isMuted?: boolean
  /** Whether the slider is disabled */
  disabled?: boolean
  /** Size variant */
  size?: 'sm' | 'md' | 'lg'
  /** Whether to show percentage */
  showPercentage?: boolean
  /** Custom class name */
  className?: string
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Get volume icon based on current volume level (T024)
 */
const getVolumeIcon = (volume: number, isMuted: boolean) => {
  if (isMuted || volume === 0) return VolumeX // Muted
  if (volume < 0.33) return Volume // Low
  if (volume < 0.67) return Volume1 // Medium
  return Volume2 // High
}

/**
 * Format volume as percentage
 */
const formatPercentage = (value: number): string => {
  return `${Math.round(value * 100)}%`
}

// =============================================================================
// Component
// =============================================================================

export function VolumeSlider({
  value,
  onChange,
  onMuteToggle,
  isMuted = false,
  disabled = false,
  size = 'md',
  showPercentage = false,
  className,
}: VolumeSliderProps) {
  const VolumeIcon = getVolumeIcon(value, isMuted)

  // Size-based styling
  const sizeClasses = {
    sm: {
      icon: 'h-4 w-4',
      slider: 'h-1 w-16',
      percentage: 'text-xs w-8',
    },
    md: {
      icon: 'h-5 w-5',
      slider: 'h-1.5 w-20',
      percentage: 'text-sm w-10',
    },
    lg: {
      icon: 'h-6 w-6',
      slider: 'h-2 w-24',
      percentage: 'text-base w-12',
    },
  }

  const currentSize = sizeClasses[size]

  /**
   * Handle slider change (T023)
   */
  const handleSliderChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = parseFloat(e.target.value)
      onChange(newValue)
    },
    [onChange]
  )

  /**
   * Handle icon click for mute toggle (T025)
   */
  const handleIconClick = useCallback(() => {
    if (onMuteToggle) {
      onMuteToggle()
    }
  }, [onMuteToggle])

  return (
    <div className={cn('flex items-center gap-2', className)}>
      {/* Volume Icon - clickable for mute toggle (T024, T025) */}
      <button
        type="button"
        onClick={handleIconClick}
        disabled={disabled || !onMuteToggle}
        className={cn(
          'rounded p-1 transition-colors',
          !disabled && onMuteToggle && 'hover:bg-muted cursor-pointer',
          disabled && 'cursor-not-allowed opacity-50',
          isMuted && 'text-destructive'
        )}
        title={isMuted ? '取消靜音' : '靜音'}
      >
        <VolumeIcon className={cn(currentSize.icon, 'text-muted-foreground')} />
      </button>

      {/* Volume Slider (T023) */}
      <input
        type="range"
        min="0"
        max="1"
        step="0.01"
        value={isMuted ? 0 : value}
        onChange={handleSliderChange}
        disabled={disabled}
        className={cn(
          'cursor-pointer appearance-none rounded-full bg-muted',
          'focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2',
          '[&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:w-3',
          '[&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary',
          '[&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:transition-transform',
          '[&::-webkit-slider-thumb]:hover:scale-110',
          '[&::-moz-range-thumb]:h-3 [&::-moz-range-thumb]:w-3 [&::-moz-range-thumb]:rounded-full',
          '[&::-moz-range-thumb]:bg-primary [&::-moz-range-thumb]:border-0',
          disabled && 'cursor-not-allowed opacity-50',
          currentSize.slider
        )}
        title={formatPercentage(value)}
      />

      {/* Percentage Display (T026) */}
      {showPercentage && (
        <span
          className={cn(
            'text-center text-muted-foreground tabular-nums',
            currentSize.percentage
          )}
        >
          {formatPercentage(isMuted ? 0 : value)}
        </span>
      )}
    </div>
  )
}

export default VolumeSlider
