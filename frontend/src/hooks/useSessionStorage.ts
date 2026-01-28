/**
 * Session Storage Hook
 * Feature: 010-magic-dj-controller
 *
 * T041: useSessionStorage hook implementing localStorage read/write for session data
 * with auto-save on operation.
 */

import { useCallback, useEffect } from 'react'

import { useMagicDJStore } from '@/stores/magicDJStore'
import type { SessionRecord } from '@/types/magic-dj'

// =============================================================================
// Constants
// =============================================================================

const STORAGE_KEY = 'magic-dj-sessions'
const MAX_STORED_SESSIONS = 10

// =============================================================================
// Types
// =============================================================================

interface StoredSessions {
  sessions: SessionRecord[]
  lastUpdated: string
}

// =============================================================================
// Hook Implementation
// =============================================================================

export function useSessionStorage() {
  const { currentSession, isSessionActive } = useMagicDJStore()

  // Load sessions from localStorage
  const loadSessions = useCallback((): SessionRecord[] => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (!stored) return []

      const data: StoredSessions = JSON.parse(stored)
      return data.sessions || []
    } catch (error) {
      console.error('Failed to load sessions from localStorage:', error)
      return []
    }
  }, [])

  // Save sessions to localStorage
  const saveSessions = useCallback((sessions: SessionRecord[]) => {
    try {
      // Keep only the most recent sessions
      const trimmedSessions = sessions.slice(-MAX_STORED_SESSIONS)

      const data: StoredSessions = {
        sessions: trimmedSessions,
        lastUpdated: new Date().toISOString(),
      }

      localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
    } catch (error) {
      console.error('Failed to save sessions to localStorage:', error)
    }
  }, [])

  // Save current session
  const saveCurrentSession = useCallback(
    (session: SessionRecord) => {
      const sessions = loadSessions()

      // Find and update existing session or add new one
      const existingIndex = sessions.findIndex((s) => s.id === session.id)
      if (existingIndex >= 0) {
        sessions[existingIndex] = session
      } else {
        sessions.push(session)
      }

      saveSessions(sessions)
    },
    [loadSessions, saveSessions]
  )

  // Delete a session
  const deleteSession = useCallback(
    (sessionId: string) => {
      const sessions = loadSessions()
      const filtered = sessions.filter((s) => s.id !== sessionId)
      saveSessions(filtered)
    },
    [loadSessions, saveSessions]
  )

  // Clear all sessions
  const clearAllSessions = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY)
  }, [])

  // Get session by ID
  const getSession = useCallback(
    (sessionId: string): SessionRecord | undefined => {
      const sessions = loadSessions()
      return sessions.find((s) => s.id === sessionId)
    },
    [loadSessions]
  )

  // Auto-save current session when it changes
  useEffect(() => {
    if (currentSession && !isSessionActive) {
      // Save when session ends (not during active session to avoid frequent writes)
      saveCurrentSession(currentSession)
    }
  }, [currentSession, isSessionActive, saveCurrentSession])

  return {
    loadSessions,
    saveCurrentSession,
    deleteSession,
    clearAllSessions,
    getSession,
  }
}

export default useSessionStorage
