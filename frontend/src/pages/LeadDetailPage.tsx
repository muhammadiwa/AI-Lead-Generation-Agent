import { useParams, Link } from 'react-router-dom'
import { 
  ArrowLeft, 
  Linkedin, 
  Github, 
  Globe, 
  Mail, 
  MessageSquare,
  History,
  TrendingUp,
  Award,
  Calendar,
  Building,
  MapPin,
  ExternalLink,
  MoreVertical
} from 'lucide-react'
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts'
import { clsx } from 'clsx'

const scoreData = [
  { name: 'ICP Fit', value: 30, max: 30, color: '#6366f1' },
  { name: 'Tech Signal', value: 25, max: 25, color: '#8b5cf6' },
  { name: 'Budget', value: 15, max: 20, color: '#ec4899' },
  { name: 'Engagement', value: 12, max: 15, color: '#f59e0b' },
  { name: 'Urgency', value: 8, max: 10, color: '#10b981' },
]

const history = [
  { id: '1', type: 'discovery', title: 'Lead Discovered', date: 'June 1, 2024', description: 'Found via LinkedIn search (VP Engineering).' },
  { id: '2', type: 'research', title: 'AI Research Completed', date: 'June 1, 2024', description: 'Detected tech stack: React, Node.js, AWS.' },
  { id: '3', type: 'scoring', title: 'Lead Qualified (HOT)', date: 'June 1, 2024', description: 'Composite score: 90/100.' },
  { id: '4', type: 'outreach', title: 'Initial Email Sent', date: 'June 2, 2024', description: 'Template: Tech Stack Modernization.' },
  { id: '5', type: 'outreach', title: 'Email Opened', date: 'June 3, 2024', description: 'Recipient opened the email 3 times.' },
]

export default function LeadDetailPage() {
  const { id } = useParams()

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to="/leads" className="p-2 hover:bg-gray-100 rounded-full transition-colors">
          <ArrowLeft className="h-5 w-5 text-gray-500" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Sarah Johnson</h1>
          <div className="flex items-center gap-4 mt-1">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
              <TrendingUp className="h-3 w-3" /> Qualified Hot
            </span>
            <span className="text-sm text-gray-500 flex items-center gap-1">
               <Building className="h-4 w-4" /> VP Engineering at TechFlow
            </span>
          </div>
        </div>
        <div className="ml-auto flex gap-2">
           <button className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
             Edit Lead
           </button>
           <button className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700">
             Start Outreach
           </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Profile Info */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Lead Profile</h3>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600">
                   <Linkedin className="h-5 w-5" />
                </div>
                <div>
                   <p className="text-sm font-medium text-gray-900">LinkedIn Profile</p>
                   <a href="#" className="text-xs text-indigo-600 hover:underline flex items-center gap-1">
                     /in/sarah-johnson <ExternalLink className="h-3 w-3" />
                   </a>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-600">
                   <Mail className="h-5 w-5" />
                </div>
                <div>
                   <p className="text-sm font-medium text-gray-900">Email Address</p>
                   <p className="text-xs text-gray-500">sarah.j@techflow.io</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-gray-600">
                   <MapPin className="h-5 w-5" />
                </div>
                <div>
                   <p className="text-sm font-medium text-gray-900">Location</p>
                   <p className="text-xs text-gray-500">San Francisco, CA</p>
                </div>
              </div>
            </div>

            <div className="mt-8">
              <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Detected Tech Stack</h4>
              <div className="flex flex-wrap gap-2">
                {['React', 'Node.js', 'TypeScript', 'AWS', 'PostgreSQL', 'Tailwind'].map(tech => (
                  <span key={tech} className="px-2 py-1 bg-gray-50 border border-gray-200 rounded text-xs text-gray-600">
                    {tech}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Company Context</h3>
            <p className="text-sm text-gray-600 leading-relaxed">
              TechFlow recently raised $15M in Series A funding. They are aggressively hiring for their engineering team to rebuild their legacy dashboard using a modern stack.
            </p>
            <div className="mt-4 flex items-center gap-4">
              <div className="text-center flex-1 p-2 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500">Team Size</p>
                <p className="text-sm font-bold text-gray-900">45-50</p>
              </div>
              <div className="text-center flex-1 p-2 bg-gray-50 rounded-lg">
                <p className="text-xs text-gray-500">Industry</p>
                <p className="text-sm font-bold text-gray-900">Fintech</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Scoring & History */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Score Breakdown</h3>
              <div className="text-right">
                <p className="text-3xl font-bold text-indigo-600">90</p>
                <p className="text-xs text-gray-500 uppercase font-medium">Composite Score</p>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
              <div className="h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={scoreData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f3f4f6" />
                    <XAxis type="number" hide />
                    <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#4b5563' }} width={80} />
                    <Tooltip cursor={{ fill: '#f9fafb' }} />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={20}>
                      {scoreData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-4">
                {scoreData.map(item => (
                  <div key={item.name}>
                    <div className="flex justify-between text-xs mb-1">
                       <span className="font-medium text-gray-700">{item.name}</span>
                       <span className="text-gray-500">{item.value} / {item.max}</span>
                    </div>
                    <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                       <div 
                         className="h-full rounded-full" 
                         style={{ width: `${(item.value / item.max) * 100}%`, backgroundColor: item.color }} 
                       />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
             <div className="p-6 border-b border-gray-100 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                   <History className="h-5 w-5 text-gray-400" /> Timeline & Activity
                </h3>
                <button className="text-xs font-medium text-indigo-600 hover:underline">View All</button>
             </div>
             <div className="p-6">
                <div className="flow-root">
                  <ul role="list" className="-mb-8">
                    {history.map((item, itemIdx) => (
                      <li key={item.id}>
                        <div className="relative pb-8">
                          {itemIdx !== history.length - 1 ? (
                            <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200" aria-hidden="true" />
                          ) : null}
                          <div className="relative flex space-x-3">
                            <div>
                              <span className={clsx(
                                "h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white",
                                item.type === 'discovery' ? 'bg-blue-500' :
                                item.type === 'research' ? 'bg-purple-500' :
                                item.type === 'scoring' ? 'bg-green-500' : 'bg-orange-500'
                              )}>
                                {item.type === 'outreach' ? <Mail className="h-4 w-4 text-white" /> : <Award className="h-4 w-4 text-white" />}
                              </span>
                            </div>
                            <div className="flex min-w-0 flex-1 justify-between space-x-4 pt-1.5">
                              <div>
                                <p className="text-sm font-bold text-gray-900">{item.title}</p>
                                <p className="text-sm text-gray-500 mt-0.5">{item.description}</p>
                              </div>
                              <div className="whitespace-nowrap text-right text-xs text-gray-500">
                                {item.date}
                              </div>
                            </div>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
             </div>
          </div>
        </div>
      </div>
    </div>
  )
}
