/**
 * Voice Name Editor Component
 *
 * Feature: 013-tts-role-mgmt
 * T017: Inline editor for custom voice display names
 */

import { useState, useRef, useEffect, useCallback } from 'react'
import { Pencil, Check, X } from 'lucide-react'

interface VoiceNameEditorProps {
  voiceCacheId: string
  originalName: string
  customName: string | null
  onSave: (customName: string | null) => Promise<void>
}

export function VoiceNameEditor({
  originalName,
  customName,
  onSave,
}: VoiceNameEditorProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [value, setValue] = useState(customName || '')
  const [isSaving, setIsSaving] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const displayName = customName || originalName

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [isEditing])

  const handleStartEdit = useCallback(() => {
    setValue(customName || originalName)
    setIsEditing(true)
  }, [customName, originalName])

  const handleSave = useCallback(async () => {
    setIsSaving(true)
    try {
      // Trim and check if different from original
      const trimmedValue = value.trim()
      const newCustomName = trimmedValue === originalName || trimmedValue === '' ? null : trimmedValue
      await onSave(newCustomName)
      setIsEditing(false)
    } catch (error) {
      console.error('Failed to save custom name:', error)
    } finally {
      setIsSaving(false)
    }
  }, [value, originalName, onSave])

  const handleCancel = useCallback(() => {
    setIsEditing(false)
    setValue(customName || '')
  }, [customName])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') {
        handleSave()
      } else if (e.key === 'Escape') {
        handleCancel()
      }
    },
    [handleSave, handleCancel]
  )

  if (isEditing) {
    return (
      <div className="flex items-center gap-2">
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          maxLength={50}
          disabled={isSaving}
          className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
          placeholder={originalName}
        />
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="p-1 text-green-600 hover:bg-green-50 rounded dark:hover:bg-green-900/20"
          title="儲存"
        >
          <Check className="w-4 h-4" />
        </button>
        <button
          onClick={handleCancel}
          disabled={isSaving}
          className="p-1 text-gray-500 hover:bg-gray-100 rounded dark:hover:bg-gray-700"
          title="取消"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2 group">
      <span className="text-sm font-medium text-gray-900 dark:text-white">
        {displayName}
      </span>
      {customName && (
        <span className="text-xs text-gray-500 dark:text-gray-400">
          ({originalName})
        </span>
      )}
      <button
        onClick={handleStartEdit}
        className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded opacity-0 group-hover:opacity-100 transition-opacity dark:hover:bg-gray-700 dark:hover:text-gray-300"
        title="編輯顯示名稱"
      >
        <Pencil className="w-3.5 h-3.5" />
      </button>
    </div>
  )
}
