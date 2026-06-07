import { useState } from 'react'
import { 
  Search, 
  Filter, 
  ArrowUpDown, 
  MoreVertical,
  ExternalLink,
  ChevronRight,
  TrendingUp,
  Mail,
  Linkedin,
  Github
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { clsx } from 'clsx'

// Mock Data
const mockLeads = [
  {
    id: '1',
    company_name: 'TechFlow Systems',
    company_domain: 'techflow.io',
    industry: 'Cloud Infrastructure',
    employee_count: 120,
    status: 'qualified_hot',
    score_current: 88,
    location_city: 'San Francisco',
    location_country: 'USA',
    source: 'linkedin',
    created_at: '2024-06-05T10:00:00Z',
  },
  {
    id: '2',
    company_name: 'FinStream AI',
    company_domain: 'finstream.ai',
    industry: 'Fintech',
    employee_count: 45,
    status: 'qualified_warm',
    score_current: 65,
    location_city: 'London',
    location_country: 'UK',
    source: 'crunchbase',
    created_at: '2024-06-06T14:30:00Z',
  },
  {
    id: '3',
    company_name: 'GreenPulse',
    company_domain: 'greenpulse.eco',
    industry: 'Clean Energy',
    employee_count: 200,
    status: 'discovered',
    score_current: 42,
    location_city: 'Berlin',
    location_country: 'Germany',
    source: 'web_scrape',
    created_at: '2024-06-07T09:15:00Z',
  },
  {
    id: '4',
    company_name: 'Nova Health',
    company_domain: 'novahealth.com',
    industry: 'Healthtech',
    employee_count: 85,
    status: 'contacted',
    score_current: 78,
    location_city: 'New York',
    location_country: 'USA',
    source: 'apollo',
    created_at: '2024-06-01T11:20:00Z',
  },
  {
    id: '5',
    company_name: 'Quantum Soft',
    company_domain: 'quantumsoft.net',
    industry: 'Software Development',
    employee_count: 30,
    status: 'cold',
    score_current: 25,
    location_city: 'Toronto',
    location_country: 'Canada',
    source: 'github',
    created_at: '2024-05-28T16:45:00Z',
  }
]

const statusStyles = {
  discovered: 'bg-gray-100 text-gray-800',
  researching: 'bg-blue-100 text-blue-800',
  researched: 'bg-indigo-100 text-indigo-800',
  scored: 'bg-purple-100 text-purple-800',
  qualified_hot: 'bg-red-100 text-red-800',
  qualified_warm: 'bg-orange-100 text-orange-800',
  qualified_cool: 'bg-blue-50 text-blue-700',
  cold: 'bg-slate-100 text-slate-600',
  contacted: 'bg-yellow-100 text-yellow-800',
  responded: 'bg-green-100 text-green-800',
}

export default function LeadsPage() {
  const [searchTerm, setSearchTerm] = useState('')

  const filteredLeads = mockLeads.filter(lead => 
    lead.company_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    lead.industry.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div className="sm:flex sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Leads</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage and qualify your B2B leads from multiple sources.
          </p>
        </div>
        <div className="mt-4 sm:ml-16 sm:mt-0 sm:flex-none">
          <button
            type="button"
            className="block rounded-md bg-indigo-600 px-3 py-2 text-center text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
          >
            Import Leads
          </button>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-4 items-center justify-between bg-white p-4 rounded-lg border border-gray-200">
        <div className="relative flex-1 w-full">
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
            <Search className="h-5 w-5 text-gray-400" aria-hidden="true" />
          </div>
          <input
            type="text"
            className="block w-full rounded-md border-0 py-1.5 pl-10 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
            placeholder="Search leads..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="flex gap-2 w-full sm:w-auto">
          <button className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
            <Filter className="h-4 w-4" />
            Filters
          </button>
          <button className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
            <ArrowUpDown className="h-4 w-4" />
            Sort
          </button>
        </div>
      </div>

      <div className="overflow-hidden bg-white shadow sm:rounded-lg border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Company</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Status</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Score</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Source</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">Created</th>
              <th scope="col" className="relative px-6 py-3">
                <span className="sr-only">Edit</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {filteredLeads.map((lead) => (
              <tr key={lead.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="h-10 w-10 flex-shrink-0 rounded-lg bg-indigo-100 flex items-center justify-center">
                      <span className="text-indigo-700 font-bold text-lg">{lead.company_name[0]}</span>
                    </div>
                    <div className="ml-4">
                      <Link to={`/leads/${lead.id}`} className="text-sm font-medium text-gray-900 hover:text-indigo-600 flex items-center gap-1">
                        {lead.company_name}
                        <ChevronRight className="h-4 w-4" />
                      </Link>
                      <div className="text-xs text-gray-500 flex items-center gap-1">
                        {lead.company_domain}
                        <ExternalLink className="h-3 w-3" />
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={clsx(
                    "inline-flex rounded-full px-2 text-xs font-semibold leading-5",
                    statusStyles[lead.status as keyof typeof statusStyles]
                  )}>
                    {lead.status.replace('_', ' ')}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 w-16 bg-gray-200 rounded-full overflow-hidden">
                      <div 
                        className={clsx(
                          "h-full rounded-full",
                          lead.score_current >= 70 ? "bg-green-500" : 
                          lead.score_current >= 50 ? "bg-yellow-500" : "bg-red-500"
                        )}
                        style={{ width: `${lead.score_current}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium text-gray-900">{lead.score_current}</span>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 uppercase">
                   <div className="flex items-center gap-1">
                      {lead.source === 'linkedin' && <Linkedin className="h-4 w-4 text-blue-600" />}
                      {lead.source === 'github' && <Github className="h-4 w-4 text-gray-900" />}
                      {lead.source === 'crunchbase' && <TrendingUp className="h-4 w-4 text-blue-400" />}
                      {lead.source === 'web_scrape' && <Search className="h-4 w-4 text-gray-400" />}
                      {lead.source === 'apollo' && <Mail className="h-4 w-4 text-indigo-400" />}
                      {lead.source}
                   </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(lead.created_at).toLocaleDateString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button className="text-gray-400 hover:text-gray-600">
                    <MoreVertical className="h-5 w-5" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
