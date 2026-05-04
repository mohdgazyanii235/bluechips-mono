import { useState } from 'react'
import { Helmet } from 'react-helmet-async'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { ChevronLeft, Check, Zap, Star, Crown, CheckCircle, X, Sparkles, Clock, Tag } from 'lucide-react'
import { motion } from 'framer-motion'
import { useQueryClient } from '@tanstack/react-query'
import { DashboardLayout } from '@/components/layout/Layout'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import { useMyProfile } from '@/hooks/useEscorts'
import { paymentsApi } from '@/api/payments'
import apiClient from '@/api/client'
import { cn } from '@/utils/cn'
import toast from 'react-hot-toast'

interface AppliedCode {
  code: string
  type: 'discount' | 'referral'
  percent_off: number
  duration_months: number
  discount_amount_pence: number
}

const PLANS = [
  {
    id: 'essential',
    name: 'Essential',
    monthlyPence: 1199,
    annualPence: 11990,   // £119.90/yr — 2 months free (10× monthly)
    icon: Zap,
    features: [
      'Up to 8 photos',
      'Identity verification badge',
      'Borough search placement',
      '"Available now" indicator',
      'Blue Tick add-on available',
    ],
  },
  {
    id: 'premium',
    name: 'Premium',
    monthlyPence: 1899,
    annualPence: 18990,   // £189.90/yr — 2 months free (10× monthly)
    icon: Star,
    popular: true,
    features: [
      'Up to 50 photos',
      'Featured search placement',
      'Blue Tick included free',
      'STD tested badge',
      'Everything in Essential',
    ],
  },
  {
    id: 'elite',
    name: 'Elite',
    monthlyPence: 2399,
    annualPence: 23990,   // £239.90/yr — 2 months free (10× monthly)
    icon: Crown,
    features: [
      'Homepage rotation',
      'Top of all search results',
      'Dedicated "Elite" badge',
      'Blue Tick included free',
      'Everything in Premium',
    ],
  },
]

function fmt(pence: number) {
  return `£${(pence / 100).toFixed(2)}`
}

type Billing = 'monthly' | 'annual'

