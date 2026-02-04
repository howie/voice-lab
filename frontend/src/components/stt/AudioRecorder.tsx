/**
 * AudioRecorder Component
 * Feature: 003-stt-testing-module
 * T039: Create AudioRecorder component with MediaRecorder API
 * T041: Implement Safari fallback (WebM → MP4)
 * T042: Add microphone permission handling
 *
 * Records audio from the microphone with real-time waveform visualization.
 */

import { useEffect, useRef, useState, useCallback } from 'react'

export type RecordingState = 'idle' | 'requesting' | 'recording' | 'paused' | 'stopped'

export interface AudioRecorderProps {
  onRecordingComplete?: (blob: Blob) => void
  onRecordingStart?: () => void
  onRecordingStop?: () => void
  onError?: (error: string) => void
  maxDuration?: number // Max recording duration in seconds
  disabled?: boolean
}

// Detect Safari browser for format fallback
const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent)

// Get preferred MIME type based on browser support
function getPreferredMimeType(): string {
  const mimeTypes = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/mp4',
    'audio/ogg;codecs=opus',
    'audio/wav',
  ]

  // Safari prefers mp4
  if (isSafari) {
    return 'audio/mp4'
  }

  for (const mimeType of mimeTypes) {
    if (MediaRecorder.isTypeSupported(mimeType)) {
      return mimeType
    }
  }

  return 'audio/webm' // Default fallback
}

