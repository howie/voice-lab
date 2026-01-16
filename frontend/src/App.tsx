import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { Dashboard } from '@/routes/Dashboard'
import { TTSPage } from '@/routes/tts/TTSPage'
import { STTPage } from '@/routes/stt/STTPage'
import { InteractionPage } from '@/routes/interaction/InteractionPage'
import { HistoryPage } from '@/routes/history/HistoryPage'
import { AdvancedPage } from '@/routes/advanced/AdvancedPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="tts" element={<TTSPage />} />
          <Route path="stt" element={<STTPage />} />
          <Route path="interaction" element={<InteractionPage />} />
          <Route path="history" element={<HistoryPage />} />
          <Route path="advanced" element={<AdvancedPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
