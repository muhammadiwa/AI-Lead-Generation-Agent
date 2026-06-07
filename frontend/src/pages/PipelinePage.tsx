export default function PipelinePage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Pipeline</h1>
      <p className="mt-1 text-sm text-gray-500">Visual kanban board of your lead stages.</p>
      <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-3">
        {['Hot', 'Warm', 'Cold'].map((stage) => (
          <div key={stage} className="bg-gray-100 rounded-lg p-4 min-h-[400px]">
            <h3 className="font-semibold text-gray-700 mb-4">{stage}</h3>
            <div className="bg-white p-3 rounded shadow-sm border border-gray-200">
              Sample Lead Card
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
