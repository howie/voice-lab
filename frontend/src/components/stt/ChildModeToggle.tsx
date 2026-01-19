/**
 * ChildModeToggle Component
 * Feature: 003-stt-testing-module - User Story 4
 * T058: Create ChildModeToggle component
 *
 * Toggles child speech optimization mode with explanatory tooltips.
 */

interface ChildModeToggleProps {
  checked: boolean
  onChange: (checked: boolean) => void
  disabled?: boolean
  providerName?: string
}

export function ChildModeToggle({
  checked,
  onChange,
  disabled = false,
  providerName,
}: ChildModeToggleProps) {
  return (
    <div className="space-y-2">
      {/* Toggle */}
      <div className="flex items-center gap-3">
        <input
          type="checkbox"
          id="childMode"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          disabled={disabled}
          className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        />
        <label
          htmlFor="childMode"
          className={`text-sm font-medium ${disabled ? 'text-gray-400 dark:text-gray-600' : 'text-gray-700 dark:text-gray-300'}`}
        >
          兒童語音模式最佳化
        </label>

        {/* Info Icon with Tooltip */}
        <div className="group relative">
          <svg
            className="h-4 w-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 cursor-help"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>

          {/* Tooltip */}
          <div className="invisible group-hover:visible absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 bg-gray-900 dark:bg-gray-800 text-white text-xs rounded-lg shadow-lg z-10">
            <div className="space-y-2">
              <p className="font-medium">啟用兒童語音最佳化</p>
              <p className="text-gray-300">
                針對兒童語音特性進行辨識優化,包含:
              </p>
              <ul className="list-disc list-inside space-y-1 text-gray-300">
                <li>較高音調適應</li>
                <li>常見兒童用語強化</li>
                <li>發音不準容錯提升</li>
              </ul>
              {providerName && (
                <p className="text-gray-400 text-xs mt-2">
                  Provider: {providerName}
                </p>
              )}
            </div>
            {/* Tooltip arrow */}
            <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900 dark:border-t-gray-800"></div>
          </div>
        </div>
      </div>

      {/* Description */}
      {checked && (
        <div className="flex items-start gap-2 rounded-lg bg-green-50 dark:bg-green-950 p-3 text-xs">
          <svg
            className="h-4 w-4 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
              clipRule="evenodd"
            />
          </svg>
          <p className="text-green-800 dark:text-green-200">
            兒童語音模式已啟用。系統將針對兒童發音特性優化辨識準確度。
          </p>
        </div>
      )}
    </div>
  )
}
