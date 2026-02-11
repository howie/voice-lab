/**
 * StoryPal Page
 * Feature: StoryPal — AI Interactive Story Companion
 *
 * Main page for browsing story templates, managing sessions, and launching interactive stories.
 */

import { useCallback, useEffect, useState } from 'react'
import { BookOpen, Clock, Plus, Sparkles } from 'lucide-react'
import { StoryPlayer, StoryTemplateCard } from '@/components/storypal'
import { useStoryPalStore } from '@/stores/storypalStore'
import type { StoryCategory, StoryTemplate } from '@/types/storypal'
import { STORY_CATEGORIES } from '@/types/storypal'
import { cn } from '@/lib/utils'

type PageView = 'browse' | 'playing'

export function StoryPalPage() {
  const {
    templates,
    sessions,
    selectedTemplate,
    isLoadingTemplates,
    isLoadingSessions,
    isLoading,
    language,
    categoryFilter,
    fetchTemplates,
    fetchSessions,
    selectTemplate,
    createSession,
    loadSession,
    deleteSession,
    setCategoryFilter,
    reset,
  } = useStoryPalStore()

  const [view, setView] = useState<PageView>('browse')

  // Load data on mount
  useEffect(() => {
    fetchTemplates()
    fetchSessions()
  }, [fetchTemplates, fetchSessions])

  // Filter templates by category
  const filteredTemplates = categoryFilter
    ? templates.filter((t) => t.category === categoryFilter)
    : templates

  const handleStartStory = useCallback(async () => {
    if (!selectedTemplate) return
    const session = await createSession({
      template_id: selectedTemplate.id,
      title: selectedTemplate.name,
      language,
      characters_config: selectedTemplate.characters,
    })
    if (session) {
      setView('playing')
    }
  }, [selectedTemplate, language, createSession])

  const handleResumeSession = useCallback(
    async (sessionId: string) => {
      await loadSession(sessionId)
      setView('playing')
    },
    [loadSession]
  )

  const handleExitPlayer = useCallback(() => {
    reset()
    setView('browse')
    fetchSessions()
  }, [reset, fetchSessions])

  // Story player view
  if (view === 'playing') {
    return (
      <div className="h-[calc(100vh-8rem)] overflow-hidden rounded-lg border bg-card">
        <StoryPlayer onExit={handleExitPlayer} />
      </div>
    )
  }

  // Browse view
  return (
    <div className="mx-auto max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2">
          <Sparkles className="h-6 w-6 text-primary" />
          <h1 className="text-2xl font-bold">StoryPal</h1>
        </div>
        <p className="text-muted-foreground">
          AI 故事陪伴 — 讓每個孩子都有專屬的說書人
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left: Template browser */}
        <div className="space-y-4 lg:col-span-2">
          {/* Category filter */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setCategoryFilter(null)}
              className={cn(
                'rounded-full px-3 py-1 text-xs font-medium transition-colors',
                !categoryFilter
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground hover:bg-accent'
              )}
            >
              全部
            </button>
            {(Object.entries(STORY_CATEGORIES) as [StoryCategory, { label: string; emoji: string }][]).map(
              ([key, { label, emoji }]) => (
                <button
                  key={key}
                  onClick={() => setCategoryFilter(key)}
                  className={cn(
                    'rounded-full px-3 py-1 text-xs font-medium transition-colors',
                    categoryFilter === key
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted text-muted-foreground hover:bg-accent'
                  )}
                >
                  {emoji} {label}
                </button>
              )
            )}
          </div>

          {/* Template grid */}
          {isLoadingTemplates ? (
            <div className="flex items-center justify-center py-12">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            </div>
          ) : filteredTemplates.length === 0 ? (
            <div className="py-12 text-center text-sm text-muted-foreground">
              還沒有故事範本，敬請期待！
            </div>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              {filteredTemplates.map((template: StoryTemplate) => (
                <StoryTemplateCard
                  key={template.id}
                  template={template}
                  isSelected={selectedTemplate?.id === template.id}
                  onSelect={selectTemplate}
                />
              ))}
            </div>
          )}

          {/* Start button */}
          {selectedTemplate && (
            <div className="sticky bottom-0 flex justify-center border-t bg-background/80 py-4 backdrop-blur-sm">
              <button
                onClick={handleStartStory}
                disabled={isLoading}
                className="flex items-center gap-2 rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground shadow-lg transition-all hover:bg-primary/90 disabled:opacity-50"
              >
                {isLoading ? (
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                ) : (
                  <Plus className="h-4 w-4" />
                )}
                開始「{selectedTemplate.name}」
              </button>
            </div>
          )}
        </div>

        {/* Right: Recent sessions */}
        <div className="space-y-4">
          <h2 className="flex items-center gap-2 text-sm font-semibold">
            <Clock className="h-4 w-4" />
            最近的故事
          </h2>

          {isLoadingSessions ? (
            <div className="flex items-center justify-center py-8">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            </div>
          ) : sessions.length === 0 ? (
            <div className="rounded-lg border border-dashed p-6 text-center">
              <BookOpen className="mx-auto mb-2 h-8 w-8 text-muted-foreground/50" />
              <p className="text-sm text-muted-foreground">還沒有故事紀錄</p>
              <p className="text-xs text-muted-foreground">選一個故事範本開始吧！</p>
            </div>
          ) : (
            <div className="space-y-2">
              {sessions.slice(0, 10).map((session) => (
                <div
                  key={session.id}
                  className="group flex items-center gap-3 rounded-lg border bg-card p-3 transition-colors hover:bg-accent/50"
                >
                  <div className="flex-1 min-w-0">
                    <p className="truncate text-sm font-medium">{session.title}</p>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span
                        className={cn(
                          'inline-block h-1.5 w-1.5 rounded-full',
                          session.status === 'active' ? 'bg-green-500' : session.status === 'paused' ? 'bg-amber-500' : 'bg-muted-foreground'
                        )}
                      />
                      <span>
                        {session.status === 'active'
                          ? '進行中'
                          : session.status === 'paused'
                            ? '暫停'
                            : '已完成'}
                      </span>
                      <span>{new Date(session.started_at).toLocaleDateString('zh-TW')}</span>
                    </div>
                  </div>
                  <div className="flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                    {session.status !== 'completed' && (
                      <button
                        onClick={() => handleResumeSession(session.id)}
                        className="rounded px-2 py-1 text-xs font-medium text-primary hover:bg-primary/10"
                      >
                        繼續
                      </button>
                    )}
                    <button
                      onClick={() => deleteSession(session.id)}
                      className="rounded px-2 py-1 text-xs text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                    >
                      刪除
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
