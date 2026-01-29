import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  MessageSquare,
  Mic,
  MessagesSquare,
  History,
  Key,
  Users,
  Briefcase,
  Disc3,
  Music,
  ChevronLeft,
  ChevronRight,
  UserCog,
  Settings,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'TTS 測試', href: '/tts', icon: MessageSquare },
  { name: '多角色 TTS', href: '/multi-role-tts', icon: Users },
  { name: '背景工作', href: '/jobs', icon: Briefcase },
  { name: 'STT 測試', href: '/stt', icon: Mic },
  { name: '互動測試', href: '/interaction', icon: MessagesSquare },
  { name: 'Magic DJ', href: '/magic-dj', icon: Disc3 },
  { name: 'AI 音樂', href: '/music', icon: Music },
  { name: '歷史紀錄', href: '/history', icon: History },
  { name: '進階功能', href: '/advanced', icon: Settings },
  { name: '角色管理', href: '/voice-management', icon: UserCog },
  { name: 'API 金鑰', href: '/settings/providers', icon: Key },
]

export function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false)

  return (
    <aside
      className={cn(
        'flex flex-col border-r bg-card transition-all duration-300',
        isCollapsed ? 'w-16' : 'w-64'
      )}
    >
      <div
        className={cn(
          'flex h-16 items-center border-b',
          isCollapsed ? 'justify-center px-2' : 'gap-2 px-6'
        )}
      >
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Mic className="h-4 w-4" />
        </div>
        {!isCollapsed && (
          <span className="text-lg font-semibold">Voice Lab</span>
        )}
      </div>
      <nav className={cn('flex-1 space-y-1', isCollapsed ? 'p-2' : 'p-4')}>
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            title={isCollapsed ? item.name : undefined}
            className={({ isActive }) =>
              cn(
                'flex items-center rounded-lg text-sm font-medium transition-colors',
                isCollapsed
                  ? 'justify-center p-2'
                  : 'gap-3 px-3 py-2',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )
            }
          >
            <item.icon className="h-4 w-4 shrink-0" />
            {!isCollapsed && item.name}
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
