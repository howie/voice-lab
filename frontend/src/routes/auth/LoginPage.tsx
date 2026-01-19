/**
 * LoginPage Component
 * T051: Login page for authentication
 */

import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { LoginButton } from '@/components/auth/LoginButton'
import { useLoginRedirect } from '@/hooks/useLoginRedirect'

export function LoginPage() {
  const { isAuthenticated, error, clearError } = useAuthStore()
  const navigate = useNavigate()
  const redirectPath = useLoginRedirect()

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate(redirectPath, { replace: true })
    }
  }, [isAuthenticated, navigate, redirectPath])

  // Clear error on unmount
  useEffect(() => {
    return () => clearError()
  }, [clearError])

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background">
      <div className="w-full max-w-md space-y-8 rounded-xl border bg-card p-8 shadow-lg">
        {/* Logo / Title */}
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight">Voice Lab</h1>
          <p className="mt-2 text-muted-foreground">
            文字轉語音測試平台
          </p>
        </div>

        {/* Login form */}
        <div className="space-y-6">
          <div className="space-y-2 text-center">
            <h2 className="text-lg font-semibold">登入您的帳號</h2>
            <p className="text-sm text-muted-foreground">
              使用 Google 帳號登入以使用所有功能
            </p>
          </div>

          {/* Error message */}
          {error && (
            <div className="rounded-lg bg-destructive/10 p-4 text-sm text-destructive">
              <p className="font-medium">登入失敗</p>
              <p className="mt-1">{error}</p>
            </div>
          )}

          {/* Google login button */}
          <LoginButton className="w-full justify-center" />

          {/* Divider */}
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-card px-2 text-muted-foreground">或</span>
            </div>
          </div>

          {/* Guest access info */}
          <div className="rounded-lg bg-muted/50 p-4 text-sm">
            <p className="font-medium">訪客模式</p>
            <p className="mt-1 text-muted-foreground">
              部分功能需要登入才能使用，包括：
            </p>
            <ul className="mt-2 list-inside list-disc text-muted-foreground">
              <li>語音合成紀錄查詢</li>
              <li>自訂設定儲存</li>
              <li>API 金鑰管理</li>
            </ul>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-muted-foreground">
          登入即表示您同意我們的服務條款和隱私政策
        </p>
      </div>
    </div>
  )
}
