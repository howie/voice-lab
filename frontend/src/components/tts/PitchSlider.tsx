/**
 * PitchSlider Component
 * T059: Create PitchSlider component (-20 to +20)
 */

interface PitchSliderProps {
  value: number
  onChange: (value: number) => void
  min?: number
  max?: number
  step?: number
  disabled?: boolean
}

export function PitchSlider({
  value,
  onChange,
  min = -20,
  max = 20,
  step = 1,
  disabled = false,
}: PitchSliderProps) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(parseFloat(e.target.value))
  }

  // Calculate percentage for visual indicator (centered at 0)
  const percentage = ((value - min) / (max - min)) * 100

  // Format display value with sign
  const displayValue = value > 0 ? `+${value}` : value.toString()

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium">
          音調
        </label>
        <span className="text-sm font-mono text-primary">
          {displayValue}
        </span>
      </div>

      <div className="relative">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={handleChange}
          disabled={disabled}
          className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer disabled:cursor-not-allowed disabled:opacity-50"
          style={{
            background: `linear-gradient(to right, hsl(var(--primary)) ${percentage}%, hsl(var(--muted)) ${percentage}%)`,
          }}
        />
        {/* Center marker */}
        <div
          className="absolute top-1/2 -translate-y-1/2 w-0.5 h-4 bg-muted-foreground/30"
          style={{ left: '50%' }}
        />
      </div>

      <div className="flex justify-between text-xs text-muted-foreground">
        <span>{min} (低)</span>
        <span>0</span>
        <span>+{max} (高)</span>
      </div>
    </div>
  )
}
