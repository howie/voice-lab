/**
 * TextInput Component
 * T040: Create TextInput component (textarea with char counter)
 */

import { ChangeEvent } from 'react'
import { AlertCircle } from 'lucide-react'

interface TextInputProps {
  value: string
  onChange: (value: string) => void
  maxLength?: number
  recommendedMaxLength?: number
  warningMessage?: string
  placeholder?: string
  disabled?: boolean
}

const MAX_TEXT_LENGTH = 5000

export function TextInput({
  value,
  onChange,
  maxLength = MAX_TEXT_LENGTH,
  recommendedMaxLength,
  warningMessage,
  placeholder = '請輸入要轉換成語音的文字...',
  disabled = false,
}: TextInputProps) {
  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value
    if (newValue.length <= maxLength) {
      onChange(newValue)
    }
  }

  const charCount = value.length
  const isNearLimit = charCount >= maxLength * 0.9
  const isAtLimit = charCount >= maxLength
  const exceedsRecommended = recommendedMaxLength ? charCount > recommendedMaxLength : false

  return (
    <div className="space-y-2">
      <textarea
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
        disabled={disabled}
        className={`
          h-40 w-full rounded-lg border bg-background p-3 text-sm
          focus:outline-none focus:ring-2 focus:ring-primary
          disabled:cursor-not-allowed disabled:opacity-50
          ${isAtLimit ? 'border-destructive' : ''}
          ${exceedsRecommended && !isAtLimit ? 'border-yellow-500' : ''}
        `}
      />

      {/* Warning message for recommended limit */}
      {exceedsRecommended && warningMessage && (
        <div className="flex items-start gap-2 rounded-md bg-yellow-50 p-3 text-xs text-yellow-800">
          <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
          <span>{warningMessage}</span>
        </div>
      )}

      <div className="flex justify-between text-xs">
        <span className="text-muted-foreground">
          {value.length === 0 && '輸入文字開始合成'}
          {exceedsRecommended && recommendedMaxLength && (
            <span className="text-yellow-600">
              （建議 {recommendedMaxLength.toLocaleString()} 字內）
            </span>
          )}
        </span>
        <span
          className={`
            ${isAtLimit ? 'text-destructive font-medium' : ''}
            ${isNearLimit && !isAtLimit ? 'text-yellow-600' : ''}
            ${!isNearLimit ? 'text-muted-foreground' : ''}
          `}
        >
          {charCount.toLocaleString()} / {maxLength.toLocaleString()} 字
        </span>
      </div>
    </div>
  )
}
