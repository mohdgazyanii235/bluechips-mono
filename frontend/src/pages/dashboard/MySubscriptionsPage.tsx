import { useState } from 'react'
import { Helmet } from 'react-helmet-async'
import { Link } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ChevronLeft, CreditCard, FileText, ExternalLink, AlertTriangle,
  CheckCircle, XCircle, Clock, Zap, Star, Crown, CheckCheck,
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { DashboardLayout } from '@/components/layout/Layout'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import { useMyProfile } from '@/hooks/useEscorts'
import { paymentsApi } from '@/api/payments'
import { cn } from '@/utils/cn'
import toast from 'react-hot-toast'

// ─── Cancellation reasons ────────────────────────────────────────────────────
const CANCEL_REASONS = [
  'Too expensive for my budget',
  'Not getting enough enquiries or bookings',
  'Switching to a different platform',
  'Taking a break from the industry',
  'Technical issues with the platform',
  'Other reason',
]

const TIER_FEATURES: Record<string, string[]> = {
  essential: ['Contact buttons (phone & WhatsApp)', 'Up to 8 photos', 'Borough search listing', '"Available now" indicator'],
  premium: ['Featured search placement', 'Up to 50 photos', 'STD tested badge', 'Analytics dashboard'],
  elite: ['Homepage rotation', 'Top search placement', 'Elite badge', 'Priority support'],
}

const TIER_ICONS: Record<string, any> = { essential: Zap, premium: Star, elite: Crown }

// ─── Cancellation modal ───────────────────────────────────────────────────────
type CancelTarget = 'main' | 'blue_tick'

interface CancelModalProps {
  target: CancelTarget
  tier: string
  onClose: () => void
  onConfirm: () => Promise<void>
}

