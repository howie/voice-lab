/**
 * Prompt Template Panel Component
 * Feature: 015-magic-dj-ai-prompts (T012)
 *
 * Grid layout of PromptTemplateButton items with scrollable container
 * and "+" add button. First column in AI conversation mode.
 */

import { Plus } from 'lucide-react'

import { PromptTemplateButton } from './PromptTemplateButton'
import type { PromptTemplate } from '@/types/magic-dj'

// =============================================================================
// Types
// =============================================================================

export interface PromptTemplatePanelProps {
  templates: PromptTemplate[]
  disabled?: boolean
  lastSentPromptId?: string | null
  onSendPrompt: (template: PromptTemplate) => void
  onAddTemplate?: () => void
  onEditTemplate?: (template: PromptTemplate) => void
  onDeleteTemplate?: (template: PromptTemplate) => void
}

// =============================================================================
// Component
// =============================================================================

export function PromptTemplatePanel({
  templates,
  disabled = false,
  lastSentPromptId,
  onSendPrompt,
  onAddTemplate,
  onEditTemplate,
  onDeleteTemplate,
}: PromptTemplatePanelProps) {
  const sorted = [...templates].sort((a, b) => a.order - b.order)

  return (
    <div className="flex h-full w-48 shrink-0 flex-col rounded-lg border bg-card">
      {/* Header */}
      <div className="border-b p-3">
        <h3 className="text-sm font-semibold">Prompt Templates</h3>
        <p className="text-xs text-muted-foreground">按下即介入 AI 對話</p>
      </div>

      {/* Template Buttons */}
      <div className="flex flex-1 flex-col gap-1.5 overflow-y-auto p-2">
        {sorted.map((template) => (
          <PromptTemplateButton
            key={template.id}
            template={template}
            disabled={disabled}
            isJustSent={lastSentPromptId === template.id}
            onSend={onSendPrompt}
            onEdit={onEditTemplate}
            onDelete={onDeleteTemplate}
          />
        ))}

        {/* Add Button */}
        {onAddTemplate && (
          <button
            onClick={onAddTemplate}
            className="flex w-full items-center justify-center gap-1.5 rounded-md border border-dashed px-3 py-2 text-xs text-muted-foreground transition-colors hover:border-primary hover:text-primary"
          >
            <Plus className="h-3.5 w-3.5" />
            新增 Template
          </button>
        )}
      </div>
    </div>
  )
}

export default PromptTemplatePanel
