/**
 * Story Player
 * Feature: StoryPal — AI Interactive Story Companion
 *
 * Full immersive story player experience — the core interactive component.
 * Manages WebSocket connection, story playback, voice input, and choice interactions.
 */

import { useCallback, useEffect, useState } from 'react'
import { ArrowLeft } from 'lucide-react'
import { useStoryPalStore } from '@/stores/storypalStore'
import { CharacterPanel } from './CharacterPanel'
import { ChoicePrompt } from './ChoicePrompt'
import { SceneBGMIndicator } from './SceneBGMIndicator'
import { StoryControls } from './StoryControls'
import { StoryTranscript } from './StoryTranscript'

interface StoryPlayerProps {
  onExit: () => void
}

export function StoryPlayer({ onExit }: StoryPlayerProps) {
  const {
    session,
    playState,
    turns,
    characters,
    speakingCharacter,
    currentChoice,
    currentScene,
    currentSegment,
    bgmPlaying,
    isConnected,
    error,
    connectWS,
    disconnectWS,
    sendStoryConfig,
    sendChoice,
    sendTextInput,
    sendInterrupt,
    setPlayState,
    reset,
    clearError,
  } = useStoryPalStore()

  const [isListening, setIsListening] = useState(false)
  const [textInput, setTextInput] = useState('')

  // Connect WebSocket on mount
  useEffect(() => {
    connectWS()
    return () => {
      disconnectWS()
    }
  }, [connectWS, disconnectWS])

  // Send story config once connected
  useEffect(() => {
    if (isConnected && session && playState === 'loading') {
      sendStoryConfig({
        template_id: session.template_id ?? undefined,
        language: session.language,
        characters_config: session.characters_config,
      })
    }
  }, [isConnected, session, playState, sendStoryConfig])

  const handleChoiceSelect = useCallback(
    (choice: string) => {
      sendChoice(choice)
    },
    [sendChoice]
  )

  const handleTextSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault()
      if (textInput.trim()) {
        sendTextInput(textInput.trim())
        setTextInput('')
      }
    },
    [textInput, sendTextInput]
  )

  const handleToggleListening = useCallback(() => {
    setIsListening((prev) => !prev)
    // Microphone audio streaming would be wired here via useMicrophone hook
  }, [])

  const handlePause = useCallback(() => {
    setPlayState('paused')
    sendInterrupt()
  }, [setPlayState, sendInterrupt])

  const handleResume = useCallback(() => {
    setPlayState('playing')
  }, [setPlayState])

  const handleStop = useCallback(() => {
    disconnectWS()
    setPlayState('ended')
  }, [disconnectWS, setPlayState])

  const handleRestart = useCallback(() => {
    reset()
    onExit()
  }, [reset, onExit])

  return (
    <div className="flex h-full flex-col">
      {/* Top bar */}
      <div className="flex items-center gap-3 border-b px-4 py-2">
        <button
          onClick={onExit}
          className="rounded-md p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
        </button>
        <div className="flex-1">
          <h2 className="text-sm font-semibold">{session?.title ?? '故事時間'}</h2>
          <div className="flex items-center gap-2">
            <SceneBGMIndicator scene={currentScene} bgmPlaying={bgmPlaying} />
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <span
            className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}
          />
          <span className="text-xs text-muted-foreground">
            {isConnected ? '已連線' : '未連線'}
          </span>
        </div>
      </div>

      {/* Characters */}
      <div className="border-b px-4 py-2">
        <CharacterPanel characters={characters} speakingCharacter={speakingCharacter} />
      </div>

      {/* Story content — scrollable */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {error && (
          <div className="mb-4 flex items-center justify-between rounded-lg border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            <span>{error}</span>
            <button onClick={clearError} className="text-xs underline">
              關閉
            </button>
          </div>
        )}

        <StoryTranscript
          turns={turns}
          characters={characters}
          currentSegmentContent={currentSegment?.content}
        />

        {/* Choice prompt */}
        {currentChoice && playState === 'waiting_choice' && (
          <div className="mt-4">
            <ChoicePrompt choice={currentChoice} onSelect={handleChoiceSelect} />
          </div>
        )}

        {/* Story ended */}
        {playState === 'ended' && (
          <div className="mt-6 text-center">
            <p className="mb-2 text-lg font-semibold">故事結束了！</p>
            <p className="text-sm text-muted-foreground">
              這次的冒險真精彩，要再聽一個故事嗎？
            </p>
            <button
              onClick={handleRestart}
              className="mt-3 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
            >
              選擇新故事
            </button>
          </div>
        )}
      </div>

      {/* Text input for typing (alternative to voice) */}
      {(playState === 'waiting_choice' || playState === 'listening') && (
        <div className="border-t px-4 py-2">
          <form onSubmit={handleTextSubmit} className="flex gap-2">
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="用打字回答也可以..."
              className="flex-1 rounded-lg border bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <button
              type="submit"
              disabled={!textInput.trim()}
              className="rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground disabled:opacity-50"
            >
              送出
            </button>
          </form>
        </div>
      )}

      {/* Controls */}
      <div className="border-t px-4 py-3">
        <StoryControls
          playState={playState}
          isConnected={isConnected}
          isListening={isListening}
          onToggleListening={handleToggleListening}
          onPause={handlePause}
          onResume={handleResume}
          onStop={handleStop}
          onRestart={handleRestart}
        />
      </div>
    </div>
  )
}
