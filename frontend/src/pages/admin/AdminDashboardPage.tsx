import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AdminLayout } from './AdminLayout'
import { adminApi } from '@/api/admin'
import { Spinner } from '@/components/ui/Spinner'
import { Button } from '@/components/ui/Button'
import { cn } from '@/utils/cn'

export function AdminDashboardPage() {
  const [stats, setStats] = useState<{ total_escorts: number; pending_verifications: number; paid_escorts: number } | null>(null)
  const [pending, setPending] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([adminApi.getStats(), adminApi.getPendingVerifications()])
      .then(([s, p]) => { setStats(s); setPending(p.items) })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <AdminLayout><Spinner fullPage /></AdminLayout>

  return (
    <AdminLayout>
      <div className="space-y-8">
        <div>
          <h1 className="font-serif text-3xl text-ivory-100">Admin Dashboard</h1>
          <p className="text-stone-500 text-sm mt-1">Overview of platform activity</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: 'Total Escorts', value: stats?.total_escorts ?? 0 },
            { label: 'Paid Escorts', value: stats?.paid_escorts ?? 0 },
            { label: 'Pending Verifications', value: stats?.pending_verifications ?? 0, urgent: (stats?.pending_verifications ?? 0) > 0 },
          ].map(({ label, value, urgent }) => (
            <div key={label} className={cn('card-surface p-5 rounded-xl', urgent && 'border-amber-500/30 bg-amber-900/10')}>
              <p className={cn('font-serif text-3xl', urgent ? 'text-amber-400' : 'text-gold-400')}>{value}</p>
              <p className="text-stone-500 text-sm mt-1">{label}</p>
            </div>
          ))}
        </div>

        {/* Pending verifications queue */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-serif text-xl text-ivory-100">Pending Verifications</h2>
            <Link to="/admin/verifications">
              <Button variant="outline-gold" size="sm">View All</Button>
            </Link>
          </div>

          {pending.length === 0 ? (
            <div className="card-surface p-8 rounded-xl text-center text-stone-500 text-sm">
              No pending verifications — you're all caught up.
            </div>
          ) : (
            <div className="space-y-2">
              {pending.slice(0, 5).map((v) => (
                <Link key={v.id} to={`/admin/verifications/${v.id}`}>
                  <div className="card-surface-hover p-4 rounded-xl flex items-center justify-between gap-4">
                    <div>
                      <p className="text-ivory-200 text-sm font-medium">{v.escort?.stage_name ?? 'Unknown'}</p>
                      <p className="text-stone-500 text-xs">{v.escort?.email} · {v.level_name}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-stone-500 text-xs">{v.time_ago}</span>
                      <span className="bg-amber-500/10 text-amber-400 border border-amber-500/30 text-[10px] font-bold px-2 py-0.5 rounded-full">
                        PENDING
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </AdminLayout>
  )
}
