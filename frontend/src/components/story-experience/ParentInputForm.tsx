/**
 * ParentInputForm - Story Experience input form
 * Feature: 016-story-experience-mvp
 *
 * Form for parents to input story generation parameters.
 */

import { useState } from 'react'

import { useStoryExperienceStore } from '@/stores/storyExperienceStore'
import type { ContentType } from '@/types/story-experience'
import { EMOTIONS_OPTIONS, VALUES_OPTIONS } from '@/types/story-experience'

function ChipSelector({
  label,
  options,
  selected,
  onToggle,
}: {
  label: string
  options: readonly string[]
  selected: string[]
  onToggle: (value: string) => void
}) {
  return (
    <div>
      <label className="mb-1.5 block text-sm font-medium">{label}</label>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => {
          const isSelected = selected.includes(option)
          return (
            <button
              key={option}
              type="button"
              onClick={() => onToggle(option)}
              className={`rounded-full border px-3 py-1 text-sm transition-colors ${
                isSelected
                  ? 'border-primary bg-primary text-primary-foreground'
                  : 'border-border bg-background text-foreground hover:bg-accent'
              }`}
            >
              {option}
            </button>
          )
        })}
      </div>
    </div>
  )
}

export function ParentInputForm() {
  const { formData, setFormData, generateContent, isGenerating, error, clearError } =
    useStoryExperienceStore()

  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

  const handleToggleValue = (value: string) => {
    const current = formData.values
    const updated = current.includes(value)
      ? current.filter((v) => v !== value)
      : [...current, value]
    setFormData({ values: updated })
  }

  const handleToggleEmotion = (emotion: string) => {
    const current = formData.emotions
    const updated = current.includes(emotion)
      ? current.filter((e) => e !== emotion)
      : [...current, emotion]
    setFormData({ emotions: updated })
  }

  const validate = (): boolean => {
    const errors: Record<string, string> = {}
    if (!formData.age) errors.age = '請選擇年齡'
    if (!formData.educational_content.trim()) errors.educational_content = '請輸入教導內容'
    if (formData.values.length === 0) errors.values = '請選擇至少一個價值觀'
    if (formData.emotions.length === 0) errors.emotions = '請選擇至少一個情緒認知'
    if (!formData.favorite_character.trim()) errors.favorite_character = '請輸入喜愛角色'
    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()
    if (!validate()) return
    await generateContent()
  }

  return (
    <form onSubmit={handleSubmit} className="mx-auto max-w-2xl space-y-5">
      <h2 className="text-lg font-semibold">故事體驗 — 輸入參數</h2>

      {/* Age selector */}
      <div>
        <label htmlFor="age" className="mb-1.5 block text-sm font-medium">
          孩子年齡 *
        </label>
        <select
          id="age"
          value={formData.age ?? ''}
          onChange={(e) => setFormData({ age: e.target.value ? Number(e.target.value) : null })}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        >
          <option value="">請選擇年齡</option>
          {Array.from({ length: 11 }, (_, i) => i + 2).map((age) => (
            <option key={age} value={age}>
              {age} 歲
            </option>
          ))}
        </select>
        {validationErrors.age && (
          <p className="mt-1 text-xs text-destructive">{validationErrors.age}</p>
        )}
      </div>

      {/* Educational content */}
      <div>
        <label htmlFor="educational_content" className="mb-1.5 block text-sm font-medium">
          教導內容 *
        </label>
        <input
          id="educational_content"
          type="text"
          placeholder="例如：認識顏色、學習數數、認識動物"
          value={formData.educational_content}
          onChange={(e) => setFormData({ educational_content: e.target.value })}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        />
        {validationErrors.educational_content && (
          <p className="mt-1 text-xs text-destructive">{validationErrors.educational_content}</p>
        )}
      </div>

      {/* Values */}
      <div>
        <ChipSelector
          label="價值觀 * (可多選)"
          options={VALUES_OPTIONS}
          selected={formData.values}
          onToggle={handleToggleValue}
        />
        {validationErrors.values && (
          <p className="mt-1 text-xs text-destructive">{validationErrors.values}</p>
        )}
      </div>

      {/* Emotions */}
      <div>
        <ChipSelector
          label="情緒認知 * (可多選)"
          options={EMOTIONS_OPTIONS}
          selected={formData.emotions}
          onToggle={handleToggleEmotion}
        />
        {validationErrors.emotions && (
          <p className="mt-1 text-xs text-destructive">{validationErrors.emotions}</p>
        )}
      </div>

      {/* Favorite character */}
      <div>
        <label htmlFor="favorite_character" className="mb-1.5 block text-sm font-medium">
          喜愛角色 *
        </label>
        <input
          id="favorite_character"
          type="text"
          placeholder="例如：小恐龍、公主、太空人、小貓咪"
          value={formData.favorite_character}
          onChange={(e) => setFormData({ favorite_character: e.target.value })}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        />
        {validationErrors.favorite_character && (
          <p className="mt-1 text-xs text-destructive">{validationErrors.favorite_character}</p>
        )}
      </div>

      {/* Content type */}
      <div>
        <label className="mb-1.5 block text-sm font-medium">內容形式 *</label>
        <div className="flex gap-4">
          {(['story', 'song'] as ContentType[]).map((type) => (
            <label key={type} className="flex items-center gap-2 text-sm">
              <input
                type="radio"
                name="content_type"
                value={type}
                checked={formData.content_type === type}
                onChange={() => setFormData({ content_type: type })}
                className="accent-primary"
              />
              {type === 'story' ? '故事' : '兒歌'}
            </label>
          ))}
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="rounded-md border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Submit button */}
      <button
        type="submit"
        disabled={isGenerating}
        className="w-full rounded-md bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
      >
        {isGenerating ? '生成中...' : '生成內容'}
      </button>
    </form>
  )
}
