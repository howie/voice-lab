/**
 * Prompt Template Editor Modal Component
 * Feature: 015-magic-dj-ai-prompts (T025)
 *
 * Modal dialog for creating/editing prompt templates.
 * Form: name, prompt content, color picker.
 */

import { useState, useEffect, useCallback } from 'react'
import { X } from 'lucide-react'

import { cn } from '@/lib/utils'
import type { PromptTemplate, PromptTemplateColor } from '@/types/magic-dj'

// =============================================================================
// Color Options
// =============================================================================

const COLOR_OPTIONS: { value: PromptTemplateColor; label: string; class: string }[] = [
  { value: 'blue', label: '藍', class: 'bg-blue-500' },
  { value: 'green', label: '綠', class: 'bg-green-500' },
  { value: 'yellow', label: '黃', class: 'bg-yellow-500' },
  { value: 'red', label: '紅', class: 'bg-red-500' },
  { value: 'purple', label: '紫', class: 'bg-purple-500' },
  { value: 'orange', label: '橙', class: 'bg-orange-500' },
  { value: 'pink', label: '粉', class: 'bg-pink-500' },
  { value: 'cyan', label: '青', class: 'bg-cyan-500' },
]

// =============================================================================
// Types
// =============================================================================

export interface PromptTemplateEditorProps {
  isOpen: boolean
  onClose: () => void
  onSave: (data: { name: string; prompt: string; color: PromptTemplateColor }) => void
  editingTemplate?: PromptTemplate | null
}

// =============================================================================
// Component
// =============================================================================

export function PromptTemplateEditor({
  isOpen,
  onClose,
  onSave,
  editingTemplate,
}: PromptTemplateEditorProps) {
  const [name, setName] = useState('')
  const [prompt, setPrompt] = useState('')
  const [color, setColor] = useState<PromptTemplateColor>('orange')
  const [errors, setErrors] = useState<{ name?: string; prompt?: string }>({})

  // Populate form when editing
  useEffect(() => {
    if (editingTemplate) {
      setName(editingTemplate.name)
      setPrompt(editingTemplate.prompt)
      setColor(editingTemplate.color)
    } else {
      setName('')
      setPrompt('')
      setColor('orange')
    }
    setErrors({})
  }, [editingTemplate, isOpen])

  const validate = useCallback((): boolean => {
    const newErrors: { name?: string; prompt?: string } = {}
    if (!name.trim()) {
      newErrors.name = '名稱不能為空'
    } else if (name.trim().length > 20) {
      newErrors.name = '名稱不能超過 20 字'
    }
    if (!prompt.trim()) {
      newErrors.prompt = 'Prompt 內容不能為空'
    } else if (prompt.trim().length > 500) {
      newErrors.prompt = 'Prompt 不能超過 500 字'
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }, [name, prompt])

  const handleSave = useCallback(() => {
    if (!validate()) return
    onSave({ name: name.trim(), prompt: prompt.trim(), color })
    onClose()
  }, [validate, onSave, name, prompt, color, onClose])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="mx-4 w-full max-w-md rounded-lg border bg-background p-6 shadow-lg">
        {/* Header */}
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">
            {editingTemplate ? '編輯 Prompt Template' : '新增 Prompt Template'}
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
              placeholder="例如：裝傻"
              className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
            />
            {errors.name && (
              <p className="mt-1 text-xs text-destructive">{errors.name}</p>
            )}
            <p className="mt-1 text-xs text-muted-foreground">{name.length}/20</p>
          </div>

          {/* Prompt Content */}
          <div>
            <label className="mb-1 block text-sm font-medium">Prompt 內容</label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              maxLength={500}
              rows={4}
              placeholder="輸入要送給 AI 的隱藏指令..."
              className="w-full resize-none rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
            />
            {errors.prompt && (
              <p className="mt-1 text-xs text-destructive">{errors.prompt}</p>
            )}
            <p className="mt-1 text-xs text-muted-foreground">{prompt.length}/500</p>
          </div>

          {/* Color Picker */}
          <div>
            <label className="mb-1 block text-sm font-medium">顏色</label>
            <div className="flex gap-2">
              {COLOR_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setColor(opt.value)}
                  className={cn(
                    'h-8 w-8 rounded-full transition-all',
                    opt.class,
                    color === opt.value
                      ? 'ring-2 ring-primary ring-offset-2'
                      : 'opacity-60 hover:opacity-100',
                  )}
                  title={opt.label}
                />
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

export default PromptTemplateEditor
