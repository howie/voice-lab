import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  MessageSquare,
  Mic,
  MessagesSquare,
  Key,
  Users,
  Briefcase,
  Disc3,
  Music,
  ChevronLeft,
  ChevronRight,
  UserCog,
  Gauge,
  Zap,
  BookOpen,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'StoryPal', href: '/storypal', icon: BookOpen, label: '新功能' },
  { name: 'TTS 測試', href: '/tts', icon: MessageSquare },
  { name: '多角色 TTS', href: '/multi-role-tts', icon: Users },
  { name: '背景工作', href: '/jobs', icon: Briefcase },
  { name: 'STT 測試', href: '/stt', icon: Mic, label: '開發中' },
  { name: '互動測試', href: '/interaction', icon: MessagesSquare, label: '調教中' },
  { name: 'Gemini 直連', href: '/gemini-live-test', icon: Zap, label: '實驗' },
  { name: 'Magic DJ', href: '/magic-dj', icon: Disc3, label: '實驗中' },
  { name: 'AI 音樂', href: '/music', icon: Music, label: '開發中' },
  { name: '角色管理', href: '/voice-management', icon: UserCog },
  { name: '配額監控', href: '/quota', icon: Gauge },
  { name: 'API 金鑰', href: '/settings/providers', icon: Key },
]

export function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false)

  return (
    <aside
      className={cn(
        'flex shrink-0 flex-col border-r bg-card transition-all duration-300',
        isCollapsed ? 'w-16' : 'w-fit'
      )}
    >
      <div
        className={cn(
          'flex h-12 items-center border-b',
          isCollapsed ? 'justify-center px-2' : 'gap-2 px-3'
        )}
      >
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground">
          <Mic className="h-3.5 w-3.5" />
        </div>
        {!isCollapsed && (
          <span className="text-sm font-semibold">Voice Lab</span>
        )}
      </div>
      <nav className={cn('flex-1 space-y-0.5', isCollapsed ? 'p-2' : 'p-2')}>
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            title={isCollapsed ? item.name : undefined}
            className={({ isActive }) =>
              cn(
                'flex items-center whitespace-nowrap rounded-md text-sm font-medium transition-colors',
                isCollapsed
                  ? 'justify-center p-2'
                  : 'gap-2 px-2 py-1.5',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )
            }
          >
            <item.icon className="h-3.5 w-3.5 shrink-0" />
            {!isCollapsed && (
              <span className="flex items-center gap-2">
                {item.name}
                {'label' in item && item.label && (
                  <span className="rounded-full bg-muted px-1.5 py-0.5 text-[10px] leading-none text-muted-foreground">
                    {item.label}
                  </span>
                )}
              </span>
            )}
          </NavLink>
        ))}
      </nav>
      <div className="border-t p-2">
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="flex w-full items-center justify-center rounded-lg p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
          title={isCollapsed ? '展開側邊欄' : '收合側邊欄'}
        >
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </button>
        {!isCollapsed && (
          <p className="mt-2 text-center text-xs text-muted-foreground">
            Voice Lab v0.1.0
          </p>
        )}
      </div>
    </aside>
  )
}
