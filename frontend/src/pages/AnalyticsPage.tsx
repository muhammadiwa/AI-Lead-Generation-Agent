import { 
  Users, 
  Target, 
  TrendingUp, 
  Zap,
  ArrowUpRight,
  ArrowDownRight
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
  Bar
} from 'recharts'

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
  { name: 'LinkedIn', value: 450 },
  { name: 'GitHub', value: 320 },
  { name: 'Crunchbase', value: 280 },
  { name: 'Web Scraping', value: 150 },
]

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <p className="mt-1 text-sm text-gray-500">
          Track lead performance and campaign effectiveness.
        </p>
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

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Performance Chart */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">Lead Acquisition Trend</h3>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={performanceData}>
                <defs>
                  <linearGradient id="colorLeads" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.1}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#9ca3af' }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#9ca3af' }} />
                <Tooltip 
                  contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                />
                <Area type="monotone" dataKey="leads" stroke="#6366f1" fillOpacity={1} fill="url(#colorLeads)" />
                <Area type="monotone" dataKey="qualified" stroke="#10b981" fillOpacity={0} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Source Breakdown */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">Leads by Source</h3>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sourceData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f3f4f6" />
                <XAxis type="number" axisLine={false} tickLine={false} hide />
                <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#4b5563' }} width={100} />
                <Tooltip 
                   cursor={{ fill: '#f9fafb' }}
                   contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                />
                <Bar dataKey="value" fill="#6366f1" radius={[0, 4, 4, 0]} barSize={24} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  )
}

import { clsx } from 'clsx'
