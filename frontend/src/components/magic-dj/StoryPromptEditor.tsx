/**
 * Story Prompt Editor Modal Component
 * Feature: 015-magic-dj-ai-prompts
 *
 * Modal dialog for creating/editing story prompts.
 * Form: name, prompt content, category picker.
 */

import { useState, useEffect, useCallback } from 'react'
import { X } from 'lucide-react'

import { cn } from '@/lib/utils'
import type { StoryPrompt } from '@/types/magic-dj'

// =============================================================================
// Category Options
// =============================================================================

const CATEGORY_OPTIONS: { value: string; label: string; class: string }[] = [
  { value: 'adventure', label: '冒險', class: 'bg-emerald-500' },
  { value: 'activity', label: '活動', class: 'bg-amber-500' },
  { value: 'fantasy', label: '幻想', class: 'bg-violet-500' },
  { value: 'daily', label: '日常', class: 'bg-sky-500' },
]

// =============================================================================
// Types
// =============================================================================

export interface StoryPromptEditorProps {
  isOpen: boolean
  onClose: () => void
  onSave: (data: { name: string; prompt: string; category: string }) => void
  editingPrompt?: StoryPrompt | null
}

// =============================================================================
// Component
// =============================================================================

export function StoryPromptEditor({
  isOpen,
  onClose,
  onSave,
  editingPrompt,
}: StoryPromptEditorProps) {
  const [name, setName] = useState('')
  const [prompt, setPrompt] = useState('')
  const [category, setCategory] = useState('adventure')
  const [errors, setErrors] = useState<{ name?: string; prompt?: string }>({})

  // Populate form when editing
  useEffect(() => {
    if (editingPrompt) {
      setName(editingPrompt.name)
      setPrompt(editingPrompt.prompt)
      setCategory(editingPrompt.category)
    } else {
      setName('')
      setPrompt('')
      setCategory('adventure')
    }
    setErrors({})
  }, [editingPrompt, isOpen])

  const validate = useCallback((): boolean => {
    const newErrors: { name?: string; prompt?: string } = {}
    if (!name.trim()) {
      newErrors.name = '名稱不能為空'
    } else if (name.trim().length > 20) {
      newErrors.name = '名稱不能超過 20 字'
    }
    if (!prompt.trim()) {
      newErrors.prompt = '故事指令不能為空'
    } else if (prompt.trim().length > 1000) {
      newErrors.prompt = '故事指令不能超過 1000 字'
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }, [name, prompt])

  const handleSave = useCallback(() => {
    if (!validate()) return
    onSave({ name: name.trim(), prompt: prompt.trim(), category })
    onClose()
  }, [validate, onSave, name, prompt, category, onClose])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="mx-4 w-full max-w-md rounded-lg border bg-background p-6 shadow-lg">
        {/* Header */}
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">
            {editingPrompt ? '編輯故事指令' : '新增故事指令'}
          </h2>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-accent">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form */}
        <div className="space-y-4">
          {/* Name */}
          <div>
            <label className="mb-1 block text-sm font-medium">名稱</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={20}
              placeholder="例如：魔法森林"
              className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
            />
            {errors.name && (
              <p className="mt-1 text-xs text-destructive">{errors.name}</p>
            )}
            <p className="mt-1 text-xs text-muted-foreground">{name.length}/20</p>
          </div>

          {/* Prompt Content */}
          <div>
            <label className="mb-1 block text-sm font-medium">故事指令內容</label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              maxLength={1000}
              rows={5}
              placeholder="輸入故事情境描述，AI 會根據這段指令開始說故事..."
              className="w-full resize-none rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
            />
            {errors.prompt && (
              <p className="mt-1 text-xs text-destructive">{errors.prompt}</p>
            )}
            <p className="mt-1 text-xs text-muted-foreground">{prompt.length}/1000</p>
          </div>

          {/* Category Picker */}
          <div>
            <label className="mb-1 block text-sm font-medium">分類</label>
            <div className="flex gap-2">
              {CATEGORY_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setCategory(opt.value)}
                  className={cn(
                    'rounded-md px-3 py-1.5 text-sm font-medium transition-all',
                    category === opt.value
                      ? cn(opt.class, 'text-white ring-2 ring-primary ring-offset-2')
                      : 'bg-muted text-muted-foreground hover:bg-accent',
                  )}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="mt-6 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-md px-4 py-2 text-sm hover:bg-accent"
          >
            取消
          </button>
          <button
            onClick={handleSave}
            className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90"
          >
            儲存
          </button>
        </div>
      </div>
    </div>
  )
}
