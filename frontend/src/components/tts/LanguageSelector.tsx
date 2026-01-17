/**
 * LanguageSelector Component
 * T062: Create LanguageSelector component (zh-TW, zh-CN, en-US, ja-JP, ko-KR)
 */

interface Language {
  code: string
  name: string
  nativeName: string
  flag: string
}

const SUPPORTED_LANGUAGES: Language[] = [
  { code: 'zh-TW', name: 'Traditional Chinese (Taiwan)', nativeName: '繁體中文 (台灣)', flag: '🇹🇼' },
  { code: 'zh-CN', name: 'Simplified Chinese (China)', nativeName: '简体中文 (中国)', flag: '🇨🇳' },
  { code: 'en-US', name: 'English (US)', nativeName: 'English (US)', flag: '🇺🇸' },
  { code: 'ja-JP', name: 'Japanese', nativeName: '日本語', flag: '🇯🇵' },
  { code: 'ko-KR', name: 'Korean', nativeName: '한국어', flag: '🇰🇷' },
]

interface LanguageSelectorProps {
  value: string
  onChange: (languageCode: string) => void
  disabled?: boolean
  showFlags?: boolean
}

export function LanguageSelector({
  value,
  onChange,
  disabled = false,
  showFlags = true,
}: LanguageSelectorProps) {
  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">語言</label>

      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="w-full rounded-lg border bg-background p-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary disabled:cursor-not-allowed disabled:opacity-50"
      >
        {SUPPORTED_LANGUAGES.map((lang) => (
          <option key={lang.code} value={lang.code}>
            {showFlags ? `${lang.flag} ` : ''}{lang.nativeName}
          </option>
        ))}
      </select>

      {/* Language code display */}
      <p className="text-xs text-muted-foreground">
        語言代碼: {value}
      </p>
    </div>
  )
}

// Export languages for reuse
export { SUPPORTED_LANGUAGES }
export type { Language }
