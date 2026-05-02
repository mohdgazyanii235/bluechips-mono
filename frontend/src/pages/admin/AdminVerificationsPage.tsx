import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AdminLayout } from './AdminLayout'
import { adminApi } from '@/api/admin'
import { Spinner } from '@/components/ui/Spinner'

export function AdminVerificationsPage() {
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    adminApi.getPendingVerifications()
      .then((d) => setItems(d.items))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  if (loading) return <AdminLayout><Spinner fullPage /></AdminLayout>

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div>
          <h1 className="font-serif text-3xl text-ivory-100">Pending Verifications</h1>
          <p className="text-stone-500 text-sm mt-1">{items.length} application{items.length !== 1 ? 's' : ''} awaiting review</p>
        </div>

        {items.length === 0 ? (
          <div className="card-surface p-12 rounded-xl text-center text-stone-500">
            No pending verifications — all caught up!
          </div>
        ) : (
          <div className="space-y-2">
            {items.map((v) => (
              <Link key={v.id} to={`/admin/verifications/${v.id}`}>
                <div className="card-surface-hover p-5 rounded-xl flex items-center justify-between gap-4">
                  <div className="space-y-0.5">
                    <p className="text-ivory-200 font-medium">{v.escort?.stage_name ?? 'Unknown'}</p>
                    <p className="text-stone-500 text-sm">{v.escort?.email}</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className={`text-xs px-2.5 py-1 rounded-full border font-medium ${
                      v.level === 2
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                        : 'bg-blue-500/10 text-blue-400 border-blue-500/30'
                    }`}>
                      {v.level_name}
                    </span>
                    <span className="text-stone-500 text-xs">{v.time_ago}</span>
                    <span className="bg-amber-500/10 text-amber-400 border border-amber-500/30 text-[10px] font-bold px-2 py-0.5 rounded-full">
                      REVIEW
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </AdminLayout>
  )
}
