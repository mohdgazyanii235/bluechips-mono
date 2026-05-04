import { Link, useLocation, useNavigate } from 'react-router-dom'
import { ClipboardList, Users, LogOut, LayoutDashboard, Tag, PoundSterling } from 'lucide-react'
import { useAdminStore } from '@/store/adminStore'
import { cn } from '@/utils/cn'

const NAV = [
  { label: 'Dashboard', href: '/admin', icon: LayoutDashboard, exact: true },
  { label: 'Verifications', href: '/admin/verifications', icon: ClipboardList },
  { label: 'Escorts', href: '/admin/escorts', icon: Users },
  { label: 'Discounts', href: '/admin/discounts', icon: Tag },
  { label: 'Pricing', href: '/admin/pricing', icon: PoundSterling },
]

export function AdminLayout({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const { logout, email } = useAdminStore()

  const handleLogout = () => {
    logout()
    navigate('/admin/login')
  }

  return (
    <div className="min-h-screen bg-black flex">
      {/* Sidebar */}
      <aside className="w-56 shrink-0 border-r border-surface-border flex flex-col">
        <div className="p-6 border-b border-surface-border">
          <p className="font-serif text-lg gold-text">BLUECHIPS</p>
          <p className="text-stone-600 text-[10px] uppercase tracking-widest mt-0.5">Admin</p>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {NAV.map(({ label, href, icon: Icon, exact }) => {
            const active = exact ? pathname === href : pathname.startsWith(href)
            return (
              <Link
                key={href}
                to={href}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors',
                  active
                    ? 'bg-gold-400/10 text-gold-400 border border-gold-400/20'
                    : 'text-stone-400 hover:text-ivory-200 hover:bg-surface'
                )}
              >
                <Icon className="w-4 h-4" />
                {label}
              </Link>
            )
          })}
        </nav>

        <div className="p-3 border-t border-surface-border">
          <p className="text-stone-600 text-xs px-3 mb-2 truncate">{email}</p>
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-stone-500 hover:text-red-400 hover:bg-red-900/10 transition-colors w-full"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto p-8">{children}</main>
    </div>
  )
}
