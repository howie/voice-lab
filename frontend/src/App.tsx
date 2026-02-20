import { lazy, Suspense, useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { LoginPage } from '@/routes/auth/LoginPage'
import { AuthCallback } from '@/routes/auth/AuthCallback'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { useAuthStore } from '@/stores/authStore'
import { Spinner } from '@/components/tts/LoadingIndicator'

// Lazy-loaded route pages (code splitting)
const Dashboard = lazy(() => import('@/routes/Dashboard').then(m => ({ default: m.Dashboard })))
const TTSPage = lazy(() => import('@/routes/tts/TTSPage').then(m => ({ default: m.TTSPage })))
const STTPage = lazy(() => import('@/routes/stt/STTPage').then(m => ({ default: m.STTPage })))
const STTHistoryPage = lazy(() => import('@/routes/stt/STTHistoryPage').then(m => ({ default: m.STTHistoryPage })))
const InteractionPage = lazy(() => import('@/routes/interaction/InteractionPage').then(m => ({ default: m.InteractionPage })))
const InteractionHistoryPage = lazy(() => import('@/routes/interaction/InteractionHistoryPage').then(m => ({ default: m.InteractionHistoryPage })))
const HistoryPage = lazy(() => import('@/routes/history/HistoryPage').then(m => ({ default: m.HistoryPage })))
const AdvancedPage = lazy(() => import('@/routes/advanced/AdvancedPage').then(m => ({ default: m.AdvancedPage })))
const ProviderSettings = lazy(() => import('@/routes/settings/ProviderSettings').then(m => ({ default: m.ProviderSettings })))
const MultiRoleTTSPage = lazy(() => import('@/routes/multi-role-tts/MultiRoleTTSPage').then(m => ({ default: m.MultiRoleTTSPage })))
const JobsPage = lazy(() => import('@/routes/jobs').then(m => ({ default: m.JobsPage })))
const MagicDJPage = lazy(() => import('@/routes/magic-dj/MagicDJPage').then(m => ({ default: m.MagicDJPage })))
const VoiceManagementPage = lazy(() => import('@/routes/voice-management').then(m => ({ default: m.VoiceManagementPage })))
const QuotaDashboardPage = lazy(() => import('@/routes/quota/QuotaDashboardPage').then(m => ({ default: m.QuotaDashboardPage })))
const MusicPage = lazy(() => import('@/routes/music').then(m => ({ default: m.MusicPage })))
const GeminiLiveTestPage = lazy(() => import('@/routes/gemini-live-test/GeminiLiveTestPage').then(m => ({ default: m.GeminiLiveTestPage })))
const StoryPalPage = lazy(() => import('@/routes/storypal/StoryPalPage').then(m => ({ default: m.StoryPalPage })))

function AppContent() {
  const checkAuth = useAuthStore((state) => state.checkAuth)
  const setToken = useAuthStore((state) => state.setToken)

  // Handle OAuth token from URL and check auth
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const token = params.get('token')
    const error = params.get('error')

    if (token) {
      // Store token, clean URL, then check auth
      setToken(token)
      window.history.replaceState({}, '', window.location.pathname)
      // checkAuth will be called after token is set
      checkAuth()
    } else if (error) {
      // Handle error (e.g., domain_not_allowed)
      console.error('OAuth error:', error)
      window.history.replaceState({}, '', window.location.pathname)
      checkAuth()
    } else {
      // No token in URL, just check existing auth
      checkAuth()
    }
  }, [setToken, checkAuth])

  return (
    <Suspense fallback={<div className="flex h-screen items-center justify-center"><Spinner className="h-8 w-8" /></div>}>
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/auth/callback" element={<AuthCallback />} />

      {/* Protected routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="tts" element={<TTSPage />} />
        <Route path="multi-role-tts" element={<MultiRoleTTSPage />} />
        <Route path="jobs" element={<JobsPage />} />
        <Route path="stt" element={<STTPage />} />
        <Route path="stt/history" element={<STTHistoryPage />} />
        <Route path="interaction" element={<InteractionPage />} />
        <Route path="interaction/history" element={<InteractionHistoryPage />} />
        <Route path="magic-dj" element={<MagicDJPage />} />
        <Route path="music" element={<MusicPage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="advanced" element={<AdvancedPage />} />
        <Route path="quota" element={<QuotaDashboardPage />} />
        <Route path="settings/providers" element={<ProviderSettings />} />
        <Route path="voice-management" element={<VoiceManagementPage />} />
        <Route path="gemini-live-test" element={<GeminiLiveTestPage />} />
        <Route path="storypal" element={<StoryPalPage />} />
      </Route>
    </Routes>
    </Suspense>
  )
}

function App() {
  return (
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <AppContent />
    </BrowserRouter>
  )
}

export default App
