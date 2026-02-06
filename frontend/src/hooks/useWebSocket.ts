/**
 * WebSocket hook for real-time communication.
 * Feature: 004-interaction-module
 *
 * T022: Provides WebSocket connection management with auto-reconnection
 * and typed message handling.
 */

import { useCallback, useEffect, useRef, useState } from 'react'

import type { ConnectionStatus, WSMessage, WSMessageType } from '@/types/interaction'

// =============================================================================
// Types
// =============================================================================

export interface UseWebSocketOptions {
  /** WebSocket URL to connect to */
  url: string
  /** Auto-connect on mount (default: false) */
  autoConnect?: boolean
  /** Auto-reconnect on disconnect (default: true) */
  autoReconnect?: boolean
  /** Max reconnection attempts (default: 5) */
  maxReconnectAttempts?: number
  /** Reconnection delay in ms (default: 1000) */
  reconnectDelay?: number
  /** Heartbeat interval in ms (default: 30000) */
  heartbeatInterval?: number
  /** Message handler */
  onMessage?: (message: WSMessage) => void
  /** Connection status change handler */
  onStatusChange?: (status: ConnectionStatus) => void
  /** Error handler */
  onError?: (error: Event) => void
}

export interface UseWebSocketReturn {
  /** Current connection status */
  status: ConnectionStatus
  /** Connect to WebSocket */
  connect: () => void
  /** Disconnect from WebSocket */
  disconnect: () => void
  /** Send a JSON message */
  sendMessage: <T>(type: WSMessageType, data: T) => void
  /** Send raw binary data */
  sendBinary: (data: ArrayBuffer | Blob) => void
  /** Last error message */
  error: string | null
}

// =============================================================================
// Hook Implementation
// =============================================================================

export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  const {
    url,
    autoConnect = false,
    autoReconnect = true,
    maxReconnectAttempts = 5,
    reconnectDelay = 1000,
    heartbeatInterval = 30000,
    onMessage,
    onStatusChange,
    onError,
  } = options

  const [status, setStatus] = useState<ConnectionStatus>('disconnected')
  const [error, setError] = useState<string | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const heartbeatTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const isManualDisconnectRef = useRef(false)
  const connectRef = useRef<() => void>(() => {})
  const suppressWarningsRef = useRef(false)

  // Update status and notify
  const updateStatus = useCallback(
    (newStatus: ConnectionStatus) => {
      setStatus(newStatus)
      onStatusChange?.(newStatus)
    },
    [onStatusChange]
  )

  // Clear all timeouts
  const clearTimeouts = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current)
      heartbeatTimeoutRef.current = null
    }
  }, [])

  // Start heartbeat
  const startHeartbeat = useCallback(() => {
    if (heartbeatInterval <= 0) return

    heartbeatTimeoutRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping', data: {} }))
      }
    }, heartbeatInterval)
  }, [heartbeatInterval])

  // Handle reconnection
  const attemptReconnect = useCallback(() => {
    if (
      !autoReconnect ||
      isManualDisconnectRef.current ||
      reconnectAttemptsRef.current >= maxReconnectAttempts
    ) {
      if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
        setError(`Failed to reconnect after ${maxReconnectAttempts} attempts`)
        updateStatus('error')
      }
      return
    }

    reconnectAttemptsRef.current += 1
    const delay = reconnectDelay * Math.pow(1.5, reconnectAttemptsRef.current - 1)

    reconnectTimeoutRef.current = setTimeout(() => {
      if (!isManualDisconnectRef.current) {
        connectRef.current()
      }
    }, delay)
  }, [autoReconnect, maxReconnectAttempts, reconnectDelay, updateStatus])

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    // Close existing connection if any
    if (wsRef.current) {
      wsRef.current.close()
    }

    clearTimeouts()
    isManualDisconnectRef.current = false
    suppressWarningsRef.current = false
    setError(null)
    updateStatus('connecting')

    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        reconnectAttemptsRef.current = 0
        updateStatus('connected')
        startHeartbeat()
      }

      ws.onclose = (event) => {
        clearTimeouts()

        if (!isManualDisconnectRef.current) {
          // Server-initiated application errors (4000-4099): don't reconnect
          // These are permanent errors like invalid config or missing credentials
          if (event.code >= 4000 && event.code < 4100) {
            setError(event.reason || 'Connection rejected by server')
            updateStatus('error')
            return
          }
          updateStatus('disconnected')
          attemptReconnect()
        }
      }

      ws.onerror = (event) => {
        setError('WebSocket connection error')
        onError?.(event)
        updateStatus('error')
      }

      ws.onmessage = (event) => {
        try {
          // Handle binary messages
          if (event.data instanceof Blob) {
            event.data.arrayBuffer().then((buffer) => {
              onMessage?.({
                type: 'audio',
                data: { audio: buffer, format: 'pcm16' },
              })
            })
            return
          }

          // Handle JSON messages
          const message = JSON.parse(event.data) as WSMessage
          onMessage?.(message)
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e)
        }
      }
    } catch (e) {
      setError(`Failed to connect: ${e}`)
      updateStatus('error')
    }
  }, [url, clearTimeouts, updateStatus, startHeartbeat, attemptReconnect, onMessage, onError])

  // Keep ref in sync so attemptReconnect can call connect without circular dependency
  connectRef.current = connect

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    isManualDisconnectRef.current = true
    suppressWarningsRef.current = true
    clearTimeouts()

    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect')
      wsRef.current = null
    }

    updateStatus('disconnected')
  }, [clearTimeouts, updateStatus])

  // Send JSON message
  const sendMessage = useCallback(<T,>(type: WSMessageType, data: T) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) {
      if (!suppressWarningsRef.current) {
        console.warn('WebSocket is not connected')
      }
      return
    }

    const message: WSMessage<T> = { type, data }
    wsRef.current.send(JSON.stringify(message))
  }, [])

  // Send binary data
  const sendBinary = useCallback((data: ArrayBuffer | Blob) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) {
      if (!suppressWarningsRef.current) {
        console.warn('WebSocket is not connected')
      }
      return
    }

    wsRef.current.send(data)
  }, [])

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (autoConnect) {
      connect()
    }

    return () => {
      disconnect()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoConnect])

  return {
    status,
    connect,
    disconnect,
    sendMessage,
    sendBinary,
    error,
  }
}

export default useWebSocket
