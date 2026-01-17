/**
 * AuthCallback Component
 * T051: Handle OAuth callback after Google login
 */

import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { Spinner } from '@/components/tts/LoadingIndicator'
import { authApi } from '@/lib/api'

export function AuthCallback() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { setToken, setUser, checkAuth } = useAuthStore()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code')
      const error = searchParams.get('error')

      if (error) {
        setError(`認證錯誤: ${error}`)
        return
      }

      if (!code) {
        setError('缺少認證碼')
        return
      }

      try {
        // Exchange code for token
        const response = await authApi.callback(code)
        const { access_token, user } = response.data

        // Store token and user
        setToken(access_token)
        setUser(user)

        // Redirect to home or original destination
        navigate('/', { replace: true })
      } catch (err: any) {
        console.error('Auth callback error:', err)
        setError(err.response?.data?.detail || '認證處理失敗')
      }
    }

    handleCallback()
  }, [searchParams, setToken, setUser, navigate, checkAuth])

  if (error) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-background">
        <div className="w-full max-w-md rounded-xl border bg-card p-8 shadow-lg">
          <div className="text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="currentColor"
                className="h-6 w-6 text-destructive"
              >
                <path
                  fillRule="evenodd"
                  d="M12 2.25c-5.385 0-9.75 4.365-9.75 9.75s4.365 9.75 9.75 9.75 9.75-4.365 9.75-9.75S17.385 2.25 12 2.25zm-1.72 6.97a.75.75 0 10-1.06 1.06L10.94 12l-1.72 1.72a.75.75 0 101.06 1.06L12 13.06l1.72 1.72a.75.75 0 101.06-1.06L13.06 12l1.72-1.72a.75.75 0 10-1.06-1.06L12 10.94l-1.72-1.72z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <h2 className="text-lg font-semibold">登入失敗</h2>
            <p className="mt-2 text-sm text-muted-foreground">{error}</p>
            <button
              onClick={() => navigate('/login', { replace: true })}
              className="mt-6 w-full rounded-lg bg-primary py-2 text-sm text-primary-foreground hover:bg-primary/90"
            >
              返回登入頁面
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background">
      <div className="flex flex-col items-center gap-4">
        <Spinner className="h-8 w-8 text-primary" />
        <p className="text-sm text-muted-foreground">正在完成登入...</p>
      </div>
    </div>
  )
}