export function AudioRecorder({
  onRecordingComplete,
  onRecordingStart,
  onRecordingStop,
  onError,
  maxDuration = 300, // 5 minutes default
  disabled = false,
}: AudioRecorderProps) {
  const [recordingState, setRecordingState] = useState<RecordingState>('idle')
  const [duration, setDuration] = useState(0)
  const [permissionStatus, setPermissionStatus] = useState<
    'prompt' | 'granted' | 'denied' | 'unknown'
  >('unknown')
  const [audioLevel, setAudioLevel] = useState(0)

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const animationRef = useRef<number | null>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  // Check microphone permission status on mount
  useEffect(() => {
    let permissionResult: PermissionStatus | null = null

    function handlePermissionChange(this: PermissionStatus) {
      setPermissionStatus(this.state as 'prompt' | 'granted' | 'denied')
    }

    async function checkPermission() {
      try {
        permissionResult = await navigator.permissions.query({
          name: 'microphone' as PermissionName,
        })
        setPermissionStatus(permissionResult.state as 'prompt' | 'granted' | 'denied')
        permissionResult.addEventListener('change', handlePermissionChange)
      } catch {
        // Permission API not supported, will check on first use
        setPermissionStatus('unknown')
      }
    }
    checkPermission()

    return () => {
      permissionResult?.removeEventListener('change', handlePermissionChange)
    }
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRecording()
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [])

  // Draw waveform visualization
  const drawWaveform = useCallback(() => {
    const canvas = canvasRef.current
    const analyser = analyserRef.current
    if (!canvas || !analyser) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const bufferLength = analyser.frequencyBinCount
    const dataArray = new Uint8Array(bufferLength)
    analyser.getByteTimeDomainData(dataArray)

    // Calculate audio level for visual feedback
    let sum = 0
    for (let i = 0; i < bufferLength; i++) {
      const value = (dataArray[i] - 128) / 128
      sum += value * value
    }
    const rms = Math.sqrt(sum / bufferLength)
    setAudioLevel(Math.min(1, rms * 3))

    // Clear canvas
    ctx.fillStyle = 'rgb(30, 30, 35)'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    // Draw waveform
    ctx.lineWidth = 2
    ctx.strokeStyle = 'rgb(124, 58, 237)' // Primary purple color
    ctx.beginPath()

    const sliceWidth = canvas.width / bufferLength
    let x = 0

    for (let i = 0; i < bufferLength; i++) {
      const v = dataArray[i] / 128.0
      const y = (v * canvas.height) / 2

      if (i === 0) {
        ctx.moveTo(x, y)
      } else {
        ctx.lineTo(x, y)
      }

      x += sliceWidth
    }

    ctx.lineTo(canvas.width, canvas.height / 2)
    ctx.stroke()

    // Continue animation loop
    if (recordingState === 'recording') {
      animationRef.current = requestAnimationFrame(drawWaveform)
    }
  }, [recordingState])

  // Start animation when recording
  useEffect(() => {
    if (recordingState === 'recording' && analyserRef.current) {
      drawWaveform()
    }
  }, [recordingState, drawWaveform])

  const startRecording = async () => {
    try {
      setRecordingState('requesting')
      chunksRef.current = []
      setDuration(0)

      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000,
        },
      })

      streamRef.current = stream
      setPermissionStatus('granted')

      // Setup audio analysis for visualization
      audioContextRef.current = new AudioContext()
      analyserRef.current = audioContextRef.current.createAnalyser()
      analyserRef.current.fftSize = 2048
      const source = audioContextRef.current.createMediaStreamSource(stream)
      source.connect(analyserRef.current)

      // Setup MediaRecorder
      const mimeType = getPreferredMimeType()
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType,
        audioBitsPerSecond: 128000,
      })

      mediaRecorderRef.current = mediaRecorder

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType })
        onRecordingComplete?.(blob)
        onRecordingStop?.()
        cleanup()
      }

      mediaRecorder.onerror = () => {
        onError?.('Recording error occurred')
        cleanup()
        setRecordingState('idle')
      }

      // Start recording
      mediaRecorder.start(100) // Collect data every 100ms
      setRecordingState('recording')
      onRecordingStart?.()

      // Start duration timer
      timerRef.current = setInterval(() => {
        setDuration((prev) => {
          const newDuration = prev + 1
          if (newDuration >= maxDuration) {
            stopRecording()
          }
          return newDuration
        })
      }, 1000)
    } catch (error) {
      console.error('Failed to start recording:', error)

      if (error instanceof DOMException) {
        if (error.name === 'NotAllowedError') {
          setPermissionStatus('denied')
          onError?.('Microphone access denied. Please allow microphone access in your browser settings.')
        } else if (error.name === 'NotFoundError') {
          onError?.('No microphone found. Please connect a microphone and try again.')
        } else {
          onError?.(`Recording error: ${error.message}`)
        }
      } else {
        onError?.('Failed to start recording')
      }

      setRecordingState('idle')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
      setRecordingState('stopped')
    }

    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }

  const cleanup = () => {
    // Stop all tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }

    // Close audio context
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close()
      audioContextRef.current = null
    }

    // Cancel animation
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current)
      animationRef.current = null
    }

    analyserRef.current = null
    mediaRecorderRef.current = null
    setAudioLevel(0)
  }

  const handleToggleRecording = () => {
    if (recordingState === 'recording') {
      stopRecording()
    } else {
      startRecording()
    }
  }

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const isRecording = recordingState === 'recording'
  const isDisabled = disabled || recordingState === 'requesting'

  return (
    <div className="space-y-4">
      {/* Waveform Display */}
      <div className="relative rounded-lg border bg-muted/30 overflow-hidden">
        <canvas
          ref={canvasRef}
          width={400}
          height={100}
          className="w-full h-[100px]"
        />

        {/* Recording indicator */}
        {isRecording && (
          <div className="absolute top-2 left-2 flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-red-500 animate-pulse" />
            <span className="text-xs font-medium text-red-500">REC</span>
          </div>
        )}

        {/* Duration display */}
        <div className="absolute top-2 right-2 text-xs font-mono text-muted-foreground bg-background/80 px-2 py-1 rounded">
          {formatDuration(duration)} / {formatDuration(maxDuration)}
        </div>

        {/* Audio level indicator */}
        {isRecording && (
          <div className="absolute bottom-2 left-2 right-2">
            <div className="h-1 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-primary transition-all duration-75"
                style={{ width: `${audioLevel * 100}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="flex items-center justify-center gap-4">
        {/* Record/Stop Button */}
        <button
          onClick={handleToggleRecording}
          disabled={isDisabled}
          className={`
            flex h-14 w-14 items-center justify-center rounded-full
            transition-all duration-200
            ${
              isRecording
                ? 'bg-red-500 hover:bg-red-600 text-white'
                : 'bg-primary hover:bg-primary/90 text-primary-foreground'
            }
            disabled:cursor-not-allowed disabled:opacity-50
          `}
          aria-label={isRecording ? 'Stop recording' : 'Start recording'}
        >
          {recordingState === 'requesting' ? (
            // Loading spinner
            <svg className="h-6 w-6 animate-spin" fill="none" viewBox="0 0 24 24">
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
          ) : isRecording ? (
            // Stop icon (square)
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              className="h-6 w-6"
            >
              <path
                fillRule="evenodd"
                d="M4.5 7.5a3 3 0 013-3h9a3 3 0 013 3v9a3 3 0 01-3 3h-9a3 3 0 01-3-3v-9z"
                clipRule="evenodd"
              />
            </svg>
          ) : (
            // Microphone icon
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              className="h-6 w-6"
            >
              <path d="M8.25 4.5a3.75 3.75 0 117.5 0v8.25a3.75 3.75 0 11-7.5 0V4.5z" />
              <path d="M6 10.5a.75.75 0 01.75.75v1.5a5.25 5.25 0 1010.5 0v-1.5a.75.75 0 011.5 0v1.5a6.751 6.751 0 01-6 6.709v2.291h3a.75.75 0 010 1.5h-7.5a.75.75 0 010-1.5h3v-2.291a6.751 6.751 0 01-6-6.709v-1.5A.75.75 0 016 10.5z" />
            </svg>
          )}
        </button>
      </div>

      {/* Status Messages */}
      {permissionStatus === 'denied' && (
        <div className="rounded-lg bg-red-50 dark:bg-red-950 p-3 text-center text-sm text-red-600 dark:text-red-400">
          <p>Microphone access is blocked.</p>
          <p className="text-xs mt-1">
            Please enable microphone access in your browser settings and refresh the page.
          </p>
        </div>
      )}

      {recordingState === 'idle' && permissionStatus !== 'denied' && (
        <p className="text-center text-sm text-muted-foreground">
          Click the button to start recording
        </p>
      )}
    </div>
  )
}
