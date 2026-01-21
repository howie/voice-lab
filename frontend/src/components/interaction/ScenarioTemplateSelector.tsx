/**
 * ScenarioTemplateSelector Component
 * Feature: 004-interaction-module
 * T075-T076 [US4]: Scenario template selection and one-click fill.
 *
 * Allows users to:
 * - Browse available scenario templates
 * - Select a template to auto-fill role and scenario configuration
 */

import { useCallback, useEffect, useState } from 'react'

import type { ScenarioTemplate } from '@/types/interaction'

interface ScenarioTemplateSelectorProps {
  /** Callback when a template is selected */
  onSelect: (template: ScenarioTemplate) => void
  /** Whether to disable the selector (e.g., during active session) */
  disabled?: boolean
  /** Additional CSS classes */
  className?: string
  /** Currently selected template ID (for highlighting) */
  selectedTemplateId?: string
}

// Group templates by category for better organization
function groupByCategory(templates: ScenarioTemplate[]): Record<string, ScenarioTemplate[]> {
  return templates.reduce(
    (acc, template) => {
      const category = template.category || '其他'
      if (!acc[category]) {
        acc[category] = []
      }
      acc[category].push(template)
      return acc
    },
    {} as Record<string, ScenarioTemplate[]>
  )
}

export function ScenarioTemplateSelector({
  onSelect,
  disabled = false,
  className = '',
  selectedTemplateId,
}: ScenarioTemplateSelectorProps) {
  const [templates, setTemplates] = useState<ScenarioTemplate[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isExpanded, setIsExpanded] = useState(false)

  // Fetch templates on mount
  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        setIsLoading(true)
        setError(null)
        const response = await fetch('/api/v1/interaction/templates')
        if (!response.ok) {
          throw new Error('Failed to fetch templates')
        }
        const data = await response.json()
        setTemplates(data.templates || data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
        // Use fallback templates if API fails
        setTemplates(FALLBACK_TEMPLATES)
      } finally {
        setIsLoading(false)
      }
    }

    fetchTemplates()
  }, [])

  const handleSelectTemplate = useCallback(
    (template: ScenarioTemplate) => {
      onSelect(template)
      setIsExpanded(false)
    },
    [onSelect]
  )

  const groupedTemplates = groupByCategory(templates)

  return (
    <div className={`rounded-lg border bg-card ${className}`}>
      {/* Header with expand toggle */}
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        disabled={disabled}
        className="
          flex w-full items-center justify-between p-4 text-left
          hover:bg-muted/50 disabled:cursor-not-allowed disabled:opacity-50
        "
      >
        <div>
          <h3 className="text-sm font-medium text-foreground">情境範本</h3>
          <p className="mt-0.5 text-xs text-muted-foreground">
            選擇預設範本快速設定角色與情境
          </p>
        </div>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          className={`h-5 w-5 text-muted-foreground transition-transform ${
            isExpanded ? 'rotate-180' : ''
          }`}
        >
          <path
            fillRule="evenodd"
            d="M12.53 16.28a.75.75 0 01-1.06 0l-7.5-7.5a.75.75 0 011.06-1.06L12 14.69l6.97-6.97a.75.75 0 111.06 1.06l-7.5 7.5z"
            clipRule="evenodd"
          />
        </svg>
      </button>

      {/* Template list */}
      {isExpanded && (
        <div className="border-t p-2">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <svg
                className="h-6 w-6 animate-spin text-primary"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              <span className="ml-2 text-sm text-muted-foreground">載入中...</span>
            </div>
          ) : error && templates.length === 0 ? (
            <div className="py-4 text-center text-sm text-destructive">{error}</div>
          ) : (
            <div className="max-h-64 space-y-3 overflow-y-auto">
              {Object.entries(groupedTemplates).map(([category, categoryTemplates]) => (
                <div key={category}>
                  <h4 className="mb-1 px-2 text-xs font-medium text-muted-foreground">
                    {category}
                  </h4>
                  <div className="space-y-1">
                    {categoryTemplates.map((template) => (
                      <button
                        key={template.id}
                        type="button"
                        onClick={() => handleSelectTemplate(template)}
                        disabled={disabled}
                        className={`
                          w-full rounded-lg p-3 text-left transition-all
                          hover:bg-muted/80 disabled:cursor-not-allowed disabled:opacity-50
                          ${
                            selectedTemplateId === template.id
                              ? 'bg-primary/10 ring-1 ring-primary'
                              : 'bg-muted/30'
                          }
                        `}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <span className="text-sm font-medium text-foreground">
                              {template.name}
                            </span>
                            {template.is_default && (
                              <span className="ml-2 rounded bg-primary/20 px-1.5 py-0.5 text-xs text-primary">
                                預設
                              </span>
                            )}
                            <p className="mt-0.5 text-xs text-muted-foreground">
                              {template.description}
                            </p>
                          </div>
                        </div>
                        <div className="mt-2 flex gap-2 text-xs text-muted-foreground">
                          <span className="rounded bg-muted px-1.5 py-0.5">
                            {template.user_role}
                          </span>
                          <span>↔</span>
                          <span className="rounded bg-muted px-1.5 py-0.5">
                            {template.ai_role}
                          </span>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// T075: Fallback templates in case API is unavailable
const FALLBACK_TEMPLATES: ScenarioTemplate[] = [
  {
    id: 'fallback-general',
    name: '一般對話',
    description: '通用的對話情境',
    user_role: '使用者',
    ai_role: 'AI 助理',
    scenario_context: '你是一個友善、有耐心的 AI 助理，可以回答各種問題並提供幫助。',
    category: '通用',
    is_default: true,
    created_at: '',
    updated_at: '',
  },
  {
    id: 'fallback-customer-service',
    name: '客服諮詢',
    description: '客戶服務對話練習',
    user_role: '客戶',
    ai_role: '客服專員',
    scenario_context:
      '你是一家電商平台的客服專員，需要協助客戶處理訂單查詢、退換貨申請、商品諮詢等問題。請保持專業、友善、有耐心的態度。',
    category: '商業',
    is_default: false,
    created_at: '',
    updated_at: '',
  },
  {
    id: 'fallback-language-tutor',
    name: '語言教學',
    description: '語言學習對話練習',
    user_role: '學生',
    ai_role: '語言老師',
    scenario_context:
      '你是一位經驗豐富的語言老師，專門教授中文。請用清晰、有耐心的方式回答問題，適時糾正發音和用法，並給予鼓勵。',
    category: '教育',
    is_default: false,
    created_at: '',
    updated_at: '',
  },
]

export default ScenarioTemplateSelector
