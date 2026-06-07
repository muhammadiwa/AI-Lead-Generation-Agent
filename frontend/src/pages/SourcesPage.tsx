export default function SourcesPage() {
  const sources = [
    { name: 'LinkedIn Sales Navigator', enabled: true, status: 'Active' },
    { name: 'GitHub Explorer', enabled: true, status: 'Active' },
    { name: 'Crunchbase API', enabled: false, status: 'Disabled' },
    { name: 'Firecrawl Scraper', enabled: true, status: 'Active' },
  ]

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Data Sources</h1>
      <p className="mt-1 text-sm text-gray-500">Enable and configure data collection sources.</p>
      <div className="mt-6 bg-white shadow sm:rounded-lg border border-gray-200 overflow-hidden">
        <ul className="divide-y divide-gray-200">
          {sources.map((source) => (
            <li key={source.name} className="px-6 py-4 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900">{source.name}</p>
                <p className="text-sm text-gray-500">{source.status}</p>
              </div>
              <button
                type="button"
                className={`px-3 py-1 text-xs font-semibold rounded-full ${
                  source.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                }`}
              >
                {source.enabled ? 'Enabled' : 'Disabled'}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
