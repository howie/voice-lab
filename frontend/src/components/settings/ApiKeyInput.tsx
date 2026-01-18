/**
 * ApiKeyInput Component
 * T032: Secure input field for API keys with show/hide toggle
 */

import { useState, ChangeEvent, KeyboardEvent } from 'react'
import { Eye, EyeOff, Key, Loader2 } from 'lucide-react'

interface ApiKeyInputProps {
  value: string
  onChange: (value: string) => void
  onSubmit?: () => void
  placeholder?: string
  disabled?: boolean
  isValidating?: boolean
  error?: string | null
  maxLength?: number
}

export function ApiKeyInput({
  value,
  onChange,
  onSubmit,
  placeholder = 'Enter your API key',
  disabled = false,
  isValidating = false,
  error,
  maxLength = 256,
}: ApiKeyInputProps) {
  const [showKey, setShowKey] = useState(false)

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    if (newValue.length <= maxLength) {
      onChange(newValue)
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && onSubmit && !disabled && !isValidating) {
      e.preventDefault()
      onSubmit()
    }
  }

  const toggleShowKey = () => {
    setShowKey(!showKey)
  }

  return (
    <div className="space-y-2">
      <div className="relative">
        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
          <Key className="h-4 w-4 text-muted-foreground" />
        </div>
        <input
          type={showKey ? 'text' : 'password'}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled || isValidating}
          className={`
            w-full rounded-lg border bg-background py-2.5 pl-10 pr-20 text-sm
            focus:outline-none focus:ring-2 focus:ring-primary
            disabled:cursor-not-allowed disabled:opacity-50
            ${error ? 'border-destructive focus:ring-destructive' : 'border-input'}
          `}
          autoComplete="off"
          spellCheck={false}
        />
        <div className="absolute inset-y-0 right-0 flex items-center gap-1 pr-2">
          {isValidating && (
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          )}
          <button
            type="button"
            onClick={toggleShowKey}
            disabled={disabled}
            className="rounded p-1 hover:bg-muted disabled:opacity-50"
            aria-label={showKey ? 'Hide API key' : 'Show API key'}
          >
            {showKey ? (
              <EyeOff className="h-4 w-4 text-muted-foreground" />
            ) : (
              <Eye className="h-4 w-4 text-muted-foreground" />
            )}
          </button>
        </div>
      </div>

      {error && (
        <p className="text-xs text-destructive">{error}</p>
      )}

      <p className="text-xs text-muted-foreground">
        Your API key is encrypted and stored securely.
      </p>
    </div>
  )
}
