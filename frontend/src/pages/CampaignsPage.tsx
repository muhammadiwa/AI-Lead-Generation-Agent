import { useState } from 'react'
import { 
  Plus, 
  Search, 
  Filter, 
  MoreVertical,
  Play,
  Pause,
  BarChart2,
  Mail,
  Linkedin,
  MessageSquare
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { clsx } from 'clsx'

// Mock Data
const mockCampaigns = [
  {
    id: '1',
    name: 'Tech Stack Modernization',
    status: 'active',
    channels: ['email', 'linkedin'],
    leads_processed: 124,
    max_leads: 500,
    performance: { sent: 124, opened: 68, replied: 12, converted: 3 },
    created_at: '2024-06-01T10:00:00Z',
  },
  {
    id: '2',
    name: 'SaaS Founder Outreach',
    status: 'paused',
    channels: ['email'],
    leads_processed: 45,
    max_leads: 200,
    performance: { sent: 45, opened: 22, replied: 4, converted: 1 },
    created_at: '2024-06-03T14:30:00Z',
  },
  {
    id: '3',
    name: 'AI Agency Lead Gen',
    status: 'draft',
    channels: ['email', 'linkedin', 'whatsapp'],
    leads_processed: 0,
    max_leads: 1000,
    performance: { sent: 0, opened: 0, replied: 0, converted: 0 },
    created_at: '2024-06-07T09:15:00Z',
  }
]

const statusStyles = {
  active: 'bg-green-100 text-green-800',
  paused: 'bg-yellow-100 text-yellow-800',
  draft: 'bg-gray-100 text-gray-800',
  completed: 'bg-blue-100 text-blue-800',
  archived: 'bg-slate-100 text-slate-600',
}

export default function CampaignsPage() {
  const [searchTerm, setSearchTerm] = useState('')

  const filteredCampaigns = mockCampaigns.filter(campaign => 
    campaign.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div className="sm:flex sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Campaigns</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage your outreach campaigns and monitor performance.
          </p>
        </div>
        <div className="mt-4 sm:ml-16 sm:mt-0 sm:flex-none">
          <Link
            to="/campaigns/new"
            className="flex items-center gap-2 rounded-md bg-indigo-600 px-3 py-2 text-center text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
          >
            <Plus className="h-4 w-4" />
            Create Campaign
          </Link>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
        <div className="relative flex-1 w-full">
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
            <Search className="h-5 w-5 text-gray-400" aria-hidden="true" />
          </div>
          <input
            type="text"
            className="block w-full rounded-md border-0 py-1.5 pl-10 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
            placeholder="Search campaigns..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="flex gap-2 w-full sm:w-auto">
          <button className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors">
            <Filter className="h-4 w-4" />
            Filters
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {filteredCampaigns.map((campaign) => (
          <div key={campaign.id} className="bg-white overflow-hidden rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
            <div className="p-6 space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 truncate max-w-[200px]">
                    {campaign.name}
                  </h3>
                  <div className="mt-1 flex items-center gap-2">
                    <span className={clsx(
                      "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                      statusStyles[campaign.status as keyof typeof statusStyles]
                    )}>
                      {campaign.status}
                    </span>
                    <span className="text-xs text-gray-500">
                      Created {new Date(campaign.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                <button className="text-gray-400 hover:text-gray-600">
                  <MoreVertical className="h-5 w-5" />
                </button>
              </div>

              <div className="flex gap-2">
                {campaign.channels.map(channel => (
                  <div key={channel} className="p-1.5 rounded bg-gray-50 text-gray-600 border border-gray-100" title={channel}>
                    {channel === 'email' && <Mail className="h-4 w-4" />}
                    {channel === 'linkedin' && <Linkedin className="h-4 w-4" />}
                    {channel === 'whatsapp' && <MessageSquare className="h-4 w-4" />}
                  </div>
                ))}
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <span>Progress</span>
                  <span>{campaign.leads_processed} / {campaign.max_leads} leads</span>
                </div>
                <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-indigo-600 rounded-full"
                    style={{ width: `${(campaign.leads_processed / campaign.max_leads) * 100}%` }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-4 gap-2 pt-2">
                <div className="text-center">
                  <p className="text-lg font-bold text-gray-900">{campaign.performance.sent}</p>
                  <p className="text-[10px] text-gray-500 uppercase">Sent</p>
                </div>
                <div className="text-center">
                  <p className="text-lg font-bold text-gray-900">
                    {Math.round((campaign.performance.opened / (campaign.performance.sent || 1)) * 100)}%
                  </p>
                  <p className="text-[10px] text-gray-500 uppercase">Open</p>
                </div>
                <div className="text-center">
                  <p className="text-lg font-bold text-gray-900">
                    {Math.round((campaign.performance.replied / (campaign.performance.sent || 1)) * 100)}%
                  </p>
                  <p className="text-[10px] text-gray-500 uppercase">Reply</p>
                </div>
                <div className="text-center">
                  <p className="text-lg font-bold text-indigo-600">{campaign.performance.converted}</p>
                  <p className="text-[10px] text-gray-500 uppercase font-medium">Conv.</p>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 px-6 py-3 flex items-center justify-between border-t border-gray-100">
              <div className="flex gap-3">
                {campaign.status === 'active' ? (
                   <button className="flex items-center gap-1.5 text-sm font-medium text-yellow-700 hover:text-yellow-800">
                     <Pause className="h-4 w-4" /> Pause
                   </button>
                ) : (
                  <button className="flex items-center gap-1.5 text-sm font-medium text-green-700 hover:text-green-800">
                    <Play className="h-4 w-4" /> Start
                  </button>
                )}
              </div>
              <Link 
                to={`/campaigns/${campaign.id}`}
                className="flex items-center gap-1.5 text-sm font-medium text-indigo-600 hover:text-indigo-700"
              >
                <BarChart2 className="h-4 w-4" /> View Stats
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
