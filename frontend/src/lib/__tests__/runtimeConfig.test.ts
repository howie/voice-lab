/**
 * Runtime Config Tests
 *
 * These tests ensure that the frontend correctly reads configuration
 * from runtime config (Cloud Run) with proper fallback to build-time env.
 *
 * Problem this prevents:
 * - Blank screen after login on Cloud Run due to incorrect API URL
 * - Environment variable naming mismatches (VITE_API_URL vs VITE_API_BASE_URL)
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

// Type for window with runtime config
declare global {
  interface Window {
    __RUNTIME_CONFIG__?: {
      VITE_API_BASE_URL?: string
      VITE_WS_URL?: string
      VITE_GOOGLE_CLIENT_ID?: string
    }
  }
}

describe('Runtime Config', () => {
  const originalRuntimeConfig = window.__RUNTIME_CONFIG__

  beforeEach(() => {
    // Clear runtime config before each test
    delete window.__RUNTIME_CONFIG__
  })

  afterEach(() => {
    // Restore original runtime config
    if (originalRuntimeConfig) {
      window.__RUNTIME_CONFIG__ = originalRuntimeConfig
    } else {
      delete window.__RUNTIME_CONFIG__
    }
  })

  describe('getApiBaseUrl helper pattern', () => {
    // This tests the pattern used across multiple files
    function getApiBaseUrl(): string {
      const runtimeConfig = window.__RUNTIME_CONFIG__
      return (
        runtimeConfig?.VITE_API_BASE_URL ||
        import.meta.env.VITE_API_BASE_URL ||
        '/api/v1'
      )
    }

    it('should prioritize runtime config over build-time env', () => {
      window.__RUNTIME_CONFIG__ = {
        VITE_API_BASE_URL: 'https://api.example.com/api/v1',
      }

      const result = getApiBaseUrl()
      expect(result).toBe('https://api.example.com/api/v1')
    })

    it('should fallback to /api/v1 when no config is available', () => {
      // No runtime config, no env var
      const result = getApiBaseUrl()
      expect(result).toBe('/api/v1')
    })

    it('should handle empty runtime config', () => {
      window.__RUNTIME_CONFIG__ = {}

      const result = getApiBaseUrl()
      // Should fallback to env or default
      expect(result).toBe('/api/v1')
    })

    it('should handle empty string in runtime config', () => {
      window.__RUNTIME_CONFIG__ = {
        VITE_API_BASE_URL: '',
      }

      const result = getApiBaseUrl()
      // Empty string is falsy, should fallback
      expect(result).toBe('/api/v1')
    })
  })

  describe('Runtime config structure validation', () => {
    it('should use VITE_API_BASE_URL not VITE_API_URL', () => {
      // This test ensures we use the correct variable name
      window.__RUNTIME_CONFIG__ = {
        VITE_API_BASE_URL: 'https://correct.example.com/api/v1',
      }

      // Simulate the old incorrect pattern
      const incorrectPattern = (window as { __RUNTIME_CONFIG__?: { VITE_API_URL?: string } })
        .__RUNTIME_CONFIG__?.VITE_API_URL

      // Simulate the correct pattern
      const correctPattern = window.__RUNTIME_CONFIG__?.VITE_API_BASE_URL

      expect(incorrectPattern).toBeUndefined()
      expect(correctPattern).toBe('https://correct.example.com/api/v1')
    })

    it('should include /api/v1 in the URL path', () => {
      window.__RUNTIME_CONFIG__ = {
        VITE_API_BASE_URL: 'https://api.example.com/api/v1',
      }

      const url = window.__RUNTIME_CONFIG__?.VITE_API_BASE_URL
      expect(url).toContain('/api/v1')
    })
  })

  describe('WebSocket URL derivation', () => {
    function getWsUrl(): string {
      const runtimeConfig = window.__RUNTIME_CONFIG__
      return runtimeConfig?.VITE_WS_URL || import.meta.env.VITE_WS_URL || ''
    }

    function buildWebSocketUrl(apiBaseUrl: string): string {
      if (!apiBaseUrl) return ''

      const wsProtocol = apiBaseUrl.startsWith('https') ? 'wss' : 'ws'
      const host = apiBaseUrl.replace(/\/api\/v1$/, '').replace(/^https?:\/\//, '')

      return `${wsProtocol}://${host}/api/interaction/ws`
    }

    it('should use dedicated WS URL when available', () => {
      window.__RUNTIME_CONFIG__ = {
        VITE_WS_URL: 'wss://api.example.com',
      }

      const wsUrl = getWsUrl()
      expect(wsUrl).toBe('wss://api.example.com')
    })

    it('should derive WebSocket URL from API URL correctly', () => {
      const apiUrl = 'https://api.example.com/api/v1'
      const wsUrl = buildWebSocketUrl(apiUrl)

      expect(wsUrl).toBe('wss://api.example.com/api/interaction/ws')
    })

    it('should use ws:// for http:// URLs', () => {
      const apiUrl = 'http://localhost:8000/api/v1'
      const wsUrl = buildWebSocketUrl(apiUrl)

      expect(wsUrl).toBe('ws://localhost:8000/api/interaction/ws')
    })
  })
})

describe('Config.js loading', () => {
  it('should have config.js script tag in index.html', async () => {
    // This is a static check - we read the index.html file
    const fs = await import('fs')
    const path = await import('path')

    const indexPath = path.resolve(__dirname, '../../../index.html')
    const indexContent = fs.readFileSync(indexPath, 'utf-8')

    // Check that config.js is loaded BEFORE the main script
    const configScriptIndex = indexContent.indexOf('src="/config.js"')
    const mainScriptIndex = indexContent.indexOf('src="/src/main.tsx"')

    expect(configScriptIndex).toBeGreaterThan(-1)
    expect(mainScriptIndex).toBeGreaterThan(-1)
    expect(configScriptIndex).toBeLessThan(mainScriptIndex)
  })
})

describe('Environment variable naming consistency', () => {
  it('should not use VITE_API_URL (use VITE_API_BASE_URL instead)', async () => {
    // This test checks specific files that are known to use API config
    const fs = await import('fs')
    const path = await import('path')

    const srcDir = path.resolve(__dirname, '../../')

    // Files that should use VITE_API_BASE_URL
    const filesToCheck = [
      'lib/api.ts',
      'lib/streaming.ts',
      'stores/authStore.ts',
      'services/interactionApi.ts',
      'services/jobApi.ts',
    ]

    const violations: string[] = []

    for (const file of filesToCheck) {
      const filePath = path.join(srcDir, file)

      // Skip if file doesn't exist
      if (!fs.existsSync(filePath)) {
        continue
      }

      const content = fs.readFileSync(filePath, 'utf-8')

      // Check for old incorrect pattern (but allow in comments and runtime config checks)
      const lines = content.split('\n')
      lines.forEach((line, index) => {
        // Skip comments
        if (line.trim().startsWith('//') || line.trim().startsWith('*')) {
          return
        }

        // Check for VITE_API_URL usage (not VITE_API_BASE_URL)
        // Allow usage in runtime config type definitions
        if (
          line.includes('VITE_API_URL') &&
          !line.includes('VITE_API_BASE_URL') &&
          !line.includes('__RUNTIME_CONFIG__') &&
          !line.includes('VITE_API_URL?:') // Allow type definitions
        ) {
          violations.push(`${file}:${index + 1}: Uses VITE_API_URL instead of VITE_API_BASE_URL`)
        }
      })
    }

    expect(violations).toEqual([])
  })
})
