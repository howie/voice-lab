/**
 * TextInput Component
 * T040: Create TextInput component (textarea with char counter)
 */

import { ChangeEvent } from 'react'

interface TextInputProps {
  value: string
  onChange: (value: string) => void
  maxLength?: number
  placeholder?: string
  disabled?: boolean
}

const MAX_TEXT_LENGTH = 5000

export function TextInput({
  value,
  onChange,
  maxLength = MAX_TEXT_LENGTH,
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
        `}
      />
      <div className="flex justify-between text-xs">
        <span className="text-muted-foreground">
          {value.length === 0 && '輸入文字開始合成'}
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
