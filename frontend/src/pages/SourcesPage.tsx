import { useState } from 'react'
import { 
  Database, 
  Linkedin, 
  Github, 
  Globe, 
  Search, 
  Settings2, 
  ShieldCheck,
  Plus,
  RefreshCw,
  ExternalLink
} from 'lucide-react'
import { clsx } from 'clsx'

const mockSources = [
  {
    id: 'linkedin',
    name: 'LinkedIn Sales Navigator',
    description: 'Find decision makers and company profiles on LinkedIn.',
    icon: Linkedin,
    status: 'active',
    lastSync: '2 minutes ago',
    config: {
      queries: ['VP Engineering', 'CTO'],
      location: 'United States',
    }
  },
  {
    id: 'github',
    name: 'GitHub Explorer',
    description: 'Analyze repositories, tech stacks, and contributors.',
    icon: Github,
    status: 'active',
    lastSync: '1 hour ago',
    config: {
      topics: ['react', 'python'],
      minStars: 100,
    }
  },
  {
    id: 'crunchbase',
    name: 'Crunchbase API',
    description: 'Track recent funding rounds and new companies.',
    icon: Globe,
    status: 'disabled',
    lastSync: 'Never',
    config: {
      fundingRounds: ['Series A', 'Seed'],
    }
  },
  {
    id: 'firecrawl',
    name: 'Firecrawl Scraper',
    description: 'Advanced web scraping for job boards and news.',
    icon: Search,
    status: 'active',
    lastSync: '15 minutes ago',
    config: {
      domains: ['ycombinator.com/jobs'],
    }
  },
]

export default function SourcesPage() {
  const [sources, setSources] = useState(mockSources)

  const toggleSource = (id: string) => {
    setSources(sources.map(s => 
      s.id === id 
        ? { ...s, status: s.status === 'active' ? 'disabled' : 'active' } 
        : s
    ))
  }

  return (
    <div className="space-y-6">
      <div className="sm:flex sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Data Sources</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage your lead discovery sources and synchronization settings.
          </p>
        </div>
        <div className="mt-4 sm:ml-16 sm:mt-0 sm:flex-none">
          <button
            className="flex items-center gap-2 rounded-md bg-indigo-600 px-3 py-2 text-center text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
          >
            <Plus className="h-4 w-4" />
            Add Custom Source
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {sources.map((source) => (
          <div key={source.id} className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                  <div className={clsx(
                    "p-3 rounded-lg",
                    source.status === 'active' ? "bg-indigo-50 text-indigo-600" : "bg-gray-100 text-gray-400"
                  )}>
                    <source.icon className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{source.name}</h3>
                    <p className="text-sm text-gray-500">{source.description}</p>
                  </div>
                </div>
                <button
                  onClick={() => toggleSource(source.id)}
                  className={clsx(
                    "relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2",
                    source.status === 'active' ? "bg-indigo-600" : "bg-gray-200"
                  )}
                >
                  <span className={clsx(
                    "pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out",
                    source.status === 'active' ? "translate-x-5" : "translate-x-0"
                  )} />
                </button>
              </div>

              <div className="mt-6 grid grid-cols-2 gap-4 border-t border-gray-100 pt-6">
                <div>
                  <p className="text-xs font-bold text-gray-500 uppercase">Status</p>
                  <div className="mt-1 flex items-center gap-2">
                    <div className={clsx(
                      "h-2 w-2 rounded-full",
                      source.status === 'active' ? "bg-green-500" : "bg-gray-300"
                    )} />
                    <span className="text-sm font-medium capitalize">{source.status}</span>
                  </div>
                </div>
                <div>
                  <p className="text-xs font-bold text-gray-500 uppercase">Last Sync</p>
                  <p className="mt-1 text-sm font-medium text-gray-900 flex items-center gap-1">
                    <RefreshCw className="h-3 w-3 text-gray-400" /> {source.lastSync}
                  </p>
                </div>
              </div>

              <div className="mt-6 space-y-4">
                 <p className="text-xs font-bold text-gray-500 uppercase">Current Configuration</p>
                 <div className="bg-gray-50 rounded-lg p-4 flex flex-wrap gap-2">
                    {Object.entries(source.config).map(([key, value]) => (
                      <div key={key} className="bg-white border border-gray-200 rounded px-2 py-1 flex items-center gap-2">
                        <span className="text-[10px] font-bold text-gray-400 uppercase">{key}:</span>
                        <span className="text-xs text-gray-700 font-medium">
                          {Array.isArray(value) ? value.join(', ') : value}
                        </span>
                      </div>
                    ))}
                    <button className="text-xs text-indigo-600 font-medium flex items-center gap-1 hover:underline">
                      <Settings2 className="h-3 w-3" /> Edit
                    </button>
                 </div>
              </div>
            </div>
            <div className="bg-gray-50 px-6 py-3 border-t border-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <ShieldCheck className="h-4 w-4 text-green-500" />
                API connection secure
              </div>
              <button className="text-xs font-medium text-indigo-600 hover:text-indigo-500 flex items-center gap-1">
                View Logs <ExternalLink className="h-3 w-3" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
