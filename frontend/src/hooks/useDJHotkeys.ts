/**
 * DJ Hotkeys Hook
 * Feature: 010-magic-dj-controller
 *
 * T006: Keydown event listeners for DJ control hotkeys.
 * T019: Track hotkey bindings (1-5).
 * T025: Mode toggle hotkey (M).
 */

import { useCallback, useEffect, useMemo } from 'react'

import { useMagicDJStore, OperationPriority } from '@/stores/magicDJStore'
import type { DJSettings } from '@/types/magic-dj'

// =============================================================================
// Types
// =============================================================================

export interface DJHotkeyActions {
  /** Triggered when Force Submit (Space) is pressed */
  onForceSubmit?: () => void
  /** Triggered when Interrupt (Escape) is pressed */
  onInterrupt?: () => void
  /** Triggered when Filler Sound (F) is pressed */
  onFillerSound?: () => void
  /** Triggered when Rescue Wait (W) is pressed */
  onRescueWait?: () => void
  /** Triggered when Rescue End (E) is pressed */
  onRescueEnd?: () => void
  /** Triggered when Mode Toggle (M) is pressed */
  onToggleMode?: () => void
  /** Triggered when Track hotkey (1-5) is pressed */
  onPlayTrack?: (trackIndex: number) => void
}

export interface UseDJHotkeysOptions {
  /** Whether hotkeys are enabled */
  enabled?: boolean
  /** Custom hotkey configuration (overrides store settings) */
  hotkeys?: Partial<DJSettings['hotkeys']>
}

// =============================================================================
// Hook Implementation
// =============================================================================

export function useDJHotkeys(
  actions: DJHotkeyActions,
  options: UseDJHotkeysOptions = {}
): void {
  const { enabled = true, hotkeys: customHotkeys } = options

  const { settings, currentMode, queueOperation, processOperationQueue } =
    useMagicDJStore()

  // Merge custom hotkeys with store settings
  const hotkeys = useMemo(
    () => ({ ...settings.hotkeys, ...customHotkeys }),
    [settings.hotkeys, customHotkeys]
  )

  // Handle keydown events
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return

      // Ignore if typing in input/textarea
      const target = event.target as HTMLElement
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return
      }

      // Ignore key repeats
      if (event.repeat) return

      const key = event.key

      // === Control Hotkeys ===

      // Force Submit (Space) - only in AI mode
      if (key === hotkeys.forceSubmit && currentMode === 'ai-conversation') {
        event.preventDefault()

        // Queue operation with priority
        const canExecute = queueOperation({
          type: 'force_submit',
          priority: OperationPriority.FORCE_SUBMIT,
        })

        if (canExecute) {
          actions.onForceSubmit?.()
        } else {
          // Process queue after debounce window
          setTimeout(() => {
            const op = processOperationQueue()
            if (op?.type === 'force_submit') {
              actions.onForceSubmit?.()
            } else if (op?.type === 'interrupt') {
              actions.onInterrupt?.()
            } else if (op?.type === 'emergency_end') {
              actions.onRescueEnd?.()
            }
          }, 100)
        }
        return
      }

      // Interrupt (Escape)
      if (key === hotkeys.interrupt) {
        event.preventDefault()

        // Interrupt has highest priority - always execute
        const canExecute = queueOperation({
          type: 'interrupt',
          priority: OperationPriority.INTERRUPT,
        })

        if (canExecute) {
          actions.onInterrupt?.()
        } else {
          // Process queue - interrupt will win
          const op = processOperationQueue()
          if (op?.type === 'interrupt') {
            actions.onInterrupt?.()
          }
        }
        return
      }

      // Toggle Mode (M)
      if (hotkeys.toggleMode && key.toLowerCase() === hotkeys.toggleMode.toLowerCase()) {
        event.preventDefault()
        actions.onToggleMode?.()
        return
      }

      // === Sound Hotkeys ===

      // Filler Sound (F)
      if (hotkeys.fillerSound && key.toLowerCase() === hotkeys.fillerSound.toLowerCase()) {
        event.preventDefault()

        const canExecute = queueOperation({
          type: 'playback',
          priority: OperationPriority.PLAYBACK,
        })

        if (canExecute) {
          actions.onFillerSound?.()
        }
        return
      }

      // Rescue Wait (W)
      if (hotkeys.rescueWait && key.toLowerCase() === hotkeys.rescueWait.toLowerCase()) {
        event.preventDefault()

        const canExecute = queueOperation({
          type: 'playback',
          priority: OperationPriority.PLAYBACK,
        })

        if (canExecute) {
          actions.onRescueWait?.()
        }
        return
      }

      // Rescue End (E)
      if (hotkeys.rescueEnd && key.toLowerCase() === hotkeys.rescueEnd.toLowerCase()) {
        event.preventDefault()

        // Emergency End has high priority
        const canExecute = queueOperation({
          type: 'emergency_end',
          priority: OperationPriority.EMERGENCY_END,
        })

        if (canExecute) {
          actions.onRescueEnd?.()
        } else {
          // Process queue - emergency end may win
          setTimeout(() => {
            const op = processOperationQueue()
            if (op?.type === 'emergency_end') {
              actions.onRescueEnd?.()
            } else if (op?.type === 'interrupt') {
              actions.onInterrupt?.()
            }
          }, 100)
        }
        return
      }

      // === Track Hotkeys (1-5) ===

      const trackHotkeys = [
        hotkeys.track1,
        hotkeys.track2,
        hotkeys.track3,
        hotkeys.track4,
        hotkeys.track5,
      ]

      const trackIndex = trackHotkeys.indexOf(key)
      if (trackIndex !== -1) {
        event.preventDefault()

        const canExecute = queueOperation({
          type: 'playback',
          priority: OperationPriority.PLAYBACK,
          trackId: `track_${trackIndex + 1}`,
        })

        if (canExecute) {
          actions.onPlayTrack?.(trackIndex)
        }
        return
      }
    },
    [
      enabled,
      hotkeys,
      currentMode,
      actions,
      queueOperation,
      processOperationQueue,
    ]
  )

  // Register keydown listener
  useEffect(() => {
    if (!enabled) return

    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [enabled, handleKeyDown])
}

export default useDJHotkeys
