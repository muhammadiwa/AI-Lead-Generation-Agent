import { Routes, Route, Navigate } from 'react-router-dom'
import DashboardLayout from './components/layout/DashboardLayout'
import LeadsPage from './pages/LeadsPage'
import LeadDetailPage from './pages/LeadDetailPage'
import PipelinePage from './pages/PipelinePage'
import SourcesPage from './pages/SourcesPage'
import CampaignsPage from './pages/CampaignsPage'
import CreateCampaignPage from './pages/CreateCampaignPage'
import AnalyticsPage from './pages/AnalyticsPage'

function App() {
  return (
    <Routes>
      <Route element={<DashboardLayout />}>
        <Route path="/" element={<Navigate to="/leads" replace />} />
        <Route path="/leads" element={<LeadsPage />} />
        <Route path="/leads/:id" element={<LeadDetailPage />} />
        <Route path="/pipeline" element={<PipelinePage />} />
        <Route path="/sources" element={<SourcesPage />} />
        <Route path="/campaigns" element={<CampaignsPage />} />
        <Route path="/campaigns/new" element={<CreateCampaignPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
      </Route>
    </Routes>
  )
}

export default App
