import { useState } from 'react'
import { 
  Search, 
  Filter, 
  MoreVertical, 
  Plus, 
  MoreHorizontal,
  Mail,
  Linkedin,
  Clock
} from 'lucide-react'
import { clsx } from 'clsx'

const stages = [
  { id: 'hot', name: 'Hot Leads', color: 'bg-red-500' },
  { id: 'warm', name: 'Warm Leads', color: 'bg-orange-500' },
  { id: 'cold', name: 'Cold Pool', color: 'bg-blue-500' },
  { id: 'qualified', name: 'Qualified', color: 'bg-green-500' },
]

const initialLeads = [
  { id: '1', name: 'Sarah Johnson', company: 'TechFlow', score: 92, stage: 'hot', source: 'linkedin', lastActive: '2h ago' },
  { id: '2', name: 'Michael Chen', company: 'CloudScale', score: 85, stage: 'hot', source: 'github', lastActive: '5h ago' },
  { id: '3', name: 'Emma Wilson', company: 'DataViz', score: 64, stage: 'warm', source: 'linkedin', lastActive: '1d ago' },
  { id: '4', name: 'James Miller', company: 'Innovate AI', score: 71, stage: 'warm', source: 'crunchbase', lastActive: '3h ago' },
  { id: '5', name: 'Olivia Brown', company: 'EcoTech', score: 45, stage: 'cold', source: 'web', lastActive: '2d ago' },
]

export default function PipelinePage() {
  const [leads, setLeads] = useState(initialLeads)

  const getLeadsByStage = (stageId: string) => leads.filter(l => l.stage === stageId)

  return (
    <div className="h-full flex flex-col space-y-6">
      <div className="sm:flex sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Pipeline</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage leads through different stages of the qualification funnel.
          </p>
        </div>
        <div className="flex gap-2">
          <button className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
             <Filter className="h-4 w-4" /> Filter
          </button>
          <button className="flex items-center gap-2 rounded-md bg-indigo-600 px-3 py-2 text-center text-sm font-semibold text-white shadow-sm hover:bg-indigo-500">
            <Plus className="h-4 w-4" /> Add Lead
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-x-auto pb-4">
        <div className="inline-flex gap-6 h-full min-w-full">
          {stages.map((stage) => (
            <div key={stage.id} className="w-80 flex-shrink-0 flex flex-col bg-gray-100 rounded-xl border border-gray-200">
              <div className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className={clsx("w-2 h-2 rounded-full", stage.color)} />
                  <h3 className="font-semibold text-gray-900">{stage.name}</h3>
                  <span className="text-xs font-medium text-gray-500 bg-gray-200 px-2 py-0.5 rounded-full">
                    {getLeadsByStage(stage.id).length}
                  </span>
                </div>
                <button className="text-gray-400 hover:text-gray-600">
                  <MoreHorizontal className="h-5 w-5" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-2 space-y-3">
                {getLeadsByStage(stage.id).map((lead) => (
                  <div 
                    key={lead.id} 
                    className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow cursor-grab active:cursor-grabbing"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="text-sm font-bold text-gray-900">{lead.name}</h4>
                        <p className="text-xs text-gray-500">{lead.company}</p>
                      </div>
                      <div className={clsx(
                        "text-[10px] font-bold px-1.5 py-0.5 rounded",
                        lead.score >= 80 ? "bg-green-100 text-green-700" : 
                        lead.score >= 50 ? "bg-yellow-100 text-yellow-700" : "bg-gray-100 text-gray-700"
                      )}>
                        {lead.score}
                      </div>
                    </div>
                    
                    <div className="mt-4 flex items-center justify-between">
                      <div className="flex gap-1.5">
                        <div className="p-1 rounded bg-gray-50 border border-gray-100">
                           {lead.source === 'linkedin' ? <Linkedin className="h-3 w-3 text-gray-400" /> : <Mail className="h-3 w-3 text-gray-400" />}
                        </div>
                      </div>
                      <div className="flex items-center gap-1 text-[10px] text-gray-400 font-medium">
                        <Clock className="h-3 w-3" /> {lead.lastActive}
                      </div>
                    </div>
                  </div>
                ))}
                
                {getLeadsByStage(stage.id).length === 0 && (
                  <div className="h-24 flex items-center justify-center border-2 border-dashed border-gray-300 rounded-lg">
                    <p className="text-xs text-gray-400">No leads in this stage</p>
                  </div>
                )}
              </div>
              
              <div className="p-2 border-t border-gray-200">
                 <button className="w-full flex items-center justify-center gap-1 py-1.5 text-xs font-medium text-gray-500 hover:text-indigo-600 hover:bg-white rounded-md transition-colors">
                    <Plus className="h-3 w-3" /> Add Lead
                 </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
