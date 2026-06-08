import { 
  Users, 
  Target, 
  TrendingUp, 
  Zap,
  ArrowUpRight,
  ArrowDownRight,
  Download,
  Calendar as CalendarIcon,
  Filter,
  History
} from 'lucide-react'
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  Cell,
  PieChart,
  Pie
} from 'recharts'
import { clsx } from 'clsx'
import { useState } from 'react'

const stats = [
  { name: 'Total Leads', value: '2,845', change: '+12.5%', trend: 'up' },
  { name: 'Conversion Rate', value: '3.2%', change: '+0.4%', trend: 'up' },
  { name: 'Active Campaigns', value: '8', change: '0%', trend: 'neutral' },
  { name: 'Qualified Rate', value: '42%', change: '-2.1%', trend: 'down' },
]

const performanceData = [
  { name: 'Mon', leads: 45, qualified: 20 },
  { name: 'Tue', leads: 52, qualified: 24 },
  { name: 'Wed', leads: 38, qualified: 18 },
  { name: 'Thu', leads: 65, qualified: 32 },
  { name: 'Fri', leads: 48, qualified: 22 },
  { name: 'Sat', leads: 24, qualified: 10 },
  { name: 'Sun', leads: 30, qualified: 12 },
]

const sourceData = [
  { name: 'LinkedIn', value: 450, color: '#0077b5' },
  { name: 'GitHub', value: 320, color: '#333' },
  { name: 'Crunchbase', value: 280, color: '#0284c7' },
  { name: 'Web Scraping', value: 150, color: '#6366f1' },
]

const funnelData = [
  { step: 'Discovered', value: 2845, color: '#6366f1' },
  { step: 'Qualified', value: 1200, color: '#8b5cf6' },
  { step: 'Contacted', value: 850, color: '#ec4899' },
  { step: 'Converted', value: 92, color: '#10b981' },
]

const scoreDistribution = [
  { score: '0-20', count: 150 },
  { score: '21-40', count: 450 },
  { score: '41-60', count: 800 },
  { score: '61-80', count: 1100 },
  { score: '81-100', count: 345 },
]

const activityLogs = [
  { id: 1, agent: 'Discovery Agent', action: 'Found 12 new leads', target: 'LinkedIn', time: '5 mins ago' },
  { id: 2, agent: 'Research Agent', action: 'Enriched profile', target: 'Sarah Johnson', time: '12 mins ago' },
  { id: 3, agent: 'Qualifier Agent', action: 'Lead scored 92 (Hot)', target: 'Michael Chen', time: '1 hour ago' },
  { id: 4, agent: 'Outreach Agent', action: 'Email sent', target: 'Emma Wilson', time: '2 hours ago' },
  { id: 5, agent: 'System', action: 'Backup completed', target: 'Database', time: '5 hours ago' },
]

const outreachPerformance = [
  { name: 'Sent', value: 850, color: '#6366f1' },
  { name: 'Opened', value: 460, color: '#8b5cf6' },
  { name: 'Replied', value: 120, color: '#ec4899' },
  { name: 'Meetings', value: 12, color: '#10b981' },
]

