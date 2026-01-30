/**
 * DialogueInput Component
 * T030: Textarea for multi-role dialogue input with character count and format hints
 */

import { ChangeEvent } from 'react'
import { AlertCircle, HelpCircle, Sparkles } from 'lucide-react'
import type { MultiRoleTTSProvider } from '@/types/multi-role-tts'

interface DialogueInputProps {
  value: string
  onChange: (value: string) => void
  characterLimit: number
  disabled?: boolean
  provider?: MultiRoleTTSProvider
}

export function DialogueInput({
  value,
  onChange,
  characterLimit,
  disabled = false,
  provider,
}: DialogueInputProps) {
  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value)
  }

  const charCount = value.length
  const warningThreshold = characterLimit * 0.8
  const isWarning = charCount >= warningThreshold && charCount < characterLimit
  const isError = charCount >= characterLimit

  return (
    <div className="space-y-3">
      {/* Format hint */}
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-3">
        <div className="flex items-start gap-2">
          <HelpCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-blue-600" />
          <div className="text-xs text-blue-800">
            <p className="font-medium">支援的格式：</p>
            <ul className="mt-1 list-inside list-disc space-y-0.5">
              <li>
                字母格式：<code className="rounded bg-blue-100 px-1">A: 你好</code>{' '}
                <code className="rounded bg-blue-100 px-1">B: 嗨</code>
              </li>
              <li>
                方括號格式：<code className="rounded bg-blue-100 px-1">[主持人]: 歡迎</code>{' '}
                <code className="rounded bg-blue-100 px-1">[來賓]: 謝謝</code>
              </li>
              <li>支援中文冒號（：）和英文冒號（:）</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Gemini TTS specific guidance */}
      {provider === 'gemini' && (
        <div className="rounded-lg border border-purple-200 bg-purple-50 p-3">
          <div className="flex items-start gap-2">
            <Sparkles className="mt-0.5 h-4 w-4 flex-shrink-0 text-purple-600" />
            <div className="text-xs text-purple-800">
              <p className="font-medium">Gemini TTS 語音調教技巧：</p>
              <p className="mt-1 opacity-80">
                Style Prompt、SSML、情緒標籤直接寫在每行對話的文字內容中：
              </p>
              <div className="mt-1.5 space-y-1.5">
                <div>
                  <p className="font-medium">1. Style Prompt（語氣描述）</p>
                  <p className="opacity-80">
                    用自然語言描述語氣風格，前置於台詞：
                  </p>
                  <code className="mt-0.5 block rounded bg-purple-100 px-1.5 py-0.5">
                    A: 用溫暖友善的語氣說: 歡迎收聽今天的節目
                  </code>
                </div>
                <div>
                  <p className="font-medium">2. SSML 標記（精確控制）</p>
                  <p className="opacity-80">
                    控制語速、停頓、強調：
                  </p>
                  <code className="mt-0.5 block rounded bg-purple-100 px-1.5 py-0.5">
                    {'A: <prosody rate="slow">慢慢說</prosody> <break time="1s"/> 接下來...'}
                  </code>
                </div>
                <div>
                  <p className="font-medium">3. 行內情緒標籤（局部情緒）</p>
                  <p className="opacity-80">
                    用方括號標記情緒或動作：
                  </p>
                  <code className="mt-0.5 block rounded bg-purple-100 px-1.5 py-0.5">
                    A: [excited] 太棒了！ [whispering] 這是祕密...
                  </code>
                </div>
              </div>
              <details className="mt-2">
                <summary className="cursor-pointer font-medium hover:opacity-80">
                  範例：幼兒園老師講故事
                </summary>
                <pre className="mt-1.5 whitespace-pre-wrap rounded bg-purple-100 p-2 font-mono leading-relaxed">
{`[老師]: 用幼兒園老師溫柔又充滿驚喜的語氣說: 小朋友們～今天老師要講一個好好聽的故事喔！
[老師]: <prosody rate="slow">從前從前</prosody> <break time="800ms"/> 在一座大大的森林裡 <break time="500ms"/> 住著一隻 <emphasis level="strong">小小的兔子</emphasis>
[老師]: [excited] 猜猜看！小兔子叫什麼名字？ <break time="1s"/> 牠叫 <prosody pitch="+3st">跳跳</prosody>！
[老師]: [whispering] 有一天晚上，跳跳偷偷溜出門 <break time="500ms"/> 牠聽到了一個好奇怪的聲音
[老師]: <prosody rate="x-slow" pitch="-2st">咕嚕 <break time="300ms"/> 咕嚕 <break time="300ms"/> 咕嚕</prosody>
[老師]: [excited] 原來是跳跳的肚子餓了啦！ [laughing] 好好笑對不對？`}
                </pre>
              </details>
              <p className="mt-2 opacity-60">
                Pro 模型對指令遵循度較高；英文 prompt 效果通常優於中文
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Textarea */}
      <textarea
        value={value}
        onChange={handleChange}
        placeholder={`A: 你好，歡迎收聽今天的節目。
B: 謝謝，很高興來到這裡。
A: 今天我們要聊聊人工智慧的發展...`}
        disabled={disabled}
        className={`
          h-48 w-full rounded-lg border bg-background p-3 text-sm font-mono
          focus:outline-none focus:ring-2 focus:ring-primary
          disabled:cursor-not-allowed disabled:opacity-50
          ${isError ? 'border-destructive focus:ring-destructive' : ''}
          ${isWarning ? 'border-yellow-500 focus:ring-yellow-500' : ''}
        `}
      />

      {/* Character count and warnings */}
      <div className="flex items-center justify-between">
        {isError && (
          <div className="flex items-center gap-1 text-xs text-destructive">
            <AlertCircle className="h-3.5 w-3.5" />
            <span>已超過字數限制</span>
          </div>
        )}
        {isWarning && !isError && (
          <div className="flex items-center gap-1 text-xs text-yellow-600">
            <AlertCircle className="h-3.5 w-3.5" />
            <span>接近字數限制</span>
          </div>
        )}
        {!isWarning && !isError && <div />}

        <span
          className={`
            text-xs
            ${isError ? 'font-medium text-destructive' : ''}
            ${isWarning && !isError ? 'text-yellow-600' : ''}
            ${!isWarning && !isError ? 'text-muted-foreground' : ''}
          `}
        >
          {charCount.toLocaleString()} / {characterLimit.toLocaleString()} 字
        </span>
      </div>
    </div>
  )
}
