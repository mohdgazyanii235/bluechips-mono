import React, { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Loader2, Save, PoundSterling, AlertTriangle, CheckCircle } from 'lucide-react'
import { AdminLayout } from './AdminLayout'
import { adminApi } from '@/api/admin'

interface PriceField {
  key: string
  label: string
  stripeKey: string
  hint?: string
}

const PRICE_GROUPS: { title: string; fields: PriceField[] }[] = [
  {
    title: 'Essential',
    fields: [
      { key: 'essential_monthly_pence', label: 'Monthly', stripeKey: 'stripe_essential_monthly_id' },
      { key: 'essential_annual_pence', label: 'Annual', stripeKey: 'stripe_essential_annual_id', hint: 'Tip: set to 10× monthly for 2 months free' },
    ],
  },
  {
    title: 'Premium',
    fields: [
      { key: 'premium_monthly_pence', label: 'Monthly', stripeKey: 'stripe_premium_monthly_id' },
      { key: 'premium_annual_pence', label: 'Annual', stripeKey: 'stripe_premium_annual_id', hint: 'Tip: set to 10× monthly for 2 months free' },
    ],
  },
  {
    title: 'Elite',
    fields: [
      { key: 'elite_monthly_pence', label: 'Monthly', stripeKey: 'stripe_elite_monthly_id' },
      { key: 'elite_annual_pence', label: 'Annual', stripeKey: 'stripe_elite_annual_id', hint: 'Tip: set to 10× monthly for 2 months free' },
    ],
  },
  {
    title: 'Blue Tick',
    fields: [
      { key: 'blue_tick_setup_pence', label: 'One-time setup fee', stripeKey: 'stripe_blue_tick_setup_id' },
      { key: 'blue_tick_monthly_pence', label: 'Monthly recurring', stripeKey: 'stripe_blue_tick_monthly_id' },
    ],
  },
]

function penceToPounds(pence: number): string {
  return (pence / 100).toFixed(2)
}

function poundsToPence(pounds: string): number {
  return Math.round(parseFloat(pounds) * 100)
}