export default function AnalyticsPage() {
  const [dateRange, setDateRange] = useState('Last 7 Days')

  const exportCSV = () => {
    alert('Exporting lead data to CSV...')
  }

  return (
    <div className="space-y-6">
      <div className="sm:flex sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reporting & Analytics</h1>
          <p className="mt-1 text-sm text-gray-500">
            Track lead performance, campaign effectiveness, and agent activity.
          </p>
        </div>
        <div className="mt-4 sm:ml-16 sm:mt-0 flex gap-3">
          <div className="relative inline-block text-left">
             <button className="inline-flex items-center gap-2 rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50">
               <CalendarIcon className="h-4 w-4 text-gray-400" />
               {dateRange}
             </button>
          </div>
          <button
            onClick={exportCSV}
            className="flex items-center gap-2 rounded-md bg-indigo-600 px-3 py-2 text-center text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
          >
            <Download className="h-4 w-4" />
            Export CSV
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((item) => (
          <div key={item.name} className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-gray-500">{item.name}</p>
              {item.trend === 'up' && <ArrowUpRight className="h-4 w-4 text-green-500" />}
              {item.trend === 'down' && <ArrowDownRight className="h-4 w-4 text-red-500" />}
            </div>
            <div className="mt-2 flex items-baseline justify-between">
              <p className="text-2xl font-bold text-gray-900">{item.value}</p>
              <p className={clsx(
                "text-sm font-medium",
                item.trend === 'up' ? "text-green-600" : item.trend === 'down' ? "text-red-600" : "text-gray-600"
              )}>
                {item.change}
              </p>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Outreach Performance */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm lg:col-span-2">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">Outreach Performance</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
            {outreachPerformance.map(metric => (
              <div key={metric.name} className="p-4 rounded-lg bg-gray-50 border border-gray-100">
                <p className="text-xs font-bold text-gray-500 uppercase">{metric.name}</p>
                <p className="text-xl font-bold text-gray-900 mt-1">{metric.value}</p>
                {metric.name !== 'Sent' && (
                  <p className="text-[10px] text-gray-500 mt-1">
                    {Math.round((metric.value / outreachPerformance[0].value) * 100)}% of sent
                  </p>
                )}
              </div>
            ))}
          </div>
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={outreachPerformance}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12 }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12 }} />
                <Tooltip cursor={{ fill: '#f9fafb' }} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]} barSize={40}>
                   {outreachPerformance.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Source Breakdown (Mini) */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm lg:col-span-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">Source Attribution</h3>
          <div className="h-[250px] flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={sourceData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {sourceData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 space-y-2">
            {sourceData.map(source => (
              <div key={source.name} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: source.color }} />
                  <span className="text-xs text-gray-600">{source.name}</span>
                </div>
                <span className="text-xs font-bold text-gray-900">{source.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Conversion Funnel */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm lg:col-span-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">Conversion Funnel</h3>
          <div className="space-y-4">
             {funnelData.map((item, index) => (
               <div key={item.step} className="space-y-1">
                 <div className="flex justify-between text-xs font-medium">
                   <span className="text-gray-500 uppercase">{item.step}</span>
                   <span className="text-gray-900">{item.value}</span>
                 </div>
                 <div className="w-full h-8 bg-gray-100 rounded overflow-hidden relative">
                   <div 
                     className="h-full opacity-80 transition-all duration-1000" 
                     style={{ 
                       width: `${(item.value / funnelData[0].value) * 100}%`,
                       backgroundColor: item.color,
                       marginLeft: index > 0 ? `${((funnelData[0].value - item.value) / funnelData[0].value) * 50}%` : '0'
                     }}
                   />
                   {index > 0 && (
                     <div className="absolute inset-y-0 right-2 flex items-center text-[10px] font-bold text-gray-600">
                        {Math.round((item.value / funnelData[index - 1].value) * 100)}% Conversion
                     </div>
                   )}
                 </div>
               </div>
             ))}
          </div>
        </div>

        {/* Score Distribution */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm lg:col-span-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">Score Distribution</h3>
          <div className="h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scoreDistribution}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
                <XAxis dataKey="score" axisLine={false} tickLine={false} tick={{ fontSize: 10 }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10 }} />
                <Tooltip cursor={{ fill: '#f9fafb' }} />
                <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Agent Activity Logs */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm lg:col-span-1">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Agent Activity</h3>
            <History className="h-5 w-5 text-gray-400" />
          </div>
          <div className="flow-root">
            <ul role="list" className="-mb-8">
              {activityLogs.map((log, logIdx) => (
                <li key={log.id}>
                  <div className="relative pb-8">
                    {logIdx !== activityLogs.length - 1 ? (
                      <span className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200" aria-hidden="true" />
                    ) : null}
                    <div className="relative flex space-x-3">
                      <div>
                        <span className={clsx(
                          "h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white bg-indigo-100"
                        )}>
                          <Zap className="h-4 w-4 text-indigo-600" />
                        </span>
                      </div>
                      <div className="flex min-w-0 flex-1 justify-between space-x-4 pt-1.5">
                        <div>
                          <p className="text-xs font-medium text-gray-900">
                            {log.agent} <span className="font-normal text-gray-500">{log.action}</span>
                          </p>
                          <p className="text-[10px] text-indigo-600 font-semibold truncate max-w-[120px]">
                            {log.target}
                          </p>
                        </div>
                        <div className="whitespace-nowrap text-right text-[10px] text-gray-500">
                          {log.time}
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
  )
}
