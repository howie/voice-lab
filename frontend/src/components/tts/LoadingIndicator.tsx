/**
 * LoadingIndicator Component
 * T045: Create LoadingIndicator component for synthesis in progress
 */

interface LoadingIndicatorProps {
  isLoading: boolean
  progress?: number // 0-100
  message?: string
}

export function LoadingIndicator({
  isLoading,
  progress,
  message = '正在合成語音...',
}: LoadingIndicatorProps) {
  if (!isLoading) return null

  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-8">
      {/* Spinner */}
      <div className="relative">
        <svg
          className="h-12 w-12 animate-spin text-primary"
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

        {/* Waveform animation in center */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="flex items-center gap-0.5">
            {[0, 1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className="h-3 w-0.5 animate-pulse rounded bg-primary"
                style={{
                  animationDelay: `${i * 0.15}s`,
                  animationDuration: '0.8s',
                }}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Message */}
      <p className="text-sm text-muted-foreground">{message}</p>

      {/* Progress bar (if progress is provided) */}
      {progress !== undefined && (
        <div className="w-full max-w-xs">
          <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-all duration-300"
              style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
            />
          </div>
          <p className="mt-1 text-center text-xs text-muted-foreground">
            {Math.round(progress)}%
          </p>
        </div>
      )}
    </div>
  )
}

/**
 * Inline loading spinner
 */
export function Spinner({ className = '' }: { className?: string }) {
  return (
    <svg
      className={`animate-spin ${className}`}
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
  )
}