export function AdminPricingPage() {
  const queryClient = useQueryClient()
  const { data: pricing, isLoading } = useQuery({
    queryKey: ['admin-pricing'],
    queryFn: adminApi.getPricing,
  })

  const [form, setForm] = useState<Record<string, string>>({})
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (!pricing) return
    const initial: Record<string, string> = {}
    for (const group of PRICE_GROUPS) {
      for (const field of group.fields) {
        initial[field.key] = penceToPounds((pricing as any)[field.key])
      }
    }
    setForm(initial)
  }, [pricing])

  const saveMutation = useMutation({
    mutationFn: () => {
      const payload: Record<string, number> = {}
      for (const group of PRICE_GROUPS) {
        for (const field of group.fields) {
          const val = parseFloat(form[field.key])
          if (!isNaN(val) && val > 0) {
            payload[field.key] = poundsToPence(form[field.key])
          }
        }
      }
      return adminApi.updatePricing(payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-pricing'] })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    },
  })

  const handleChange = (key: string, value: string) => {
    setForm(f => ({ ...f, [key]: value }))
    setSaved(false)
  }

  const hasChanges = pricing && PRICE_GROUPS.some(g =>
    g.fields.some(f => {
      const current = penceToPounds((pricing as any)[f.key])
      return form[f.key] !== undefined && form[f.key] !== current
    })
  )

  if (isLoading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center py-24 text-stone-500">
          <Loader2 className="w-6 h-6 animate-spin mr-3" /> Loading pricing…
        </div>
      </AdminLayout>
    )
  }

  return (
    <AdminLayout>
      <div className="max-w-3xl space-y-8">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="font-serif text-2xl text-ivory-100">Pricing</h1>
            <p className="text-stone-500 text-sm mt-1">
              Click any price field, type a new amount, then click <strong className="text-ivory-300">Save Changes</strong>.
            </p>
            {pricing?.updated_at && (
              <p className="text-stone-600 text-xs mt-1">
                Last updated {new Date(pricing.updated_at).toLocaleString('en-GB')} by {pricing.updated_by}
              </p>
            )}
          </div>
          <button
            onClick={() => saveMutation.mutate()}
            disabled={saveMutation.isPending || !hasChanges}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-gold-400 text-black font-semibold text-sm hover:bg-gold-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saveMutation.isPending
              ? <><Loader2 className="w-4 h-4 animate-spin" /> Saving…</>
              : saved
              ? <><CheckCircle className="w-4 h-4" /> Saved!</>
              : <><Save className="w-4 h-4" /> Save Changes</>}
          </button>
        </div>

        {saveMutation.isError && (
          <div className="flex items-start gap-3 p-4 rounded-xl bg-red-900/20 border border-red-800/40 text-red-400">
            <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-sm">Save failed</p>
              <p className="text-red-600 text-xs mt-0.5">
                {(saveMutation.error as any)?.response?.data?.detail ?? 'An error occurred. Check that Stripe is configured.'}
              </p>
            </div>
          </div>
        )}

        <div className="p-4 rounded-xl bg-amber-900/15 border border-amber-800/30 flex items-start gap-3">
          <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
          <p className="text-amber-600 text-xs">
            Saving creates <strong>new Stripe Price objects</strong> for any changed amounts and archives the old ones. This cannot be undone. Existing active subscriptions are not affected — they continue at their original price until cancelled or changed.
          </p>
        </div>

        {PRICE_GROUPS.map(group => (
          <div key={group.title} className="bg-stone-900 border border-surface-border rounded-xl overflow-hidden">
            <div className="px-5 py-3 border-b border-surface-border bg-stone-950/50">
              <h2 className="font-serif text-lg text-ivory-100">{group.title}</h2>
            </div>
            <div className="divide-y divide-surface-border">
              {group.fields.map(field => {
                const currentPence = pricing ? (pricing as any)[field.key] : 0
                const inputVal = form[field.key] ?? ''
                const inputPence = poundsToPence(inputVal)
                const changed = inputPence !== currentPence && !isNaN(inputPence)
                const stripeId = pricing ? (pricing as any)[field.stripeKey] : ''

                return (
                  <div key={field.key} className="p-5 flex items-start gap-4">
                    <div className="flex-1 space-y-1.5">
                      <label className="block text-sm font-medium text-ivory-200">{field.label}</label>
                      {field.hint && <p className="text-stone-600 text-xs">{field.hint}</p>}
                      {stripeId && (
                        <p className="text-stone-700 text-[11px] font-mono truncate" title={stripeId}>
                          Stripe: {stripeId}
                        </p>
                      )}
                    </div>

                    <div className="shrink-0 flex items-center gap-2">
                      <div className={`flex items-center rounded-lg border overflow-hidden transition-colors hover:border-gold-400/40 ${changed ? 'border-gold-400/60 bg-gold-400/5' : 'border-surface-border'}`}>
                        <span className="pl-3 pr-1 text-stone-500 text-sm">
                          <PoundSterling className="w-3.5 h-3.5" />
                        </span>
                        <input
                          type="number"
                          min="0.01"
                          step="0.01"
                          value={inputVal}
                          onChange={e => handleChange(field.key, e.target.value)}
                          className="bg-transparent text-ivory-100 text-sm px-2 py-2.5 w-24 focus:outline-none cursor-text"
                        />
                      </div>
                      {changed && (
                        <span className="text-gold-400 text-xs font-medium whitespace-nowrap">
                          was £{penceToPounds(currentPence)}
                        </span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        ))}

        <div className="flex justify-end">
          <button
            onClick={() => saveMutation.mutate()}
            disabled={saveMutation.isPending || !hasChanges}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-gold-400 text-black font-semibold text-sm hover:bg-gold-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saveMutation.isPending
              ? <><Loader2 className="w-4 h-4 animate-spin" /> Saving…</>
              : saved
              ? <><CheckCircle className="w-4 h-4" /> Saved!</>
              : <><Save className="w-4 h-4" /> Save Changes</>}
          </button>
        </div>
      </div>
    </AdminLayout>
  )
}
