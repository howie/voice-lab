/**
 * ProviderSelector Component
 * Feature: 003-stt-testing-module
 * T032: Create ProviderSelector component
 *
 * Allows users to select an STT provider with capability indicators.
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

  const handleProviderChange = (provider: STTProviderName) => {
    setSelectedProvider(provider)
    onProviderChange?.(provider)
  }

  const selectedProviderInfo = availableProviders.find(
    (p) => p.name === selectedProvider
  )

  if (providersLoading) {
    return (
      <div className="animate-pulse">
        <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded"></div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Provider Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          STT Provider
        </label>
        <div className="grid grid-cols-3 gap-3">
          {availableProviders.map((provider) => (
            <ProviderCard
              key={provider.name}
              provider={provider}
              selected={selectedProvider === provider.name}
              disabled={disabled}
              onClick={() => handleProviderChange(provider.name)}
            />
          ))}
        </div>
      </div>

      {/* Provider Capabilities */}
      {showCapabilities && selectedProviderInfo && (
        <ProviderCapabilities provider={selectedProviderInfo} />
      )}
    </div>
  )
}

interface ProviderCardProps {
  provider: STTProvider
  selected: boolean
  disabled: boolean
  onClick: () => void
}

function ProviderCard({ provider, selected, disabled, onClick }: ProviderCardProps) {
  const hasCredentials = provider.has_credentials ?? false
  const isValid = provider.is_valid ?? false
  const isDisabled = disabled || !hasCredentials

  return (
    <button
      onClick={onClick}
      disabled={isDisabled}
      className={`
        relative p-4 rounded-lg border-2 transition-all text-left
        ${
          selected
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-950'
            : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
        }
        ${isDisabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      `}
    >
      {/* Provider Name */}
      <div className="font-medium text-gray-900 dark:text-gray-100">
        {provider.display_name}
      </div>

      {/* Credential Status */}
      {!hasCredentials && (
        <div className="mt-1 text-xs text-amber-600 dark:text-amber-400">
          尚未設定 API Key
        </div>
      )}
      {hasCredentials && !isValid && (
        <div className="mt-1 text-xs text-red-600 dark:text-red-400">
          API Key 無效
        </div>
      )}

      {/* Badges */}
      <div className="mt-2 flex flex-wrap gap-1">
        {hasCredentials && isValid && (
          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-emerald-100 dark:bg-emerald-900 text-emerald-800 dark:text-emerald-200">
            已設定
          </span>
        )}
        {provider.supports_child_mode && (
          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">
            Child Mode
          </span>
        )}
        {!provider.supports_streaming && (
          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">
            Batch Only
          </span>
        )}
      </div>

      {/* Selection indicator */}
      {selected && (
        <div className="absolute top-2 right-2">
          <svg
            className="h-5 w-5 text-blue-500"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
        </div>
      )}
    </button>
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
