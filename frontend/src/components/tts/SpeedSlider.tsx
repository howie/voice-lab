/**
 * SpeedSlider Component
 * T058: Create SpeedSlider component (0.5x - 2.0x)
 */

interface SpeedSliderProps {
  value: number
  onChange: (value: number) => void
  min?: number
  max?: number
  step?: number
  disabled?: boolean
}

export function SpeedSlider({
  value,
  onChange,
  min = 0.5,
  max = 2.0,
  step = 0.1,
  disabled = false,
}: SpeedSliderProps) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(parseFloat(e.target.value))
  }

  // Calculate percentage for visual indicator
  const percentage = ((value - min) / (max - min)) * 100

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium">
          語速
        </label>
        <span className="text-sm font-mono text-primary">
          {value.toFixed(1)}x
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
      </div>

      <div className="flex justify-between text-xs text-muted-foreground">
        <span>{min}x</span>
        <span>1.0x</span>
        <span>{max}x</span>
      </div>
    </div>
  )
}
