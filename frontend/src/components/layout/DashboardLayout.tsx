import { Outlet, Link, useLocation } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Users, 
  Trello, 
  Settings, 
  Database, 
  BarChart3,
  Menu,
  X
} from 'lucide-react'
import { useState } from 'react'
import { clsx } from 'clsx'

const navigation = [
  { name: 'Leads', href: '/leads', icon: Users },
  { name: 'Pipeline', href: '/pipeline', icon: Trello },
  { name: 'Sources', href: '/sources', icon: Database },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
]

export default function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const location = useLocation()

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Mobile sidebar */}
      <div className={clsx(
        "fixed inset-0 z-50 flex md:hidden",
        !sidebarOpen && "pointer-events-none"
      )}>
        <div className={clsx(
          "fixed inset-0 bg-gray-600/80 transition-opacity duration-300 ease-linear",
          sidebarOpen ? "opacity-100" : "opacity-0"
        )} onClick={() => setSidebarOpen(false)} />

        <div className={clsx(
          "relative flex w-full max-w-xs flex-1 flex-col bg-white transition duration-300 ease-in-out transform",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}>
          <div className="absolute top-0 right-0 -mr-12 pt-2">
            <button
              type="button"
              className="ml-1 flex h-10 w-10 items-center justify-center rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-6 w-6 text-white" aria-hidden="true" />
            </button>
          </div>

          <div className="flex flex-shrink-0 items-center px-4 py-6 border-b">
            <span className="text-xl font-bold text-indigo-600">Ship Studio AI</span>
          </div>
          <div className="mt-5 h-0 flex-1 overflow-y-auto">
            <nav className="space-y-1 px-2">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  className={clsx(
                    item.href === location.pathname
                      ? 'bg-indigo-50 text-indigo-600'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900',
                    'group flex items-center rounded-md px-2 py-2 text-base font-medium'
                  )}
                  onClick={() => setSidebarOpen(false)}
                >
                  <item.icon
                    className={clsx(
                      item.href === location.pathname ? 'text-indigo-600' : 'text-gray-400 group-hover:text-gray-500',
                      'mr-4 h-6 w-6 flex-shrink-0'
                    )}
                    aria-hidden="true"
                  />
                  {item.name}
                </Link>
              ))}
            </nav>
          </div>
        </div>
      </div>

      {/* Static sidebar for desktop */}
      <div className="hidden md:fixed md:inset-y-0 md:flex md:w-64 md:flex-col">
        <div className="flex min-h-0 flex-1 flex-col border-r border-gray-200 bg-white">
          <div className="flex flex-shrink-0 items-center px-4 py-6 border-b">
            <span className="text-xl font-bold text-indigo-600">Ship Studio AI</span>
          </div>
          <div className="flex flex-1 flex-col overflow-y-auto">
            <nav className="flex-1 space-y-1 bg-white px-2 py-4">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  className={clsx(
                    item.href === location.pathname
                      ? 'bg-indigo-50 text-indigo-600'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900',
                    'group flex items-center rounded-md px-2 py-2 text-sm font-medium'
                  )}
                >
                  <item.icon
                    className={clsx(
                      item.href === location.pathname ? 'text-indigo-600' : 'text-gray-400 group-hover:text-gray-500',
                      'mr-3 h-5 w-5 flex-shrink-0'
                    )}
                    aria-hidden="true"
                  />
                  {item.name}
                </Link>
              ))}
            </nav>
          </div>
          <div className="flex flex-shrink-0 border-t border-gray-200 p-4">
            <Link to="/settings" className="group block w-full flex-shrink-0">
              <div className="flex items-center">
                <div>
                  <div className="inline-block h-9 w-9 overflow-hidden rounded-full bg-gray-100">
                    <Users className="h-full w-full text-gray-300" />
                  </div>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-700 group-hover:text-gray-900">Admin User</p>
                  <p className="text-xs font-medium text-gray-500 group-hover:text-gray-700">Settings</p>
                </div>
                <Settings className="ml-auto h-5 w-5 text-gray-400 group-hover:text-gray-500" />
              </div>
            </Link>
          </div>
        </div>
      </div>

      <div className="flex flex-1 flex-col md:pl-64">
        <div className="sticky top-0 z-10 flex h-16 flex-shrink-0 bg-white shadow md:hidden">
          <button
            type="button"
            className="border-r border-gray-200 px-4 text-gray-500 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500 md:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <span className="sr-only">Open sidebar</span>
            <Menu className="h-6 w-6" aria-hidden="true" />
          </button>
          <div className="flex flex-1 justify-between px-4">
            <div className="flex flex-1 items-center">
               <span className="text-lg font-semibold text-gray-900 md:hidden">Ship Studio AI</span>
            </div>
          </div>
        </div>

        <main className="flex-1 overflow-y-auto">
          <div className="py-6">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 md:px-8">
              <Outlet />
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
