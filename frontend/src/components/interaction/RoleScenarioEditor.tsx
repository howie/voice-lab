/**
 * RoleScenarioEditor Component
 * Feature: 004-interaction-module
 * T074-T074c [US4]: Role and scenario configuration editor.
 *
 * Allows users to configure:
 * - User role name (for transcript display)
 * - AI role name (for transcript display and system prompt)
 * - Scenario context (for system prompt generation)
 */

import { useCallback } from 'react'

interface RoleScenarioEditorProps {
  /** User role name */
  userRole: string
  /** AI role name */
  aiRole: string
  /** Scenario context description */
  scenarioContext: string
  /** Callback when user role changes */
  onUserRoleChange: (value: string) => void
  /** Callback when AI role changes */
  onAiRoleChange: (value: string) => void
  /** Callback when scenario context changes */
  onScenarioContextChange: (value: string) => void
  /** Whether to disable the editor (e.g., during active session) */
  disabled?: boolean
  /** Additional CSS classes */
  className?: string
  /** Maximum length for scenario context */
  maxScenarioLength?: number
}

/** T074a: Input validation constants */
const MAX_ROLE_LENGTH = 100
const DEFAULT_MAX_SCENARIO_LENGTH = 500

export function RoleScenarioEditor({
  userRole,
  aiRole,
  scenarioContext,
  onUserRoleChange,
  onAiRoleChange,
  onScenarioContextChange,
  disabled = false,
  className = '',
  maxScenarioLength = DEFAULT_MAX_SCENARIO_LENGTH,
}: RoleScenarioEditorProps) {
  // T074a: Validated change handlers
  const handleUserRoleChange = useCallback(
    (value: string) => {
      if (value.length <= MAX_ROLE_LENGTH) {
        onUserRoleChange(value)
      }
    },
    [onUserRoleChange]
  )

  const handleAiRoleChange = useCallback(
    (value: string) => {
      if (value.length <= MAX_ROLE_LENGTH) {
        onAiRoleChange(value)
      }
    },
    [onAiRoleChange]
  )

  const handleScenarioContextChange = useCallback(
    (value: string) => {
      if (value.length <= maxScenarioLength) {
        onScenarioContextChange(value)
      }
    },
    [onScenarioContextChange, maxScenarioLength]
  )

  // T074b: Calculate character usage
  const scenarioCharCount = scenarioContext.length
  const scenarioCharPercentage = (scenarioCharCount / maxScenarioLength) * 100
  const isNearLimit = scenarioCharPercentage >= 80
  const isAtLimit = scenarioCharPercentage >= 100

  return (
    <div className={`rounded-lg border bg-card p-4 ${className}`}>
      <div className="mb-4">
        <h3 className="text-sm font-medium text-foreground">角色與情境設定</h3>
        <p className="mt-1 text-xs text-muted-foreground">
          設定對話中的角色名稱和情境背景
        </p>
      </div>

      {/* Role Names */}
      <div className="mb-4 grid grid-cols-2 gap-4">
        {/* User Role */}
        <div>
          <label
            htmlFor="user-role"
            className="mb-1 block text-sm text-muted-foreground"
          >
            使用者角色
          </label>
          <input
            id="user-role"
            type="text"
            value={userRole}
            onChange={(e) => handleUserRoleChange(e.target.value)}
            disabled={disabled}
            placeholder="使用者"
            className="
              w-full rounded-lg border bg-background px-3 py-2 text-sm
              focus:outline-none focus:ring-2 focus:ring-primary
              disabled:cursor-not-allowed disabled:opacity-50
            "
          />
          <p className="mt-1 text-xs text-muted-foreground">
            在對話記錄中顯示的名稱
          </p>
        </div>

        {/* AI Role */}
        <div>
          <label
            htmlFor="ai-role"
            className="mb-1 block text-sm text-muted-foreground"
          >
            AI 角色
          </label>
          <input
            id="ai-role"
            type="text"
            value={aiRole}
            onChange={(e) => handleAiRoleChange(e.target.value)}
            disabled={disabled}
            placeholder="AI 助理"
            className="
              w-full rounded-lg border bg-background px-3 py-2 text-sm
              focus:outline-none focus:ring-2 focus:ring-primary
              disabled:cursor-not-allowed disabled:opacity-50
            "
          />
          <p className="mt-1 text-xs text-muted-foreground">
            AI 在對話中扮演的角色
          </p>
        </div>
      </div>

      {/* Scenario Context */}
      <div>
        <div className="mb-1 flex items-center justify-between">
          <label
            htmlFor="scenario-context"
            className="text-sm text-muted-foreground"
          >
            情境描述
          </label>
          {/* T074b: Character counter */}
          <span
            className={`text-xs ${
              isAtLimit
                ? 'text-destructive'
                : isNearLimit
                  ? 'text-warning'
                  : 'text-muted-foreground'
            }`}
          >
            {scenarioCharCount} / {maxScenarioLength}
          </span>
        </div>
        <textarea
          id="scenario-context"
          value={scenarioContext}
          onChange={(e) => handleScenarioContextChange(e.target.value)}
          disabled={disabled}
          placeholder="例如：你正在接聽一通客服電話，客戶詢問關於產品退換貨的問題..."
          rows={3}
          className="
            w-full resize-none rounded-lg border bg-background px-3 py-2 text-sm
            focus:outline-none focus:ring-2 focus:ring-primary
            disabled:cursor-not-allowed disabled:opacity-50
          "
        />
        <p className="mt-1 text-xs text-muted-foreground">
          描述對話的情境背景，系統會自動生成相應的 System Prompt
        </p>

        {/* T074b: Progress bar for character count */}
        <div className="mt-2 h-1 w-full overflow-hidden rounded-full bg-muted">
          <div
            className={`h-full transition-all ${
              isAtLimit
                ? 'bg-destructive'
                : isNearLimit
                  ? 'bg-warning'
                  : 'bg-primary'
            }`}
            style={{ width: `${Math.min(scenarioCharPercentage, 100)}%` }}
          />
        </div>
      </div>

      {/* Preview generated system prompt */}
      {scenarioContext && (
        <div className="mt-4 rounded-lg bg-muted/50 p-3">
          <p className="mb-1 text-xs font-medium text-muted-foreground">
            生成的 System Prompt 預覽：
          </p>
          <p className="text-sm text-foreground">
            你是{aiRole || 'AI 助理'}。{scenarioContext}
          </p>
        </div>
      )}
    </div>
  )
}

export default RoleScenarioEditor
