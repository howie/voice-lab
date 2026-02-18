/**
 * ContentPreview - Story content preview and editing
 * Feature: 016-story-experience-mvp
 *
 * Displays generated content with editable textarea and action buttons.
 */

import { useState } from 'react'

import { useStoryExperienceStore } from '@/stores/storyExperienceStore'

function ParameterSummary() {
  const { generatedContent } = useStoryExperienceStore()
  if (!generatedContent) return null

  const { parameters_summary } = generatedContent
  return (
    <div className="rounded-md border bg-muted/50 px-4 py-3 text-sm">
      <h4 className="mb-1.5 font-medium text-muted-foreground">生成參數</h4>
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-muted-foreground">
        <span>年齡：{parameters_summary.age} 歲</span>
        <span>教導：{parameters_summary.educational_content}</span>
        <span>價值觀：{parameters_summary.values.join('、')}</span>
        <span>情緒：{parameters_summary.emotions.join('、')}</span>
        <span>角色：{parameters_summary.favorite_character}</span>
      </div>
    </div>
  )
}

export function ContentPreview() {
  const {
    generatedContent,
    editedContent,
    setEditedContent,
    regenerateContent,
    confirmContent,
    generateBranches,
    generateQuestions,
    isGenerating,
    isGeneratingBranches,
    isGeneratingQA,
    branches,
    qaQuestions,
    qaAnswers,
    selectBranch,
    askQuestion,
    error,
    setStep,
  } = useStoryExperienceStore()

  if (!generatedContent) return null

  const isSong = generatedContent.content_type === 'song'

  return (
    <div className="mx-auto max-w-2xl space-y-5">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">
          {isSong ? '兒歌預覽' : '故事預覽'}
        </h2>
        <button
          type="button"
          onClick={() => setStep('input')}
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          返回編輯參數
        </button>
      </div>

      <ParameterSummary />

      {/* Editable content area */}
      <div>
        <label htmlFor="content-editor" className="mb-1.5 block text-sm font-medium">
          內容（可直接編輯）
        </label>
        <textarea
          id="content-editor"
          value={editedContent}
          onChange={(e) => setEditedContent(e.target.value)}
          rows={Math.max(10, editedContent.split('\n').length + 2)}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm leading-relaxed"
        />
        <p className="mt-1 text-xs text-muted-foreground">
          共 {editedContent.length} 字
        </p>
      </div>

      {/* Error display */}
      {error && (
        <div className="rounded-md border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-3">
        <button
          type="button"
          onClick={regenerateContent}
          disabled={isGenerating}
          className="flex-1 rounded-md border border-input bg-background px-4 py-2.5 text-sm font-medium transition-colors hover:bg-accent disabled:opacity-50"
        >
          {isGenerating ? '生成中...' : '重新生成'}
        </button>
        <button
          type="button"
          onClick={confirmContent}
          className="flex-1 rounded-md bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
        >
          確認並生成音頻
        </button>
      </div>

      {/* Branch section (story only) */}
      {!isSong && (
        <div className="space-y-3 border-t pt-4">
          <h3 className="text-sm font-medium">故事延伸</h3>
          {branches.length === 0 ? (
            <button
              type="button"
              onClick={generateBranches}
              disabled={isGeneratingBranches}
              className="rounded-md border border-input bg-background px-4 py-2 text-sm transition-colors hover:bg-accent disabled:opacity-50"
            >
              {isGeneratingBranches ? '生成走向中...' : '生成故事走向選項'}
            </button>
          ) : (
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">選擇一個故事走向：</p>
              {branches.map((branch) => (
                <button
                  key={branch.id}
                  type="button"
                  onClick={() => selectBranch(branch.id)}
                  disabled={isGeneratingBranches}
                  className="w-full rounded-md border border-input bg-background px-4 py-3 text-left text-sm transition-colors hover:bg-accent disabled:opacity-50"
                >
                  {branch.description}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Q&A section */}
      <div className="space-y-3 border-t pt-4">
        <h3 className="text-sm font-medium">Q&A 互動</h3>
        {qaQuestions.length === 0 ? (
          <button
            type="button"
            onClick={generateQuestions}
            disabled={isGeneratingQA}
            className="rounded-md border border-input bg-background px-4 py-2 text-sm transition-colors hover:bg-accent disabled:opacity-50"
          >
            {isGeneratingQA ? '生成問題中...' : '生成思考問題'}
          </button>
        ) : (
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">選擇一個問題或輸入自訂問題：</p>
            {qaQuestions.map((q) => (
              <button
                key={q.id}
                type="button"
                onClick={() => askQuestion(q.text)}
                disabled={isGeneratingQA}
                className="w-full rounded-md border border-input bg-background px-4 py-3 text-left text-sm transition-colors hover:bg-accent disabled:opacity-50"
              >
                {q.text}
              </button>
            ))}
            <CustomQuestionInput />
          </div>
        )}

        {/* QA answers */}
        {qaAnswers.length > 0 && (
          <div className="space-y-3">
            {qaAnswers.map((qa, i) => (
              <div key={i} className="rounded-md border bg-muted/30 px-4 py-3 text-sm">
                <p className="font-medium">Q: {qa.question}</p>
                <p className="mt-1 text-muted-foreground">A: {qa.answer}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function CustomQuestionInput() {
  const { askQuestion, isGeneratingQA } = useStoryExperienceStore()
  const [customQ, setCustomQ] = useState('')

  const handleSubmit = async () => {
    if (!customQ.trim()) return
    await askQuestion(customQ.trim())
    setCustomQ('')
  }

  return (
    <div className="flex gap-2">
      <input
        type="text"
        value={customQ}
        onChange={(e) => setCustomQ(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
        placeholder="輸入自訂問題..."
        className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm"
      />
      <button
        type="button"
        onClick={handleSubmit}
        disabled={isGeneratingQA || !customQ.trim()}
        className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50"
      >
        提問
      </button>
    </div>
  )
}