function CancelModal({ target, tier, onClose, onConfirm }: CancelModalProps) {
  const [step, setStep] = useState(1)
  const [reason, setReason] = useState('')
  const [feedback, setFeedback] = useState('')
  const [confirmText, setConfirmText] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const label = target === 'blue_tick' ? 'Blue Tick' : `${tier.charAt(0).toUpperCase()}${tier.slice(1)} Plan`
  const lostFeatures = target === 'blue_tick'
    ? ['Blue tick badge on your profile', 'Appearance in "Blue Tick verified" filter', 'Verified trust signal to clients']
    : (TIER_FEATURES[tier] ?? [])

  const canProceedStep1 = reason !== ''
  const canProceedStep2 = feedback.trim().length >= 20
  const canSubmit = confirmText.trim().toUpperCase() === 'CANCEL'

  const handleSubmit = async () => {
    setSubmitting(true)
    try {
      await onConfirm()
      onClose()
    } catch {
      toast.error('Could not process cancellation. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
      onClick={(e) => {
        // Only allow backdrop-dismiss on step 1 — prevent losing progress mid-flow
        if (e.target === e.currentTarget && step === 1) onClose()
      }}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 16 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 8 }}
        className="w-full max-w-lg card-surface rounded-2xl p-8 space-y-6 shadow-card"
      >
        {/* Progress */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs text-stone-500">
            <span>Step {step} of 4</span>
            <button onClick={onClose} className="text-stone-600 hover:text-stone-400 transition-colors text-xs">
              Keep my subscription
            </button>
          </div>
          <div className="flex gap-1">
            {[1, 2, 3, 4].map((s) => (
              <div key={s} className={cn('h-1 flex-1 rounded-full transition-all', s <= step ? 'bg-red-500' : 'bg-surface-border')} />
            ))}
          </div>
        </div>

        <AnimatePresence mode="wait">
          {/* Step 1: Why are you leaving? */}
          {step === 1 && (
            <motion.div key="step1" initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -16 }} className="space-y-5">
              <div>
                <h2 className="font-serif text-xl text-ivory-100">Why are you cancelling your {label}?</h2>
                <p className="text-stone-500 text-sm mt-1">Help us understand — it takes less than a minute.</p>
              </div>
              <div className="space-y-2">
                {CANCEL_REASONS.map((r) => (
                  <button
                    key={r}
                    onClick={() => setReason(r)}
                    className={cn(
                      'w-full text-left px-4 py-3 rounded-xl border text-sm transition-all',
                      reason === r
                        ? 'border-red-500/50 bg-red-500/10 text-red-300'
                        : 'border-surface-border bg-surface text-stone-400 hover:border-stone-600 hover:text-stone-300'
                    )}
                  >
                    {r}
                  </button>
                ))}
              </div>
              <Button variant="gold" fullWidth disabled={!canProceedStep1} onClick={() => setStep(2)}>
                Continue →
              </Button>
            </motion.div>
          )}

          {/* Step 2: Feedback */}
          {step === 2 && (
            <motion.div key="step2" initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -16 }} className="space-y-5">
              <div>
                <h2 className="font-serif text-xl text-ivory-100">What could we do better?</h2>
                <p className="text-stone-500 text-sm mt-1">Your honest feedback helps us improve for other companions.</p>
              </div>
              <textarea
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="Tell us what wasn't working, what you wish we had, or any other thoughts..."
                rows={5}
                className="w-full rounded-xl bg-surface border border-surface-border text-ivory-200 placeholder-stone-600 px-4 py-3 text-sm resize-none focus:outline-none focus:border-gold-400/50 transition-colors"
              />
              <p className={cn('text-xs', feedback.trim().length >= 20 ? 'text-emerald-500' : 'text-stone-600')}>
                {feedback.trim().length}/20 characters minimum
              </p>
              <div className="flex gap-3">
                <Button variant="ghost" fullWidth onClick={() => setStep(1)}>← Back</Button>
                <Button variant="gold" fullWidth disabled={!canProceedStep2} onClick={() => setStep(3)}>
                  Continue →
                </Button>
              </div>
            </motion.div>
          )}

          {/* Step 3: What you'll lose */}
          {step === 3 && (
            <motion.div key="step3" initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -16 }} className="space-y-5">
              <div>
                <h2 className="font-serif text-xl text-ivory-100">You will lose access to:</h2>
                <p className="text-stone-500 text-sm mt-1">These features will be removed when your billing period ends.</p>
              </div>
              <ul className="space-y-3">
                {lostFeatures.map((f) => (
                  <li key={f} className="flex items-start gap-3 p-3 rounded-lg bg-red-900/10 border border-red-800/20">
                    <XCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
                    <span className="text-stone-300 text-sm">{f}</span>
                  </li>
                ))}
              </ul>
              <div className="p-4 rounded-xl bg-amber-900/15 border border-amber-800/30">
                <p className="text-amber-400 text-sm font-medium flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  You will keep access until the end of your current billing period.
                </p>
              </div>
              <div className="flex gap-3">
                <Button variant="ghost" fullWidth onClick={() => setStep(2)}>← Back</Button>
                <Button variant="outline-gold" fullWidth onClick={() => setStep(4)}>
                  I understand, continue
                </Button>
              </div>
            </motion.div>
          )}

          {/* Step 4: Type CANCEL to confirm */}
          {step === 4 && (
            <motion.div key="step4" initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -16 }} className="space-y-5">
              <div>
                <h2 className="font-serif text-xl text-ivory-100">Final confirmation</h2>
                <p className="text-stone-500 text-sm mt-1">
                  Type <span className="text-red-400 font-mono font-bold">CANCEL</span> below to confirm you want to cancel your {label}.
                </p>
              </div>
              <input
                type="text"
                value={confirmText}
                onChange={(e) => setConfirmText(e.target.value)}
                placeholder="Type CANCEL here"
                className="w-full rounded-xl bg-surface border border-surface-border text-ivory-200 placeholder-stone-600 px-4 py-3 text-sm font-mono focus:outline-none focus:border-red-500/50 transition-colors"
              />
              <div className="flex gap-3">
                <Button variant="ghost" fullWidth onClick={() => setStep(3)}>← Back</Button>
                <Button
                  variant="ghost"
                  fullWidth
                  disabled={!canSubmit || submitting}
                  loading={submitting}
                  onClick={handleSubmit}
                  className="!border-red-500/40 !text-red-400 hover:!bg-red-500/10 disabled:opacity-40"
                >
                  Cancel Subscription
                </Button>
              </div>
              <button onClick={onClose} className="w-full text-center text-stone-500 hover:text-stone-300 text-xs transition-colors py-1">
                Changed my mind — keep my subscription
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </motion.div>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────
function statusIcon(status: string | null) {
  if (status === 'active') return <CheckCircle className="w-4 h-4 text-emerald-400" />
  if (status === 'cancelling') return <Clock className="w-4 h-4 text-amber-400" />
  return <XCircle className="w-4 h-4 text-red-400" />
}

