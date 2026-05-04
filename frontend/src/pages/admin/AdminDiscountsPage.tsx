import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Tag, X, ChevronDown, ChevronUp, Loader2, Check, Ban } from 'lucide-react'
import { AdminLayout } from './AdminLayout'
import { adminApi } from '@/api/admin'

const ALL_TIERS = ['essential', 'premium', 'elite', 'blue_tick']
const TIER_LABELS: Record<string, string> = {
  essential: 'Essential',
  premium: 'Premium',
  elite: 'Elite',
  blue_tick: 'Blue Tick',
}

function TierBadge({ tier }: { tier: string }) {
  const colors: Record<string, string> = {
    essential: 'bg-blue-900/30 text-blue-300 border-blue-700/40',
    premium: 'bg-gold-900/30 text-gold-300 border-gold-700/40',
    elite: 'bg-purple-900/30 text-purple-300 border-purple-700/40',
    blue_tick: 'bg-sky-900/30 text-sky-300 border-sky-700/40',
  }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs border ${colors[tier] ?? 'bg-stone-800 text-stone-400 border-stone-700'}`}>
      {TIER_LABELS[tier] ?? tier}
    </span>
  )
}

const emptyForm = {
  code: '',
  name: '',
  percent_off: 20,
  applicable_tiers: [] as string[],
  duration_months: 3,
  max_redemptions: '' as string | number,
}

export function AdminDiscountsPage() {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ ...emptyForm })
  const [formError, setFormError] = useState('')

  const { data: codes = [], isLoading } = useQuery({
    queryKey: ['admin-discounts'],
    queryFn: adminApi.listDiscountCodes,
  })

  const createMutation = useMutation({
    mutationFn: adminApi.createDiscountCode,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-discounts'] })
      setForm({ ...emptyForm })
      setShowForm(false)
      setFormError('')
    },
    onError: (err: any) => {
      setFormError(err?.response?.data?.detail ?? 'Failed to create code')
    },
  })

  const deactivateMutation = useMutation({
    mutationFn: adminApi.deactivateDiscountCode,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-discounts'] }),
  })

  const toggleTier = (tier: string) => {
    setForm(f => ({
      ...f,
      applicable_tiers: f.applicable_tiers.includes(tier)
        ? f.applicable_tiers.filter(t => t !== tier)
        : [...f.applicable_tiers, tier],
    }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setFormError('')
    const maxR = form.max_redemptions === '' ? null : Number(form.max_redemptions)
    createMutation.mutate({
      code: form.code.toUpperCase().trim(),
      name: form.name.trim(),
      percent_off: Number(form.percent_off),
      applicable_tiers: form.applicable_tiers,
      duration_months: Number(form.duration_months),
      max_redemptions: maxR,
    })
  }

  return (
    <AdminLayout>
      <div className="max-w-4xl space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-serif text-2xl text-ivory-100">Discount Codes</h1>
            <p className="text-stone-500 text-sm mt-1">Create and manage promotional codes for escorts</p>
          </div>
          <button
            onClick={() => setShowForm(v => !v)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gold-400 text-black font-semibold text-sm hover:bg-gold-300 transition-colors"
          >
            {showForm ? <><X className="w-4 h-4" /> Cancel</> : <><Plus className="w-4 h-4" /> New Code</>}
          </button>
        </div>

        {/* Create form */}
        {showForm && (
          <form onSubmit={handleSubmit} className="bg-stone-900 border border-surface-border rounded-xl p-6 space-y-5">
            <h2 className="font-serif text-lg text-ivory-100">Create Discount Code</h2>

            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-stone-400 mb-1.5">Code <span className="text-red-400">*</span></label>
                <input
                  required
                  value={form.code}
                  onChange={e => setForm(f => ({ ...f, code: e.target.value.toUpperCase() }))}
                  placeholder="e.g. SUMMER25"
                  className="w-full bg-surface border border-surface-border rounded-lg px-3 py-2 text-ivory-100 text-sm font-mono placeholder-stone-600 focus:outline-none focus:border-gold-400/60"
                />
              </div>
              <div>
                <label className="block text-xs text-stone-400 mb-1.5">Name / Description <span className="text-red-400">*</span></label>
                <input
                  required
                  value={form.name}
                  onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                  placeholder="e.g. Summer promotion"
                  className="w-full bg-surface border border-surface-border rounded-lg px-3 py-2 text-ivory-100 text-sm placeholder-stone-600 focus:outline-none focus:border-gold-400/60"
                />
              </div>
            </div>

            <div className="grid sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs text-stone-400 mb-1.5">Discount % <span className="text-red-400">*</span></label>
                <input
                  required
                  type="number"
                  min={1}
                  max={100}
                  value={form.percent_off}
                  onChange={e => setForm(f => ({ ...f, percent_off: Number(e.target.value) }))}
                  className="w-full bg-surface border border-surface-border rounded-lg px-3 py-2 text-ivory-100 text-sm focus:outline-none focus:border-gold-400/60"
                />
              </div>
              <div>
                <label className="block text-xs text-stone-400 mb-1.5">Duration (months) <span className="text-red-400">*</span></label>
                <input
                  required
                  type="number"
                  min={1}
                  max={24}
                  value={form.duration_months}
                  onChange={e => setForm(f => ({ ...f, duration_months: Number(e.target.value) }))}
                  className="w-full bg-surface border border-surface-border rounded-lg px-3 py-2 text-ivory-100 text-sm focus:outline-none focus:border-gold-400/60"
                />
              </div>
              <div>
                <label className="block text-xs text-stone-400 mb-1.5">Max uses <span className="text-stone-600">(blank = unlimited)</span></label>
                <input
                  type="number"
                  min={1}
                  value={form.max_redemptions}
                  onChange={e => setForm(f => ({ ...f, max_redemptions: e.target.value }))}
                  placeholder="Unlimited"
                  className="w-full bg-surface border border-surface-border rounded-lg px-3 py-2 text-ivory-100 text-sm placeholder-stone-600 focus:outline-none focus:border-gold-400/60"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs text-stone-400 mb-2">Applicable tiers <span className="text-stone-600">(select none = all tiers)</span></label>
              <div className="flex flex-wrap gap-2">
                {ALL_TIERS.map(tier => (
                  <button
                    key={tier}
                    type="button"
                    onClick={() => toggleTier(tier)}
                    className={`px-3 py-1.5 rounded-lg text-sm border transition-colors ${
                      form.applicable_tiers.includes(tier)
                        ? 'bg-gold-400/20 border-gold-400/60 text-gold-300'
                        : 'bg-surface border-surface-border text-stone-400 hover:border-stone-600'
                    }`}
                  >
                    {TIER_LABELS[tier]}
                  </button>
                ))}
              </div>
              {form.applicable_tiers.length === 0 && (
                <p className="text-stone-600 text-xs mt-1.5">No tiers selected — code will work for all tiers</p>
              )}
            </div>

            {formError && <p className="text-red-400 text-sm">{formError}</p>}

            <button
              type="submit"
              disabled={createMutation.isPending}
              className="flex items-center gap-2 px-5 py-2 rounded-lg bg-gold-400 text-black font-semibold text-sm hover:bg-gold-300 transition-colors disabled:opacity-60"
            >
              {createMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Tag className="w-4 h-4" />}
              Create Code
            </button>
          </form>
        )}

        {/* Codes list */}
        {isLoading ? (
          <div className="flex items-center justify-center py-16 text-stone-500">
            <Loader2 className="w-6 h-6 animate-spin mr-3" /> Loading codes…
          </div>
        ) : codes.length === 0 ? (
          <div className="text-center py-16 text-stone-500">
            <Tag className="w-10 h-10 mx-auto mb-3 opacity-30" />
            <p>No discount codes yet</p>
          </div>
        ) : (
          <div className="space-y-3">
            {codes.map(c => (
              <div
                key={c.id}
                className={`bg-stone-900 border rounded-xl p-5 flex items-start gap-4 ${c.is_active ? 'border-surface-border' : 'border-stone-800 opacity-60'}`}
              >
                <div className="flex-1 min-w-0 space-y-2">
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className="font-mono font-bold text-ivory-100 tracking-wider">{c.code}</span>
                    {!c.is_active && <span className="text-xs text-red-400 border border-red-800/40 bg-red-900/20 px-2 py-0.5 rounded">Deactivated</span>}
                    <span className="text-xs text-stone-400">{c.name}</span>
                  </div>
                  <div className="flex items-center gap-3 flex-wrap text-xs text-stone-500">
                    <span className="text-gold-400 font-semibold">{c.percent_off}% off</span>
                    <span>for {c.duration_months} month{c.duration_months !== 1 ? 's' : ''}</span>
                    <span>·</span>
                    <span>{c.current_redemptions}{c.max_redemptions != null ? ` / ${c.max_redemptions}` : ''} uses</span>
                    {c.applicable_tiers.length > 0 && (
                      <>
                        <span>·</span>
                        <div className="flex gap-1 flex-wrap">
                          {c.applicable_tiers.map(t => <TierBadge key={t} tier={t} />)}
                        </div>
                      </>
                    )}
                    {c.applicable_tiers.length === 0 && <span>· all tiers</span>}
                  </div>
                </div>
                {c.is_active && (
                  <button
                    onClick={() => deactivateMutation.mutate(c.id)}
                    disabled={deactivateMutation.isPending}
                    title="Deactivate"
                    className="shrink-0 p-2 rounded-lg border border-stone-800 text-stone-500 hover:border-red-800/60 hover:text-red-400 hover:bg-red-900/10 transition-colors"
                  >
                    <Ban className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </AdminLayout>
  )
}
