/**
 * ProviderSelector Component (Dropdown)
 * Feature: 003-stt-testing-module
 * T080: Rewrite ProviderSelector from cards to dropdown
 *
 * Dropdown-based provider selector that only shows providers
 * with valid credentials (has_credentials && is_valid).
 */

import { useEffect } from 'react'
import { useSTTStore } from '@/stores/sttStore'
import type { STTProviderName, STTProvider } from '@/types/stt'

interface ProviderSelectorProps {
  disabled?: boolean
  showCapabilities?: boolean
  onProviderChange?: (provider: STTProviderName) => void
}

export function ProviderSelector({
  disabled = false,
  showCapabilities = true,
  onProviderChange,
}: ProviderSelectorProps) {
  const {
    selectedProvider,
    setSelectedProvider,
    availableProviders,
    providersLoading,
    loadProviders,
  } = useSTTStore()

  useEffect(() => {
    if (availableProviders.length === 0) {
      loadProviders()
    }
  }, [availableProviders.length, loadProviders])

  const validProviders = availableProviders.filter(
    (p) => p.has_credentials && p.is_valid
  )

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const provider = e.target.value as STTProviderName
    setSelectedProvider(provider)
    onProviderChange?.(provider)
  }

  const selectedProviderInfo = validProviders.find(
    (p) => p.name === selectedProvider
  )

  if (providersLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded"></div>
      </div>
    )
  }

  if (validProviders.length === 0) {
    return (
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          選擇 Provider
        </label>
        <p className="text-sm text-amber-600 dark:text-amber-400">
          請先至 Provider 管理頁面設定 API Key
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          選擇 Provider
        </label>
        <select
          value={selectedProvider}
          onChange={handleChange}
          disabled={disabled}
          className="w-full rounded-lg border bg-background p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:cursor-not-allowed disabled:opacity-50"
        >
          {validProviders.map((provider) => (
            <option key={provider.name} value={provider.name}>
              {provider.display_name}
            </option>
          ))}
        </select>
      </div>

      {showCapabilities && selectedProviderInfo && (
        <ProviderCapabilities provider={selectedProviderInfo} />
      )}
    </div>
  )
}

interface ProviderCapabilitiesProps {
  provider: STTProvider
}

function ProviderCapabilities({ provider }: ProviderCapabilitiesProps) {
  return (
    <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
      <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
        Provider Limits
      </h4>
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-gray-500">Max File Size:</span>
          <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">
            {provider.max_file_size_mb} MB
          </span>
        </div>
        <div>
          <span className="text-gray-500">Max Duration:</span>
          <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">
            {Math.floor(provider.max_duration_sec / 60)} min
          </span>
        </div>
        <div>
          <span className="text-gray-500">Formats:</span>
          <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">
            {provider.supported_formats.slice(0, 3).join(', ')}
            {provider.supported_formats.length > 3 && '...'}
          </span>
        </div>
        <div>
          <span className="text-gray-500">Child Mode:</span>
          <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">
            {provider.supports_child_mode ? 'Yes' : 'No'}
          </span>
        </div>
      </div>
    </div>
  )
}
