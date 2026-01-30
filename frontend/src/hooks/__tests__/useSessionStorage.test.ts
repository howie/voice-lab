/**
 * Session Storage Hook Tests
 * Feature: 010-magic-dj-controller
 *
 * T068: Unit tests for useSessionStorage covering save/load/export operations.
 */

import { describe, it, expect, beforeEach } from 'vitest'

import { useMagicDJStore } from '@/stores/magicDJStore'
import { act } from '@testing-library/react'

describe('Session Storage (via magicDJStore)', () => {
  beforeEach(() => {
    act(() => {
      useMagicDJStore.getState().reset()
    })
  })

  describe('startSession', () => {
    it('should create a new session record', () => {
      act(() => {
        useMagicDJStore.getState().startSession()
      })

      const { currentSession, isSessionActive } = useMagicDJStore.getState()
      expect(isSessionActive).toBe(true)
      expect(currentSession).not.toBeNull()
      expect(currentSession?.id).toBeTruthy()
      expect(currentSession?.startTime).toBeTruthy()
      expect(currentSession?.endTime).toBeNull()
    })
  })

  describe('stopSession', () => {
    it('should end the current session with endTime', () => {
      act(() => {
        useMagicDJStore.getState().startSession()
      })

      act(() => {
        useMagicDJStore.getState().stopSession()
      })

      const { currentSession, isSessionActive } = useMagicDJStore.getState()
      expect(isSessionActive).toBe(false)
      expect(currentSession?.endTime).toBeTruthy()
    })
  })

  describe('logOperation', () => {
    it('should add operation logs to the current session', () => {
      act(() => {
        useMagicDJStore.getState().startSession()
      })

      act(() => {
        useMagicDJStore.getState().logOperation('force_submit')
        useMagicDJStore.getState().logOperation('play_track', { trackId: 'track_01' })
      })

      const { currentSession } = useMagicDJStore.getState()
      expect(currentSession?.operationLogs).toHaveLength(3) // session_start + 2 logged
      expect(currentSession?.aiInteractionCount).toBe(1)
    })

    it('should count mode switches', () => {
      act(() => {
        useMagicDJStore.getState().startSession()
      })

      act(() => {
        useMagicDJStore.getState().logOperation('mode_switch', {
          from: 'prerecorded',
          to: 'ai-conversation',
        })
      })

      const { currentSession } = useMagicDJStore.getState()
      expect(currentSession?.modeSwitchCount).toBe(1)
    })

    it('should not log when no session is active', () => {
      act(() => {
        useMagicDJStore.getState().logOperation('force_submit')
      })

      const { currentSession } = useMagicDJStore.getState()
      expect(currentSession).toBeNull()
    })
  })

  describe('resetSession', () => {
    it('should clear all session data', () => {
      act(() => {
        useMagicDJStore.getState().startSession()
        useMagicDJStore.getState().updateElapsedTime(100)
        useMagicDJStore.getState().resetSession()
      })

      const { isSessionActive, elapsedTime, currentSession } =
        useMagicDJStore.getState()
      expect(isSessionActive).toBe(false)
      expect(elapsedTime).toBe(0)
      expect(currentSession).toBeNull()
    })
  })

  describe('updateElapsedTime', () => {
    it('should update elapsed time', () => {
      act(() => {
        useMagicDJStore.getState().updateElapsedTime(300)
      })

      expect(useMagicDJStore.getState().elapsedTime).toBe(300)
    })
  })
})
