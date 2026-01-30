/**
 * Cue List Hook
 * Feature: 010-magic-dj-controller
 *
 * T030: Manages CueList state for prerecorded mode.
 * Provides actions for add, remove, reorder, playback control,
 * and integrates with useMultiTrackPlayer for audio playback.
 */

import { useCallback, useEffect } from 'react'

import {
  useMagicDJStore,
  selectCueList,
  selectCueListRemainingCount,
} from '@/stores/magicDJStore'
import type { CueItem } from '@/types/magic-dj'

// =============================================================================
// Types
// =============================================================================

export interface UseCueListReturn {
  /** Current cue list */
  cueList: ReturnType<typeof selectCueList>
  /** Number of remaining items to play */
  remainingCount: number
  /** Add a track to the end of the cue list */
  addToCueList: (trackId: string) => void
  /** Remove an item from the cue list */
  removeFromCueList: (cueItemId: string) => void
  /** Reorder items within the cue list */
  reorderCueList: (activeId: string, overId: string) => void
  /** Play the next cue item, returns the item or null if at end */
  playNextCue: () => CueItem | null
  /** Reset playback position to the beginning */
  resetCuePosition: () => void
  /** Clear all items from the cue list */
  clearCueList: () => void
  /** Advance position after current item finishes playing */
  advanceCuePosition: () => void
  /** Check if cue list has reached the end */
  isAtEnd: boolean
  /** Check if cue list is empty */
  isEmpty: boolean
  /** Get the current playing cue item */
  currentItem: CueItem | null
}

// =============================================================================
// Hook Implementation
// =============================================================================

export function useCueList(): UseCueListReturn {
  const cueList = useMagicDJStore(selectCueList)
  const remainingCount = useMagicDJStore(selectCueListRemainingCount)

  const {
    tracks,
    addToCueList: storeAddToCueList,
    removeFromCueList: storeRemoveFromCueList,
    reorderCueList: storeReorderCueList,
    playNextCue: storePlayNextCue,
    resetCuePosition: storeResetCuePosition,
    clearCueList: storeClearCueList,
    advanceCuePosition: storeAdvanceCuePosition,
    validateCueList,
  } = useMagicDJStore()

  // Validate cue list when tracks change (EC-006)
  useEffect(() => {
    validateCueList()
  }, [tracks, validateCueList])

  const addToCueList = useCallback(
    (trackId: string) => {
      storeAddToCueList(trackId)
    },
    [storeAddToCueList]
  )

  const removeFromCueList = useCallback(
    (cueItemId: string) => {
      storeRemoveFromCueList(cueItemId)
    },
    [storeRemoveFromCueList]
  )

  const reorderCueList = useCallback(
    (activeId: string, overId: string) => {
      storeReorderCueList(activeId, overId)
    },
    [storeReorderCueList]
  )

  const playNextCue = useCallback((): CueItem | null => {
    return storePlayNextCue()
  }, [storePlayNextCue])

  const resetCuePosition = useCallback(() => {
    storeResetCuePosition()
  }, [storeResetCuePosition])

  const clearCueList = useCallback(() => {
    storeClearCueList()
  }, [storeClearCueList])

  const advanceCuePosition = useCallback(() => {
    storeAdvanceCuePosition()
  }, [storeAdvanceCuePosition])

  const isAtEnd =
    cueList.items.length > 0 &&
    cueList.currentPosition >= cueList.items.length - 1

  const isEmpty = cueList.items.length === 0

  const currentItem =
    cueList.currentPosition >= 0 && cueList.currentPosition < cueList.items.length
      ? cueList.items[cueList.currentPosition]
      : null

  return {
    cueList,
    remainingCount,
    addToCueList,
    removeFromCueList,
    reorderCueList,
    playNextCue,
    resetCuePosition,
    clearCueList,
    advanceCuePosition,
    isAtEnd,
    isEmpty,
    currentItem,
  }
}

export default useCueList