function statusLabel(status: string | null) {
  if (status === 'active') return 'Active'
  if (status === 'cancelling') return 'Cancels at period end'
  return 'Inactive'
}

export function MySubscriptionsPage() {
  const qc = useQueryClient()
  const { data: escort, isLoading: profileLoading } = useMyProfile()
  const [cancelModal, setCancelModal] = useState<CancelTarget | null>(null)

  const { data: subData } = useQuery({
    queryKey: ['subscription'],
    queryFn: paymentsApi.getSubscription,
    enabled: !!escort,
  })

  const { data: invoiceData, isLoading: invoicesLoading } = useQuery({
    queryKey: ['invoices'],
    queryFn: paymentsApi.getInvoices,
    enabled: !!escort,
  })

  if (profileLoading) return <DashboardLayout><Spinner fullPage /></DashboardLayout>
  if (!escort) return null

  const currentTier = escort.subscription_tier
  const isPaid = currentTier !== 'free'
  const isPremiumOrElite = currentTier === 'premium' || currentTier === 'elite'
  const hasBlueTick = !!(escort.blue_tick_stripe_subscription_id)
  const TierIcon = TIER_ICONS[currentTier] ?? Zap

  const invalidateAll = () => {
    qc.invalidateQueries({ queryKey: ['my-profile'] })
    qc.invalidateQueries({ queryKey: ['subscription'] })
    qc.invalidateQueries({ queryKey: ['invoices'] })
  }

  const handleCancelMain = async () => {
    await paymentsApi.cancelSubscription()
    toast.success('Subscription will cancel at the end of your billing period. You keep access until then.')
    invalidateAll()
  }

  const handleCancelBlueTick = async () => {
    await paymentsApi.cancelBlueTick()
    toast.success('Blue Tick will cancel at the end of your billing period.')
    invalidateAll()
  }

  const handleReactivateMain = async () => {
    // Verotel does not support programmatic reactivation. The user has to
    // start a fresh subscription via checkout.
    toast(
      'To reactivate, please start a new subscription from the Subscription page.',
      { duration: 6000 },
    )
  }

  const handleReactivateBlueTick = async () => {
    toast(
      'To reactivate Blue Tick, please apply for it again from the Verification page.',
      { duration: 6000 },
    )
  }

  const invoices: any[] = invoiceData?.invoices ?? []

  return (
    <DashboardLayout>
      <Helmet><title>My Subscriptions — Bluechips London</title></Helmet>

      <div className="page-container py-10 space-y-10">
        {/* Header */}
        <div className="flex items-center gap-3">
          <Link to="/dashboard" className="text-stone-500 hover:text-gold-400 transition-colors">
            <ChevronLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="font-serif text-3xl text-ivory-100">My Subscriptions</h1>
            <p className="text-stone-500 text-sm mt-0.5">Manage your active plans and view billing history.</p>
          </div>
        </div>

        {/* Active subscriptions */}
        <section className="space-y-4">
          <h2 className="font-serif text-xl text-ivory-100">Active Plans</h2>

          {!isPaid && !hasBlueTick ? (
            <div className="card-surface rounded-2xl p-8 text-center space-y-4">
              <CreditCard className="w-10 h-10 text-stone-600 mx-auto" />
              <div>
                <p className="text-ivory-300 font-medium">No active subscriptions</p>
                <p className="text-stone-500 text-sm mt-1">You're on the free plan. Upgrade to unlock more features.</p>
              </div>
              <Link to="/dashboard/subscription">
                <Button variant="gold">View Plans →</Button>
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Main subscription */}
              {isPaid && (
                <div className="card-surface rounded-2xl p-6 space-y-4">
                  <div className="flex items-start justify-between gap-4 flex-wrap">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-gold-400/10 border border-gold-400/20 flex items-center justify-center">
                        <TierIcon className="w-5 h-5 text-gold-400" />
                      </div>
                      <div>
                        <p className="text-ivory-100 font-medium capitalize">{currentTier} Plan</p>
                        <div className="flex items-center gap-1.5 mt-0.5">
                          {statusIcon(subData?.status ?? null)}
                          <span className="text-stone-400 text-xs">{statusLabel(subData?.status ?? null)}</span>
                        </div>
                      </div>
                    </div>
                    {subData?.current_period_end && (
                      <div className="text-right">
                        <p className="text-stone-500 text-xs">
                          {subData.status === 'cancelling' ? 'Access until' : 'Next billing'}
                        </p>
                        <p className="text-ivory-300 text-sm font-medium">
                          {new Date(subData.current_period_end).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}
                        </p>
                      </div>
                    )}
                  </div>

                  <ul className="grid sm:grid-cols-2 gap-2">
                    {(TIER_FEATURES[currentTier] ?? []).map((f) => (
                      <li key={f} className="flex items-center gap-2 text-xs text-stone-400">
                        <CheckCheck className="w-3.5 h-3.5 text-gold-400 shrink-0" />
                        {f}
                      </li>
                    ))}
                  </ul>

                  {/* Pending downgrade banner */}
                  {subData?.pending_tier && (
                    <div className="flex items-start gap-2.5 p-3 rounded-xl bg-amber-900/15 border border-amber-800/30">
                      <Clock className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                      <p className="text-amber-400 text-xs leading-relaxed">
                        Downgrading to{' '}
                        <span className="font-semibold capitalize">{subData.pending_tier}</span> on{' '}
                        {subData?.current_period_end
                          ? new Date(subData.current_period_end).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
                          : 'your next renewal date'}.
                        {' '}You keep your current plan until then.
                      </p>
                    </div>
                  )}

                  <div className="flex items-center gap-3 pt-2 border-t border-surface-border flex-wrap">
                    {subData?.status !== 'cancelling' ? (
                      <>
                        <Link to="/dashboard/subscription">
                          <Button variant="outline-gold" size="sm">Change Plan</Button>
                        </Link>
                        <button
                          onClick={() => setCancelModal('main')}
                          className="text-stone-500 hover:text-red-400 text-xs transition-colors underline underline-offset-2"
                        >
                          Cancel subscription
                        </button>
                      </>
                    ) : (
                      <div className="flex items-center gap-3 flex-wrap">
                        <span className="text-amber-500 text-xs flex items-center gap-1.5">
                          <Clock className="w-3.5 h-3.5" />
                          Cancellation scheduled — access until{' '}
                          {subData?.current_period_end
                            ? new Date(subData.current_period_end).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
                            : 'end of billing period'}
                        </span>
                        <button
                          onClick={handleReactivateMain}
                          className="text-emerald-500 hover:text-emerald-400 text-xs transition-colors underline underline-offset-2"
                        >
                          Undo cancellation
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Blue Tick subscription */}
              {hasBlueTick && (
                <div className="card-surface rounded-2xl p-6 space-y-4">
                  <div className="flex items-start justify-between gap-4 flex-wrap">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
                        <CheckCircle className="w-5 h-5 text-blue-400" />
                      </div>
                      <div>
                        <p className="text-ivory-100 font-medium">Blue Tick Add-on</p>
                        <div className="flex items-center gap-1.5 mt-0.5">
                          {subData?.blue_tick_status === 'cancelling' ? (
                            <>
                              <Clock className="w-4 h-4 text-amber-400" />
                              <span className="text-stone-400 text-xs">Cancels at period end · £3.99/month</span>
                            </>
                          ) : escort.blue_tick_active ? (
                            <>
                              <CheckCircle className="w-4 h-4 text-emerald-400" />
                              <span className="text-stone-400 text-xs">Active · £3.99/month</span>
                            </>
                          ) : (
                            <>
                              <Clock className="w-4 h-4 text-amber-400" />
                              <span className="text-stone-400 text-xs">Paid · Pending admin review · £3.99/month</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    {subData?.blue_tick_current_period_end && (
                      <div className="text-right">
                        <p className="text-stone-500 text-xs">
                          {subData.blue_tick_status === 'cancelling' ? 'Access until' : 'Next billing'}
                        </p>
                        <p className="text-ivory-300 text-sm font-medium">
                          {new Date(subData.blue_tick_current_period_end).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}
                        </p>
                      </div>
                    )}
                  </div>
                  <ul className="space-y-1.5">
                    {['Blue tick badge on your profile', 'Appears in "Blue Tick verified" filter', 'Verified trust signal to clients'].map((f) => (
                      <li key={f} className="flex items-center gap-2 text-xs text-stone-400">
                        <CheckCheck className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                        {f}
                      </li>
                    ))}
                  </ul>
                  <div className="pt-2 border-t border-surface-border">
                    {isPremiumOrElite ? (
                      <p className="text-stone-600 text-xs">Blue Tick is included with your {currentTier} plan and cannot be cancelled separately.</p>
                    ) : subData?.blue_tick_status !== 'cancelling' ? (
                      <button
                        onClick={() => setCancelModal('blue_tick')}
                        className="text-stone-500 hover:text-red-400 text-xs transition-colors underline underline-offset-2"
                      >
                        Cancel Blue Tick
                      </button>
                    ) : (
                      <div className="flex items-center gap-3 flex-wrap">
                        <span className="text-amber-500 text-xs flex items-center gap-1.5">
                          <Clock className="w-3.5 h-3.5" />
                          Cancellation scheduled — access until{' '}
                          {subData?.blue_tick_current_period_end
                            ? new Date(subData.blue_tick_current_period_end).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
                            : 'end of billing period'}
                        </span>
                        <button
                          onClick={handleReactivateBlueTick}
                          className="text-emerald-500 hover:text-emerald-400 text-xs transition-colors underline underline-offset-2"
                        >
                          Undo cancellation
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </section>

        {/* Billing history */}
        <section className="space-y-4">
          <h2 className="font-serif text-xl text-ivory-100">Billing History</h2>

          {invoicesLoading ? (
            <div className="card-surface rounded-2xl p-8 flex items-center justify-center">
              <Spinner />
            </div>
          ) : invoices.length === 0 ? (
            <div className="card-surface rounded-2xl p-8 text-center space-y-2">
              <FileText className="w-8 h-8 text-stone-600 mx-auto" />
              <p className="text-stone-500 text-sm">No invoices yet. Your payment history will appear here.</p>
            </div>
          ) : (
            <div className="card-surface rounded-2xl overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-surface-border">
                    <th className="text-left px-6 py-4 text-stone-500 font-medium text-xs uppercase tracking-wide">Date</th>
                    <th className="text-left px-6 py-4 text-stone-500 font-medium text-xs uppercase tracking-wide hidden sm:table-cell">Description</th>
                    <th className="text-left px-6 py-4 text-stone-500 font-medium text-xs uppercase tracking-wide">Amount</th>
                    <th className="text-left px-6 py-4 text-stone-500 font-medium text-xs uppercase tracking-wide">Status</th>
                    <th className="px-6 py-4" />
                  </tr>
                </thead>
                <tbody>
                  {invoices.map((inv: any, i: number) => (
                    <tr key={inv.id} className={cn('border-b border-surface-border/50 hover:bg-surface-hover/30 transition-colors', i === invoices.length - 1 && 'border-0')}>
                      <td className="px-6 py-4 text-stone-300">
                        {new Date(inv.created * 1000).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
                      </td>
                      <td className="px-6 py-4 text-stone-400 hidden sm:table-cell max-w-[220px] truncate">
                        {inv.description || 'Subscription'}
                      </td>
                      <td className="px-6 py-4 text-ivory-200 font-medium">
                        £{(inv.amount_paid / 100).toFixed(2)}
                      </td>
                      <td className="px-6 py-4">
                        <span className={cn(
                          'inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full',
                          inv.status === 'paid'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : 'bg-stone-800 text-stone-400 border border-stone-700'
                        )}>
                          {inv.status === 'paid' ? <CheckCircle className="w-3 h-3" /> : <Clock className="w-3 h-3" />}
                          {inv.status.charAt(0).toUpperCase() + inv.status.slice(1)}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        {inv.pdf_url && (
                          <a href={inv.pdf_url} target="_blank" rel="noopener noreferrer"
                            className="flex items-center gap-1 text-stone-500 hover:text-gold-400 transition-colors text-xs">
                            <ExternalLink className="w-3.5 h-3.5" />
                            PDF
                          </a>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>

      {/* Cancellation modal */}
      <AnimatePresence>
        {cancelModal && (
          <CancelModal
            target={cancelModal}
            tier={currentTier}
            onClose={() => setCancelModal(null)}
            onConfirm={cancelModal === 'main' ? handleCancelMain : handleCancelBlueTick}
          />
        )}
      </AnimatePresence>
    </DashboardLayout>
  )
}
