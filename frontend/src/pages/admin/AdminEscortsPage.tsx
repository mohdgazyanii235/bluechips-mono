import { useEffect, useState } from 'react'
import { AdminLayout } from './AdminLayout'
import { adminApi } from '@/api/admin'
import { Spinner } from '@/components/ui/Spinner'
import { Button } from '@/components/ui/Button'
import { cn } from '@/utils/cn'
import toast from 'react-hot-toast'

const TIER_COLORS: Record<string, string> = {
  free: 'text-stone-500',
  essential: 'text-blue-400',
  premium: 'text-gold-400',
  elite: 'text-gold-400',
}

export function AdminEscortsPage() {
  const [escorts, setEscorts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [toggling, setToggling] = useState<string | null>(null)

  const load = () => {
    adminApi.getEscorts().then(setEscorts).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleToggle = async (id: string, currentlyActive: boolean) => {
    if (!confirm(`${currentlyActive ? 'Deactivate' : 'Activate'} this escort?`)) return
    setToggling(id)
    try {
      await adminApi.toggleEscortActive(id)
      setEscorts((prev) => prev.map((e) => e.id === id ? { ...e, is_active: !e.is_active } : e))
      toast.success(`Escort ${currentlyActive ? 'deactivated' : 'activated'}`)
    } catch {
      toast.error('Action failed')
    } finally {
      setToggling(null)
    }
  }

  if (loading) return <AdminLayout><Spinner fullPage /></AdminLayout>

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div>
          <h1 className="font-serif text-3xl text-ivory-100">Escorts</h1>
          <p className="text-stone-500 text-sm mt-1">{escorts.length} registered</p>
        </div>

        <div className="card-surface rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-border">
                {['Name', 'Email', 'Plan', 'Verified', 'Joined', 'Status', ''].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs uppercase tracking-wider text-stone-600 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border">
              {escorts.map((e) => (
                <tr key={e.id} className={cn('hover:bg-surface/50', !e.is_active && 'opacity-50')}>
                  <td className="px-4 py-3 text-ivory-200 font-medium">{e.stage_name}</td>
                  <td className="px-4 py-3 text-stone-400">{e.email}</td>
                  <td className={cn('px-4 py-3 capitalize font-medium', TIER_COLORS[e.subscription_tier] ?? 'text-stone-400')}>{e.subscription_tier}</td>
                  <td className="px-4 py-3">
                    <span className={cn('text-xs px-2 py-0.5 rounded-full', e.verification_level >= 2 ? 'bg-emerald-500/10 text-emerald-400' : 'text-stone-600')}>
                      Level {e.verification_level}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-stone-500">{new Date(e.created_at).toLocaleDateString('en-GB')}</td>
                  <td className="px-4 py-3">
                    <span className={cn('text-xs font-medium', e.is_active ? 'text-emerald-400' : 'text-red-400')}>
                      {e.is_active ? 'Active' : 'Suspended'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <Button
                      variant="ghost"
                      size="sm"
                      loading={toggling === e.id}
                      onClick={() => handleToggle(e.id, e.is_active)}
                      className={e.is_active ? 'text-red-400 hover:bg-red-900/10' : 'text-emerald-400 hover:bg-emerald-900/10'}
                    >
                      {e.is_active ? 'Suspend' : 'Reinstate'}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AdminLayout>
  )
}
