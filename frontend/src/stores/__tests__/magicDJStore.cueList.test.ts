/**
 * Magic DJ Store - Cue List Tests
 * Feature: 010-magic-dj-controller
 *
 * T020/T028: Unit tests for magicDJStore cue list actions.
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { act } from '@testing-library/react'

import { useMagicDJStore } from '@/stores/magicDJStore'

describe('magicDJStore - Cue List', () => {
  beforeEach(() => {
    act(() => {
      useMagicDJStore.getState().reset()
    })
  })

  describe('addToCueList', () => {
    it('should add a track to the cue list', () => {
      act(() => {
        useMagicDJStore.getState().addToCueList('track_01_intro')
      })

      const { cueList } = useMagicDJStore.getState()
      expect(cueList.items).toHaveLength(1)
      expect(cueList.items[0].trackId).toBe('track_01_intro')
      expect(cueList.items[0].order).toBe(1)
      expect(cueList.items[0].status).toBe('pending')
    })

    it('should assign sequential order numbers', () => {
      act(() => {
        const store = useMagicDJStore.getState()
        store.addToCueList('track_01_intro')
        store.addToCueList('track_02_cleanup')
        store.addToCueList('sound_thinking')
      })

      const { cueList } = useMagicDJStore.getState()
      expect(cueList.items).toHaveLength(3)
      expect(cueList.items[0].order).toBe(1)
      expect(cueList.items[1].order).toBe(2)
      expect(cueList.items[2].order).toBe(3)
    })

    it('should allow same track multiple times (FR-036)', () => {
      act(() => {
        const store = useMagicDJStore.getState()
        store.addToCueList('track_01_intro')
        store.addToCueList('track_01_intro')
      })

      const { cueList } = useMagicDJStore.getState()
      expect(cueList.items).toHaveLength(2)
      expect(cueList.items[0].trackId).toBe('track_01_intro')
      expect(cueList.items[1].trackId).toBe('track_01_intro')
      expect(cueList.items[0].id).not.toBe(cueList.items[1].id)
    })
  })

  describe('removeFromCueList', () => {
    it('should remove an item by cue item ID', () => {
      act(() => {
        const store = useMagicDJStore.getState()
        store.addToCueList('track_01_intro')
        store.addToCueList('track_02_cleanup')
      })

      const itemId = useMagicDJStore.getState().cueList.items[0].id
      act(() => {
        useMagicDJStore.getState().removeFromCueList(itemId)
      })

      const { cueList } = useMagicDJStore.getState()
      expect(cueList.items).toHaveLength(1)
      expect(cueList.items[0].trackId).toBe('track_02_cleanup')
      expect(cueList.items[0].order).toBe(1) // Re-numbered
    })

    it('should adjust currentPosition when removing before current', () => {
      act(() => {
        const store = useMagicDJStore.getState()
        store.addToCueList('track_01_intro')
        store.addToCueList('track_02_cleanup')
        store.addToCueList('sound_thinking')
        // Play first two
        store.playNextCue()
        store.playNextCue()
      })

      const { cueList } = useMagicDJStore.getState()
      expect(cueList.currentPosition).toBe(1)

      // Remove first item (before current position)
      const firstItemId = cueList.items[0].id
      act(() => {
        useMagicDJStore.getState().removeFromCueList(firstItemId)
      })

      const updatedList = useMagicDJStore.getState().cueList
      expect(updatedList.currentPosition).toBe(0)
    })
  })

  describe('reorderCueList', () => {
    it('should reorder items and update order numbers', () => {
      act(() => {
        const store = useMagicDJStore.getState()
        store.addToCueList('track_01_intro')
        store.addToCueList('track_02_cleanup')
        store.addToCueList('sound_thinking')
      })

      const items = useMagicDJStore.getState().cueList.items
      // Move last item to first position
      act(() => {
        useMagicDJStore.getState().reorderCueList(items[2].id, items[0].id)
      })

      const reordered = useMagicDJStore.getState().cueList.items
      expect(reordered[0].trackId).toBe('sound_thinking')
      expect(reordered[1].trackId).toBe('track_01_intro')
      expect(reordered[2].trackId).toBe('track_02_cleanup')
      // Orders should be renumbered
      expect(reordered[0].order).toBe(1)
      expect(reordered[1].order).toBe(2)
      expect(reordered[2].order).toBe(3)
    })
  })

  describe('playNextCue', () => {
    it('should advance to the next item and mark it playing', () => {
      act(() => {
        const store = useMagicDJStore.getState()
        store.addToCueList('track_01_intro')
        store.addToCueList('track_02_cleanup')
      })

      let result: ReturnType<ReturnType<typeof useMagicDJStore.getState>['playNextCue']>
      act(() => {
        result = useMagicDJStore.getState().playNextCue()
      })

      expect(result!).not.toBeNull()
      expect(result!.trackId).toBe('track_01_intro')

      const { cueList } = useMagicDJStore.getState()
      expect(cueList.currentPosition).toBe(0)
      expect(cueList.items[0].status).toBe('playing')
    })

    it('should return null when at end of list', () => {
      act(() => {
        const store = useMagicDJStore.getState()
        store.addToCueList('track_01_intro')
        store.playNextCue() // Play only item
      })

      let result: ReturnType<ReturnType<typeof useMagicDJStore.getState>['playNextCue']>
      act(() => {
        result = useMagicDJStore.getState().playNextCue()
      })

      expect(result!).toBeNull()
    })

    it('should mark previous item as played when advancing', () => {
      act(() => {
        const store = useMagicDJStore.getState()
        store.addToCueList('track_01_intro')
        store.addToCueList('track_02_cleanup')
        store.playNextCue() // Play first
        store.playNextCue() // Play second
      })

      const { cueList } = useMagicDJStore.getState()
      expect(cueList.items[0].status).toBe('played')
      expect(cueList.items[1].status).toBe('playing')
    })
  })

  describe('advanceCuePosition', () => {
    it('should mark current as played', () => {
      act(() => {
        const store = useMagicDJStore.getState()
        store.addToCueList('track_01_intro')
        store.addToCueList('track_02_cleanup')
        store.playNextCue()
        store.advanceCuePosition()
      })

      const { cueList } = useMagicDJStore.getState()
      expect(cueList.items[0].status).toBe('played')
    })

    it('should reset position when at end (EC-007)', () => {
      act(() => {
        const store = useMagicDJStore.getState()
        store.addToCueList('track_01_intro')
        store.playNextCue()
        store.advanceCuePosition()
      })

      const { cueList } = useMagicDJStore.getState()
      expect(cueList.currentPosition).toBe(-1)
      expect(cueList.items[0].status).toBe('pending')
    })
  })

  describe('resetCuePosition', () => {
    it('should reset position and all statuses to pending', () => {
      act(() => {
        const store = useMagicDJStore.getState()
        store.addToCueList('track_01_intro')
        store.addToCueList('track_02_cleanup')
        store.playNextCue()
        store.playNextCue()
        store.resetCuePosition()
      })

      const { cueList } = useMagicDJStore.getState()
      expect(cueList.currentPosition).toBe(-1)
      expect(cueList.items[0].status).toBe('pending')
      expect(cueList.items[1].status).toBe('pending')
    })
  })

  describe('clearCueList', () => {
    it('should remove all items', () => {
      act(() => {
        const store = useMagicDJStore.getState()
        store.addToCueList('track_01_intro')
        store.addToCueList('track_02_cleanup')
        store.clearCueList()
      })

      const { cueList } = useMagicDJStore.getState()
      expect(cueList.items).toHaveLength(0)
      expect(cueList.currentPosition).toBe(-1)
    })
  })

  describe('validateCueList (EC-006)', () => {
    it('should mark items as invalid when track is deleted', () => {
      act(() => {
        const store = useMagicDJStore.getState()
        store.addToCueList('track_01_intro')
        store.addToCueList('track_02_cleanup')
      })

      // Remove track from sound library
      act(() => {
        useMagicDJStore.getState().removeTrack('track_01_intro')
      })

      // Validate
      act(() => {
        useMagicDJStore.getState().validateCueList()
      })

      const { cueList } = useMagicDJStore.getState()
      expect(cueList.items[0].status).toBe('invalid')
      expect(cueList.items[1].status).not.toBe('invalid')
    })
  })
})

describe('magicDJStore - Sound Library Actions', () => {
  beforeEach(() => {
    act(() => {
      useMagicDJStore.getState().reset()
    })
  })

  describe('addTrack', () => {
    it('should add a track to the sound library', () => {
      const newTrack = {
        id: 'custom_track_1',
        name: '自訂音軌',
        type: 'effect' as const,
        url: 'blob:test',
        source: 'tts' as const,
        volume: 1.0,
      }

      act(() => {
        useMagicDJStore.getState().addTrack(newTrack)
      })

      const { tracks } = useMagicDJStore.getState()
      expect(tracks.find((t) => t.id === 'custom_track_1')).toBeTruthy()
    })
  })

  describe('removeTrack', () => {
    it('should remove a track from the sound library', () => {
      const initialCount = useMagicDJStore.getState().tracks.length

      act(() => {
        useMagicDJStore.getState().removeTrack('track_01_intro')
      })

      expect(useMagicDJStore.getState().tracks).toHaveLength(initialCount - 1)
    })
  })

  describe('reorderTracks', () => {
    it('should reorder tracks by moving one to another position', () => {
      const tracks = useMagicDJStore.getState().tracks
      const firstId = tracks[0].id
      const lastId = tracks[tracks.length - 1].id

      act(() => {
        useMagicDJStore.getState().reorderTracks(lastId, firstId)
      })

      const reordered = useMagicDJStore.getState().tracks
      expect(reordered[0].id).toBe(lastId)
    })
  })
})
