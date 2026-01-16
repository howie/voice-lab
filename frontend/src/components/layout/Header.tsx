import { Bell, User } from 'lucide-react'

export function Header() {
  return (
    <header className="flex h-16 items-center justify-between border-b bg-card px-6">
      <div>
        {/* Breadcrumb or page title can go here */}
      </div>
      <div className="flex items-center gap-4">
        <button className="rounded-lg p-2 text-muted-foreground hover:bg-accent hover:text-accent-foreground">
          <Bell className="h-5 w-5" />
        </button>
        <button className="flex items-center gap-2 rounded-lg p-2 text-muted-foreground hover:bg-accent hover:text-accent-foreground">
          <User className="h-5 w-5" />
          <span className="text-sm">使用者</span>
        </button>
      </div>
    </header>
  )
}
