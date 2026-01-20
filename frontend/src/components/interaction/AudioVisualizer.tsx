/**
 * AudioVisualizer Component
 * Feature: 004-interaction-module
 * T035: Real-time audio visualization for voice interaction.
 *
 * Displays audio levels as animated bars or waveform during recording/playback.
 */

import { useEffect, useRef, useCallback } from 'react'

type VisualizerMode = 'bars' | 'waveform' | 'circle'

interface AudioVisualizerProps {
  /** Current audio volume level (0-1) */
  level: number
  /** Whether audio is actively being processed */
  isActive: boolean
  /** Visual mode for the visualizer */
  mode?: VisualizerMode
  /** Number of bars to display (bars mode only) */
  barCount?: number
  /** Height of the visualizer in pixels */
  height?: number
  /** Width of the visualizer in pixels */
  width?: number
  /** Color for the active visualization */
  activeColor?: string
  /** Color when inactive */
  inactiveColor?: string
  /** Background color */
  backgroundColor?: string
  /** Show level as percentage */
  showLevel?: boolean
  /** Additional CSS classes */
  className?: string
}

export function AudioVisualizer({
  level,
  isActive,
  mode = 'bars',
  barCount = 20,
  height = 60,
  width,
  activeColor = '#7C3AED',
  inactiveColor = '#6B7280',
  backgroundColor = '#1F2937',
  showLevel = false,
  className = '',
}: AudioVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animationRef = useRef<number>()
  const barsRef = useRef<number[]>(Array(barCount).fill(0))

  // Update bars with smoothed animation
  const updateBars = useCallback(() => {
    const smoothing = 0.3
    const targetHeight = isActive ? level : 0

    barsRef.current = barsRef.current.map((currentHeight, index) => {
      // Add some randomness for natural look
      const variance = isActive ? (Math.random() - 0.5) * 0.3 : 0
      const targetWithVariance = Math.max(0, Math.min(1, targetHeight + variance))
      // Apply different decay rates for visual interest
      const indexFactor = (index % 3 + 1) / 3
      return currentHeight + (targetWithVariance - currentHeight) * smoothing * indexFactor
    })
  }, [level, isActive])

  // Draw bars visualization
  const drawBars = useCallback(
    (ctx: CanvasRenderingContext2D, canvasWidth: number, canvasHeight: number) => {
      ctx.clearRect(0, 0, canvasWidth, canvasHeight)

      // Background
      ctx.fillStyle = backgroundColor
      ctx.fillRect(0, 0, canvasWidth, canvasHeight)

      const barWidth = canvasWidth / barCount
      const gap = 2
      const maxBarHeight = canvasHeight - 10

      barsRef.current.forEach((barLevel, index) => {
        const barHeight = Math.max(4, barLevel * maxBarHeight)
        const x = index * barWidth + gap / 2
        const y = (canvasHeight - barHeight) / 2
        const actualBarWidth = barWidth - gap

        // Gradient color based on level
        const gradient = ctx.createLinearGradient(0, y + barHeight, 0, y)
        gradient.addColorStop(0, isActive ? activeColor : inactiveColor)
        gradient.addColorStop(1, isActive ? `${activeColor}88` : `${inactiveColor}88`)

        ctx.fillStyle = gradient
        ctx.beginPath()
        ctx.roundRect(x, y, actualBarWidth, barHeight, 2)
        ctx.fill()
      })
    },
    [barCount, backgroundColor, activeColor, inactiveColor, isActive]
  )

  // Draw waveform visualization
  const drawWaveform = useCallback(
    (ctx: CanvasRenderingContext2D, canvasWidth: number, canvasHeight: number) => {
      ctx.clearRect(0, 0, canvasWidth, canvasHeight)

      // Background
      ctx.fillStyle = backgroundColor
      ctx.fillRect(0, 0, canvasWidth, canvasHeight)

      const centerY = canvasHeight / 2
      const amplitude = (canvasHeight / 2 - 5) * (isActive ? level : 0.1)

      ctx.beginPath()
      ctx.strokeStyle = isActive ? activeColor : inactiveColor
      ctx.lineWidth = 2

      for (let x = 0; x < canvasWidth; x++) {
        const frequency = isActive ? 0.05 + level * 0.03 : 0.02
        const phase = Date.now() * 0.005
        const y = centerY + Math.sin(x * frequency + phase) * amplitude
        if (x === 0) {
          ctx.moveTo(x, y)
        } else {
          ctx.lineTo(x, y)
        }
      }

      ctx.stroke()
    },
    [backgroundColor, activeColor, inactiveColor, isActive, level]
  )

  // Draw circle visualization
  const drawCircle = useCallback(
    (ctx: CanvasRenderingContext2D, canvasWidth: number, canvasHeight: number) => {
      ctx.clearRect(0, 0, canvasWidth, canvasHeight)

      // Background
      ctx.fillStyle = backgroundColor
      ctx.fillRect(0, 0, canvasWidth, canvasHeight)

      const centerX = canvasWidth / 2
      const centerY = canvasHeight / 2
      const maxRadius = Math.min(canvasWidth, canvasHeight) / 2 - 5
      const baseRadius = maxRadius * 0.3
      const dynamicRadius = baseRadius + (maxRadius - baseRadius) * (isActive ? level : 0)

      // Pulsing rings
      for (let i = 3; i >= 0; i--) {
        const ringRadius = dynamicRadius * (1 + i * 0.1)
        const alpha = 1 - i * 0.25

        ctx.beginPath()
        ctx.arc(centerX, centerY, ringRadius, 0, Math.PI * 2)
        ctx.strokeStyle = isActive
          ? `${activeColor}${Math.round(alpha * 255)
              .toString(16)
              .padStart(2, '0')}`
          : `${inactiveColor}${Math.round(alpha * 128)
              .toString(16)
              .padStart(2, '0')}`
        ctx.lineWidth = 2
        ctx.stroke()
      }

      // Center filled circle
      ctx.beginPath()
      ctx.arc(centerX, centerY, dynamicRadius, 0, Math.PI * 2)
      ctx.fillStyle = isActive ? `${activeColor}44` : `${inactiveColor}22`
      ctx.fill()
    },
    [backgroundColor, activeColor, inactiveColor, isActive, level]
  )

  // Animation loop
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const animate = () => {
      updateBars()

      const canvasWidth = canvas.width
      const canvasHeight = canvas.height

      switch (mode) {
        case 'waveform':
          drawWaveform(ctx, canvasWidth, canvasHeight)
          break
        case 'circle':
          drawCircle(ctx, canvasWidth, canvasHeight)
          break
        case 'bars':
        default:
          drawBars(ctx, canvasWidth, canvasHeight)
          break
      }

      animationRef.current = requestAnimationFrame(animate)
    }

    animate()

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [mode, updateBars, drawBars, drawWaveform, drawCircle])

  // Handle canvas resize
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width: w, height: h } = entry.contentRect
        canvas.width = w * window.devicePixelRatio
        canvas.height = h * window.devicePixelRatio
        const ctx = canvas.getContext('2d')
        if (ctx) {
          ctx.scale(window.devicePixelRatio, window.devicePixelRatio)
        }
      }
    })

    resizeObserver.observe(canvas)

    return () => {
      resizeObserver.disconnect()
    }
  }, [])

  return (
    <div className={`relative ${className}`}>
      <canvas
        ref={canvasRef}
        className="rounded-lg"
        style={{
          width: width ?? '100%',
          height,
        }}
      />
      {showLevel && (
        <div className="absolute bottom-1 right-2 text-xs text-muted-foreground">
          {Math.round(level * 100)}%
        </div>
      )}
    </div>
  )
}

export default AudioVisualizer
