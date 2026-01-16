import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  MessageSquare,
  Mic,
  MessagesSquare,
  History,
  Settings
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'TTS 測試', href: '/tts', icon: MessageSquare },
  { name: 'STT 測試', href: '/stt', icon: Mic },
  { name: '互動測試', href: '/interaction', icon: MessagesSquare },
  { name: '歷史紀錄', href: '/history', icon: History },
  { name: '進階功能', href: '/advanced', icon: Settings },
]

export function Sidebar() {
  return (
    <aside className="flex w-64 flex-col border-r bg-card">
      <div className="flex h-16 items-center gap-2 border-b px-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Mic className="h-4 w-4" />
        </div>
        <span className="text-lg font-semibold">Voice Lab</span>
      </div>
      <nav className="flex-1 space-y-1 p-4">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {item.name}
          </NavLink>
        ))}
      </nav>
      <div className="border-t p-4">
        <p className="text-xs text-muted-foreground">Voice Lab v0.1.0</p>
      </div>
    </aside>
  )
}
