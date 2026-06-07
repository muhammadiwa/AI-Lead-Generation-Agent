import { Routes, Route, Navigate } from 'react-router-dom'
import DashboardLayout from './components/layout/DashboardLayout'
import LeadsPage from './pages/LeadsPage'
import LeadDetailPage from './pages/LeadDetailPage'
import PipelinePage from './pages/PipelinePage'
import SourcesPage from './pages/SourcesPage'

function App() {
  return (
    <Routes>
      <Route element={<DashboardLayout />}>
        <Route path="/" element={<Navigate to="/leads" replace />} />
        <Route path="/leads" element={<LeadsPage />} />
        <Route path="/leads/:id" element={<LeadDetailPage />} />
        <Route path="/pipeline" element={<PipelinePage />} />
        <Route path="/sources" element={<SourcesPage />} />
      </Route>
    </Routes>
  )
}

export default App