export function SubscriptionPage() {
  const { data: escort, isLoading } = useMyProfile()
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [loadingTier, setLoadingTier] = useState<string | null>(null)
  const [billing, setBilling] = useState<Billing>('monthly')
  const [searchParams] = useSearchParams()
  const paymentStatus = searchParams.get('payment')

  const [codeInput, setCodeInput] = useState('')
  const [validatingCode, setValidatingCode] = useState(false)
  const [appliedCode, setAppliedCode] = useState<AppliedCode | null>(null)
  const [codeError, setCodeError] = useState<string | null>(null)

  const validateCode = async () => {
    const code = codeInput.trim().toUpperCase()
    if (!code) return
    setValidatingCode(true)
    setCodeError(null)
    try {
      const { data } = await apiClient.post('/discounts/validate', {
        code,
        tier: 'essential',
        billing,
      })
      if (data.valid) {
        setAppliedCode({ code, type: data.code_type, percent_off: data.percent_off, duration_months: data.duration_months, discount_amount_pence: data.discount_amount_pence })
      } else {
        setCodeError(data.message ?? 'Invalid code')
      }
    } catch {
      setCodeError('Could not validate code. Please try again.')
    } finally {
      setValidatingCode(false)
    }
  }

  const removeCode = () => { setAppliedCode(null); setCodeInput(''); setCodeError(null) }

  if (isLoading) return <DashboardLayout><Spinner fullPage /></DashboardLayout>
  if (!escort) return null

  const currentTier = escort.subscription_tier
  const isPaid = currentTier !== 'free'
  const isPremiumOrElite = currentTier === 'premium' || currentTier === 'elite'
  const hasActiveStripeSubscription = !!(escort as any).stripe_subscription_id

  const handleSubscribe = async (tier: string) => {
    if (!escort.is_email_verified) {
      toast.error('Please verify your email before subscribing')
      return
    }
    setLoadingTier(tier)
    try {
      if (hasActiveStripeSubscription) {
        // Existing subscriber — modify the subscription in-place, no redirect
        const { message } = await paymentsApi.upgradeTier(tier, billing)
        toast.success(message)
        qc.invalidateQueries({ queryKey: ['my-profile'] })
        qc.invalidateQueries({ queryKey: ['subscription'] })
        // For upgrades to premium/elite: go to profile so they can upload their new photo allowance
        if (tier === 'premium' || tier === 'elite') {
          navigate('/dashboard/profile')
        }
      } else {
        // New subscriber — open Stripe Checkout
        const { url } = await paymentsApi.createCheckout(
          tier,
          billing,
          appliedCode ? { type: appliedCode.type, code: appliedCode.code } : undefined,
        )
        window.location.href = url
      }
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Could not process. Please try again.')
    } finally {
      setLoadingTier(null)
    }
  }

  return (
    <DashboardLayout>
      <Helmet><title>Plans & Billing — Bluechips London</title></Helmet>

      <div className="page-container py-10 space-y-12">
        {/* Header */}
        <div className="flex items-center gap-3">
          <Link to="/dashboard" className="text-stone-500 hover:text-gold-400 transition-colors">
            <ChevronLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="font-serif text-3xl text-ivory-100">Plans & Billing</h1>
            <p className="text-stone-500 text-sm mt-0.5">
              Current plan: <span className="text-gold-400 font-medium capitalize">{currentTier}</span>
              {isPaid && (
                <Link to="/dashboard/subscriptions" className="ml-3 text-stone-500 hover:text-gold-400 underline underline-offset-2 text-xs transition-colors">
                  View billing history →
                </Link>
              )}
            </p>
          </div>
        </div>

        {/* Payment result banners */}
        {paymentStatus === 'success' && (
          <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-3 p-4 rounded-xl bg-emerald-900/20 border border-emerald-500/30 text-emerald-400">
            <CheckCircle className="w-5 h-5 shrink-0" />
            <div>
              <p className="font-medium text-sm">Payment successful!</p>
              <p className="text-emerald-600 text-xs mt-0.5">
                Your subscription is now active. Submit your identity verification to unlock your full profile.
              </p>
            </div>
          </motion.div>
        )}
        {paymentStatus === 'cancelled' && (
          <div className="flex items-center gap-3 p-4 rounded-xl bg-stone-900/40 border border-stone-700 text-stone-400">
            <X className="w-5 h-5 shrink-0" />
            <p className="text-sm">Payment cancelled — no charge was made. You can try again whenever you're ready.</p>
          </div>
        )}

        {/* Free tier notice */}
        {!isPaid && (
          <div className="p-4 rounded-xl bg-gold-400/5 border border-gold-400/20 flex items-start gap-3">
            <Sparkles className="w-5 h-5 text-gold-400 shrink-0 mt-0.5" />
            <div>
              <p className="text-gold-400 text-sm font-medium">Your free listing is active</p>
              <p className="text-stone-500 text-xs mt-1">
                You have a basic searchable profile. Upgrade to unlock contact buttons, more photos, and verification badges — shown to clients to build trust and get more bookings.
              </p>
            </div>
          </div>
        )}

        {/* Billing toggle */}
        <section className="space-y-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h2 className="font-serif text-2xl text-ivory-100">Choose Your Plan</h2>
              <p className="text-stone-500 text-sm mt-1">All plans include your listing and searchable profile.</p>
            </div>

            {/* Monthly / Annual toggle */}
            <div className="flex items-center gap-1 p-1 rounded-xl bg-surface border border-surface-border">
              <button
                onClick={() => setBilling('monthly')}
                className={cn(
                  'px-4 py-2 rounded-lg text-sm font-medium transition-all',
                  billing === 'monthly'
                    ? 'bg-gold-400/10 text-gold-400 border border-gold-400/30'
                    : 'text-stone-500 hover:text-stone-300'
                )}
              >
                Monthly
              </button>
              <button
                onClick={() => setBilling('annual')}
                className={cn(
                  'px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2',
                  billing === 'annual'
                    ? 'bg-gold-400/10 text-gold-400 border border-gold-400/30'
                    : 'text-stone-500 hover:text-stone-300'
                )}
              >
                Annual
                <span className="bg-emerald-500/20 text-emerald-400 text-[10px] font-bold px-1.5 py-0.5 rounded-full">
                  2 MONTHS FREE
                </span>
              </button>
            </div>
          </div>

          {/* Plans grid */}
          <div className="grid sm:grid-cols-3 gap-5">
            {PLANS.map((plan, i) => {
              const isActive = plan.id === currentTier
              const Icon = plan.icon
              const isLoading = loadingTier === plan.id
              const price = billing === 'annual' ? plan.annualPence : plan.monthlyPence
              const perMonth = billing === 'annual'
                ? Math.round(plan.annualPence / 12)
                : plan.monthlyPence
              const saving = plan.monthlyPence * 12 - plan.annualPence

              return (
                <motion.div
                  key={plan.id}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.07 }}
                  className={cn(
                    'card-surface rounded-2xl p-6 space-y-6 relative',
                    plan.popular && 'border-gold-400/40 shadow-gold',
                    isActive && 'border-emerald-500/40'
                  )}
                >
                  {plan.popular && !isActive && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gold-400 text-black text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-wide">
                      Most Popular
                    </div>
                  )}
                  {isActive && (
                    <div className="absolute -top-3 right-4 bg-emerald-500 text-white text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-wide">
                      Active
                    </div>
                  )}

                  <div className="space-y-1">
                    <div className="w-9 h-9 rounded-lg bg-gold-400/10 border border-gold-400/20 flex items-center justify-center mb-3">
                      <Icon className="w-4 h-4 text-gold-400" />
                    </div>
                    <h3 className="font-serif text-xl text-ivory-100">{plan.name}</h3>
                    {billing === 'annual' ? (
                      <div>
                        <div className="flex items-baseline gap-1">
                          <span className="font-serif text-3xl text-gold-400">{fmt(perMonth)}</span>
                          <span className="text-stone-500 text-sm">/month</span>
                        </div>
                        <p className="text-stone-500 text-xs mt-0.5">
                          {fmt(price)}/year
                          <span className="text-emerald-400 ml-1">· save {fmt(saving)}</span>
                        </p>
                      </div>
                    ) : (
                      <div className="flex items-baseline gap-1">
                        <span className="font-serif text-3xl text-gold-400">{fmt(price)}</span>
                        <span className="text-stone-500 text-sm">/month</span>
                      </div>
                    )}
                  </div>

                  <ul className="space-y-2.5">
                    {plan.features.map((feat) => (
                      <li key={feat} className="flex items-start gap-2.5 text-sm">
                        <Check className="w-4 h-4 text-gold-400 shrink-0 mt-0.5" />
                        <span className="text-stone-300">{feat}</span>
                      </li>
                    ))}
                  </ul>

                  {isActive ? (
                    <Link to="/dashboard/subscriptions">
                      <Button variant="ghost" fullWidth>Manage Subscription</Button>
                    </Link>
                  ) : (
                    <Button
                      variant={plan.popular ? 'gold' : 'outline-gold'}
                      fullWidth
                      loading={isLoading}
                      onClick={() => handleSubscribe(plan.id)}
                    >
                      {currentTier === 'free'
                        ? billing === 'annual'
                          ? `Subscribe — ${fmt(price)}/yr`
                          : `Subscribe — ${fmt(price)}/mo`
                        : hasActiveStripeSubscription
                          ? `Switch to ${plan.name}`
                          : `Subscribe — ${fmt(price)}${billing === 'annual' ? '/yr' : '/mo'}`}
                    </Button>
                  )}
                </motion.div>
              )
            })}
          </div>
        </section>

        {/* Promo / Referral Code */}
        {!hasActiveStripeSubscription && (
          <section className="space-y-3 max-w-lg">
            <button
              onClick={() => setCodeInput(codeInput === '' && !appliedCode ? ' ' : '')}
              className="flex items-center gap-2 text-stone-400 hover:text-gold-400 text-sm transition-colors"
            >
              <Tag className="w-4 h-4" />
              Have a promo or referral code?
            </button>

            {appliedCode ? (
              <div className="flex items-center justify-between p-4 rounded-xl bg-emerald-900/20 border border-emerald-500/30">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0" />
                  <div>
                    <p className="text-emerald-400 text-sm font-medium">
                      {appliedCode.code} — {appliedCode.percent_off}% off for {appliedCode.duration_months} month{appliedCode.duration_months > 1 ? 's' : ''}
                    </p>
                    <p className="text-emerald-600 text-xs mt-0.5">
                      {appliedCode.type === 'referral' ? 'Referral discount — applied at checkout' : 'Promo discount — applied at checkout'}
                    </p>
                  </div>
                </div>
                <button onClick={removeCode} className="text-stone-500 hover:text-stone-300 ml-4">
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="space-y-1.5">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={codeInput.trim()}
                    onChange={(e) => { setCodeInput(e.target.value.toUpperCase()); setCodeError(null) }}
                    onKeyDown={(e) => e.key === 'Enter' && validateCode()}
                    placeholder="Enter code..."
                    className="flex-1 bg-surface border border-surface-border rounded-xl px-4 py-2.5 text-sm text-ivory-100 placeholder-stone-600 focus:outline-none focus:border-gold-400/40"
                  />
                  <Button
                    variant="outline-gold"
                    size="sm"
                    loading={validatingCode}
                    onClick={validateCode}
                    disabled={!codeInput.trim()}
                  >
                    Apply
                  </Button>
                </div>
                {codeError && <p className="text-red-400 text-xs pl-1">{codeError}</p>}
              </div>
            )}
          </section>
        )}

        {/* Blue Tick section — behaviour differs by tier */}
        <section className="space-y-4">
          <div>
            <h2 className="font-serif text-2xl text-ivory-100">Blue Tick</h2>
            <p className="text-stone-500 text-sm mt-1">
              {isPremiumOrElite
                ? 'Included free with your plan — activates automatically when your identity is approved.'
                : currentTier === 'essential'
                  ? 'Optional add-on for Essential subscribers. Requires identity verification first.'
                  : 'Requires an active paid subscription.'}
            </p>
          </div>

          {isPremiumOrElite ? (
            /* ── Premium / Elite: Blue Tick is free and automatic ── */
            <div className="card-surface rounded-2xl p-6 space-y-5 max-w-lg">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="font-serif text-lg text-ivory-100 flex items-center gap-2">
                    Blue Tick
                    {escort.blue_tick_active && (
                      <span className="bg-blue-500/10 text-blue-400 border border-blue-500/30 text-[10px] font-bold px-2 py-0.5 rounded-full">ACTIVE</span>
                    )}
                  </h3>
                  <p className="text-stone-500 text-sm mt-1">Prove your photos are genuinely yours. Included free with your plan.</p>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-emerald-400 font-semibold text-sm">Free</p>
                  <p className="text-stone-600 text-xs">with your plan</p>
                </div>
              </div>
              <ul className="space-y-2">
                {[
                  'Blue tick badge on your profile',
                  'Appears in "Blue Tick verified" filter',
                  'Reviewed by our team within 1 hour',
                  'Included with all Premium & Elite plans',
                ].map((f) => (
                  <li key={f} className="flex items-center gap-2 text-sm text-stone-300">
                    <Check className="w-4 h-4 text-blue-400 shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>
              {escort.blue_tick_active ? (
                <div className="flex items-center gap-2 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm">
                  <CheckCircle className="w-4 h-4 shrink-0" />
                  Blue Tick is active on your profile.
                </div>
              ) : escort.verification_level >= 2 ? (
                <div className="flex items-center gap-2 p-3 rounded-xl bg-amber-900/15 border border-amber-800/30 text-amber-400 text-xs">
                  <Clock className="w-4 h-4 shrink-0" />
                  Identity verified — Blue Tick will activate once our team completes the review.
                </div>
              ) : (
                <div className="space-y-2">
                  <p className="text-amber-500 text-xs p-3 rounded-lg bg-amber-900/20 border border-amber-800/30">
                    Submit identity verification — your Blue Tick will activate automatically when approved.
                  </p>
                  <Link to="/dashboard/verify">
                    <Button variant="outline-gold" fullWidth size="sm">Verify Identity to Activate →</Button>
                  </Link>
                </div>
              )}
            </div>
          ) : currentTier === 'essential' ? (
            /* ── Essential: Blue Tick is a paid add-on ── */
            <div className="card-surface rounded-2xl p-6 space-y-5 max-w-lg">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="font-serif text-lg text-ivory-100 flex items-center gap-2">
                    Blue Tick
                    {escort.blue_tick_active && (
                      <span className="bg-blue-500/10 text-blue-400 border border-blue-500/30 text-[10px] font-bold px-2 py-0.5 rounded-full">ACTIVE</span>
                    )}
                    {!escort.blue_tick_active && escort.blue_tick_stripe_subscription_id && (
                      <span className="bg-amber-500/10 text-amber-400 border border-amber-500/30 text-[10px] font-bold px-2 py-0.5 rounded-full">PENDING REVIEW</span>
                    )}
                  </h3>
                  <p className="text-stone-500 text-sm mt-1">Prove your photos are genuinely yours. Hugely increases client trust and bookings.</p>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-gold-400 font-semibold">£10 setup</p>
                  <p className="text-stone-500 text-xs">then £3.99/month</p>
                </div>
              </div>
              <ul className="space-y-2">
                {['Blue tick badge on your profile', 'Appears in "Blue Tick verified" filter', 'Reviewed by our team within 1 hour', 'Cancel anytime'].map((f) => (
                  <li key={f} className="flex items-center gap-2 text-sm text-stone-300">
                    <Check className="w-4 h-4 text-blue-400 shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>
              {escort.blue_tick_stripe_subscription_id ? (
                <Link to="/dashboard/subscriptions">
                  <Button variant="ghost" fullWidth>
                    {escort.blue_tick_active ? 'Manage Blue Tick' : 'View Blue Tick Status →'}
                  </Button>
                </Link>
              ) : escort.verification_level < 2 ? (
                <div className="space-y-2">
                  <div className="p-3 rounded-lg bg-amber-900/20 border border-amber-800/30 text-amber-500 text-xs">
                    Complete identity verification first before applying for the Blue Tick
                  </div>
                  <Link to="/dashboard/verify">
                    <Button variant="outline-gold" fullWidth size="sm">Go to Verification →</Button>
                  </Link>
                </div>
              ) : (
                <Link to="/dashboard/verify">
                  <Button variant="gold" fullWidth>Apply for Blue Tick — £10 + £3.99/mo</Button>
                </Link>
              )}
            </div>
          ) : (
            /* ── Free tier: must subscribe first ── */
            <div className="card-surface rounded-2xl p-6 max-w-lg">
              <p className="text-stone-500 text-sm text-center">
                Subscribe to a paid plan to unlock the Blue Tick.
              </p>
            </div>
          )}
        </section>

        <div className="text-center p-6 rounded-xl border border-stone-800 bg-stone-900/20 max-w-lg mx-auto space-y-1">
          <p className="text-stone-400 text-sm">All plans renew automatically. Cancel anytime from <Link to="/dashboard/subscriptions" className="text-gold-400 hover:text-gold-300 underline underline-offset-2">My Subscriptions</Link>.</p>
          <p className="text-stone-600 text-xs">Payments processed securely by Stripe. We never store your card details.</p>
        </div>
      </div>
    </DashboardLayout>
  )
}
