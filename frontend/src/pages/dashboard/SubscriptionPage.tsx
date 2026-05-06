import { useState } from 'react'
import { Helmet } from 'react-helmet-async'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { ChevronLeft, Check, Zap, Star, Crown, CheckCircle, X, Sparkles, Clock, Tag, AlertTriangle, ArrowRight, Camera, ShieldCheck, BadgeCheck, PartyPopper } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { DashboardLayout } from '@/components/layout/Layout'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import { useMyProfile } from '@/hooks/useEscorts'
import { paymentsApi, UpgradePreview } from '@/api/payments'
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

interface Pricing {
  essential_monthly_pence: number
  essential_annual_pence: number
  premium_monthly_pence: number
  premium_annual_pence: number
  elite_monthly_pence: number
  elite_annual_pence: number
  blue_tick_setup_pence: number
  blue_tick_monthly_pence: number
}

const FREE_FEATURES = [
  { text: '3 photos', included: true },
  { text: 'Searchable profile listing', included: true },
  { text: 'Contact details displayed', included: true },
  { text: '1hr customer support', included: true },
  { text: 'Identity verification', included: false },
  { text: 'Account suspension protection', included: false },
]

const PLAN_META = [
  {
    id: 'essential',
    name: 'Essential',
    icon: Zap,
    monthlyKey: 'essential_monthly_pence' as keyof Pricing,
    annualKey: 'essential_annual_pence' as keyof Pricing,
    features: [
      'Up to 8 photos',
      'Borough search placement',
      '"Available now" indicator',
      'Blue Tick add-on (after ID verification)',
      '24hr priority support',
    ],
  },
  {
    id: 'premium',
    name: 'Premium',
    icon: Star,
    popular: true,
    monthlyKey: 'premium_monthly_pence' as keyof Pricing,
    annualKey: 'premium_annual_pence' as keyof Pricing,
    features: [
      'Up to 50 photos',
      'Priority search placement',
      'Blue Tick included free (auto on ID verify)',
      'STD tested badge',
      'Everything in Essential',
    ],
  },
  {
    id: 'elite',
    name: 'Elite',
    icon: Crown,
    monthlyKey: 'elite_monthly_pence' as keyof Pricing,
    annualKey: 'elite_annual_pence' as keyof Pricing,
    features: [
      'Up to 50 photos',
      'Top of all search results (featured section)',
      'Purple Tick badge (Elite exclusive)',
      'Blog posts (coming soon)',
      'Everything in Premium',
    ],
  },
]

const DEFAULT_PRICING: Pricing = {
  essential_monthly_pence: 2499,
  essential_annual_pence: 24990,
  premium_monthly_pence: 4999,
  premium_annual_pence: 49990,
  elite_monthly_pence: 8999,
  elite_annual_pence: 89990,
  blue_tick_setup_pence: 1000,
  blue_tick_monthly_pence: 399,
}

function fmt(pence: number) {
  return `£${(pence / 100).toFixed(2)}`
}

const PHOTO_LIMITS: Record<string, number> = { free: 3, essential: 8, premium: 50, elite: 50 }

const TIER_PERKS: Record<string, { icon: React.ElementType; text: string }[]> = {
  essential: [
    { icon: Camera, text: 'Up to 8 photos on your profile' },
    { icon: CheckCircle, text: 'Borough search placement' },
    { icon: BadgeCheck, text: '"Available Now" indicator visible to clients' },
    { icon: ShieldCheck, text: 'Identity verification unlocked' },
  ],
  premium: [
    { icon: Camera, text: 'Up to 50 photos on your profile' },
    { icon: Star, text: 'Priority placement in search results' },
    { icon: BadgeCheck, text: 'Blue Tick — automatically granted on ID verify' },
    { icon: ShieldCheck, text: 'STD tested badge visible to clients' },
  ],
  elite: [
    { icon: Camera, text: 'Up to 50 photos on your profile' },
    { icon: Crown, text: 'Top of every search result — featured section' },
    { icon: BadgeCheck, text: 'Purple Tick badge — Elite exclusive' },
    { icon: Star, text: 'Blog posts & editorial features (coming soon)' },
  ],
}

type Billing = 'monthly' | 'annual'

// ---------------------------------------------------------------------------
// Post-payment success view
// ---------------------------------------------------------------------------

interface SuccessViewProps {
  tier: string
  onDismiss: () => void
}

function SuccessView({ tier, onDismiss }: SuccessViewProps) {
  const tierName = tier.charAt(0).toUpperCase() + tier.slice(1)
  const perks = TIER_PERKS[tier] ?? []
  const isElite = tier === 'elite'
  const isPremium = tier === 'premium'

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.92, y: 24 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ type: 'spring', damping: 20, stiffness: 200 }}
        className={cn(
          'relative bg-stone-950 border rounded-3xl p-8 max-w-md w-full shadow-2xl space-y-6 text-center',
          isElite ? 'border-purple-500/40' : isPremium ? 'border-gold-400/40' : 'border-emerald-500/30'
        )}
      >
        {/* Icon */}
        <div className={cn(
          'w-20 h-20 rounded-full mx-auto flex items-center justify-center',
          isElite ? 'bg-purple-500/15 border border-purple-500/30' : 'bg-gold-400/10 border border-gold-400/30'
        )}>
          {isElite ? <Crown className="w-10 h-10 text-purple-400" /> : <PartyPopper className="w-10 h-10 text-gold-400" />}
        </div>

        {/* Heading */}
        <div className="space-y-2">
          <h2 className="font-serif text-3xl text-ivory-100">Welcome to {tierName}!</h2>
          <p className="text-stone-400 text-sm">Your subscription is now active. Here's what you've just unlocked:</p>
        </div>

        {/* Perks */}
        {perks.length > 0 && (
          <ul className="space-y-3 text-left">
            {perks.map(({ icon: Icon, text }) => (
              <li key={text} className="flex items-start gap-3">
                <div className={cn(
                  'w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5',
                  isElite ? 'bg-purple-500/15' : 'bg-gold-400/10'
                )}>
                  <Icon className={cn('w-3.5 h-3.5', isElite ? 'text-purple-400' : 'text-gold-400')} />
                </div>
                <span className="text-stone-300 text-sm">{text}</span>
              </li>
            ))}
          </ul>
        )}

        {/* Next step hint */}
        <div className="p-3 rounded-xl bg-stone-900 border border-stone-800 text-left space-y-1">
          <p className="text-ivory-200 text-sm font-medium">Next step</p>
          <p className="text-stone-400 text-xs">
            Submit your identity documents to activate your verification badge — reviewed within 1 hour.
          </p>
        </div>

        {/* Actions */}
        <div className="flex flex-col gap-3">
          <Link to="/dashboard/verify" onClick={onDismiss}>
            <Button variant={isElite ? 'outline-gold' : 'gold'} fullWidth>
              Verify My Identity →
            </Button>
          </Link>
          <button
            onClick={onDismiss}
            className="text-stone-500 hover:text-stone-300 text-sm transition-colors"
          >
            I'll do this later
          </button>
        </div>
      </motion.div>
    </motion.div>
  )
}

// ---------------------------------------------------------------------------
// Confirmation modal
// ---------------------------------------------------------------------------

interface PlanChangeModalProps {
  preview: UpgradePreview
  planName: string
  onConfirm: () => void
  onCancel: () => void
  loading: boolean
  currentPhotoCount?: number
}

function PlanChangeModal({ preview, planName, onConfirm, onCancel, loading, currentPhotoCount = 0 }: PlanChangeModalProps) {
  const isUpgrade = preview.type === 'upgrade' || preview.type === 'new'
  const isDowngrade = preview.type === 'downgrade'
  const newPhotoLimit = PHOTO_LIMITS[preview.to_tier] ?? 3
  const photosOverLimit = isDowngrade ? Math.max(0, currentPhotoCount - newPhotoLimit) : 0

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onCancel} />

      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 16 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 8 }}
        className="relative bg-stone-950 border border-surface-border rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-5"
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="font-serif text-xl text-ivory-100">
              {isDowngrade ? 'Confirm Downgrade' : `Switch to ${planName}`}
            </h2>
            <p className="text-stone-500 text-sm mt-1">
              {isDowngrade
                ? `From ${preview.next_billing_date} onwards`
                : 'Review your charges before confirming'}
            </p>
          </div>
          <button onClick={onCancel} className="text-stone-500 hover:text-stone-300 transition-colors mt-0.5">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Charge breakdown */}
        {isUpgrade && (
          <div className="space-y-3">
            {/* Today's charge */}
            <div className="rounded-xl bg-gold-400/5 border border-gold-400/20 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-ivory-100 text-sm font-medium">Charged today</p>
                  <p className="text-stone-500 text-xs mt-0.5">
                    Pro-rata: {preview.remaining_days} of {preview.total_days} days remaining this month
                  </p>
                </div>
                <p className="font-serif text-2xl text-gold-400">{fmt(preview.charge_now_pence)}</p>
              </div>
              <div className="h-1.5 rounded-full bg-stone-800 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gold-400/60"
                  style={{ width: `${Math.round((preview.remaining_days / preview.total_days) * 100)}%` }}
                />
              </div>
              <p className="text-stone-600 text-xs">
                {Math.round((preview.remaining_days / preview.total_days) * 100)}% of this month remains
              </p>
            </div>

            {/* Future charge */}
            <div className="rounded-xl bg-stone-900 border border-surface-border p-4 flex items-center justify-between">
              <div>
                <p className="text-ivory-200 text-sm font-medium">From {preview.next_billing_date}</p>
                <p className="text-stone-500 text-xs mt-0.5">
                  {planName} — renews on the 1st each month
                </p>
              </div>
              <p className="text-ivory-100 font-semibold">{fmt(preview.then_pence)}<span className="text-stone-500 text-xs font-normal">/mo</span></p>
            </div>
          </div>
        )}

        {isDowngrade && (
          <div className="space-y-3">
            <div className="rounded-xl bg-stone-900 border border-surface-border p-4 space-y-2">
              <div className="flex items-center gap-2 text-amber-400">
                <Clock className="w-4 h-4 shrink-0" />
                <p className="text-sm font-medium">No charge today</p>
              </div>
              <p className="text-stone-400 text-sm">
                You keep your current plan until <strong className="text-ivory-200">{preview.next_billing_date}</strong>.
              </p>
              <p className="text-stone-400 text-sm">
                From that date, you'll be billed <strong className="text-ivory-200">{fmt(preview.then_pence)}/month</strong> for {planName}.
              </p>
            </div>
            {photosOverLimit > 0 && (
              <div className="rounded-xl bg-amber-900/20 border border-amber-700/40 p-4 space-y-2">
                <div className="flex items-center gap-2 text-amber-400">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <p className="text-sm font-medium">Photo limit warning</p>
                </div>
                <p className="text-stone-400 text-sm">
                  You currently have <strong className="text-ivory-200">{currentPhotoCount} photos</strong>, but {planName} only allows <strong className="text-ivory-200">{newPhotoLimit}</strong>.
                </p>
                <p className="text-stone-400 text-sm">
                  Please remove <strong className="text-amber-400">{photosOverLimit} photo{photosOverLimit > 1 ? 's' : ''}</strong> before <strong className="text-ivory-200">{preview.next_billing_date}</strong> to avoid your profile being paused.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Plan change summary */}
        <div className="flex items-center gap-2 text-xs text-stone-500">
          <span className="capitalize">{preview.from_tier}</span>
          <ArrowRight className="w-3 h-3" />
          <span className="capitalize text-ivory-300 font-medium">{preview.to_tier}</span>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <Button variant="ghost" fullWidth onClick={onCancel} disabled={loading}>
            Cancel
          </Button>
          <Button variant="gold" fullWidth onClick={onConfirm} loading={loading}>
            {isDowngrade
              ? `Confirm Downgrade`
              : preview.charge_now_pence === 0
                ? `Confirm Switch`
                : `Pay ${fmt(preview.charge_now_pence)} & Switch`}
          </Button>
        </div>
      </motion.div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export function SubscriptionPage() {
  const { data: escort, isLoading } = useMyProfile()
  const { data: pricing = DEFAULT_PRICING } = useQuery<Pricing>({
    queryKey: ['pricing'],
    queryFn: () => apiClient.get('/pricing').then(r => r.data),
    staleTime: 5 * 60 * 1000,
  })
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [billing, setBilling] = useState<Billing>('monthly')
  const [searchParams, setSearchParams] = useSearchParams()
  const paymentStatus = searchParams.get('payment')
  const [showSuccess, setShowSuccess] = useState(paymentStatus === 'success')

  const [codeInput, setCodeInput] = useState('')
  const [validatingCode, setValidatingCode] = useState(false)
  const [appliedCode, setAppliedCode] = useState<AppliedCode | null>(null)
  const [codeError, setCodeError] = useState<string | null>(null)

  // Modal state
  const [pendingChange, setPendingChange] = useState<{
    preview: UpgradePreview
    tier: string
    planName: string
    isNewSubscription: boolean
  } | null>(null)
  const [previewLoading, setPreviewLoading] = useState<string | null>(null)
  const [confirmLoading, setConfirmLoading] = useState(false)

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
  const hasActiveStripeSubscription = !!(escort as any).stripe_subscription_id

  const handleSubscribeClick = async (tier: string, planName: string) => {
    if (!escort.is_email_verified) {
      toast.error('Please verify your email before subscribing')
      return
    }

    const isNewSub = !hasActiveStripeSubscription || currentTier === 'free'

    if (isNewSub) {
      // New subscription — go straight to Stripe Checkout (price shown there)
      setPreviewLoading(tier)
      try {
        const { url } = await paymentsApi.createCheckout(
          tier,
          billing,
          appliedCode ? { type: appliedCode.type, code: appliedCode.code } : undefined,
        )
        window.location.href = url
      } catch (err: any) {
        toast.error(err?.response?.data?.detail ?? 'Could not start checkout. Please try again.')
      } finally {
        setPreviewLoading(null)
      }
      return
    }

    // Existing subscriber switching plans — show upgrade preview modal with exact pro-rata charge
    setPreviewLoading(tier)
    try {
      const preview = await paymentsApi.getUpgradePreview(tier, billing)
      setPendingChange({ preview, tier, planName, isNewSubscription: false })
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Could not load plan details. Please try again.')
    } finally {
      setPreviewLoading(null)
    }
  }

  const handleConfirm = async () => {
    if (!pendingChange) return
    const { tier, isNewSubscription } = pendingChange
    setConfirmLoading(true)
    try {
      if (isNewSubscription) {
        // New subscriber — redirect to Stripe Checkout
        const { url } = await paymentsApi.createCheckout(
          tier,
          billing,
          appliedCode ? { type: appliedCode.type, code: appliedCode.code } : undefined,
        )
        window.location.href = url
      } else {
        // Existing subscriber — upgrade/downgrade in-place
        const { message } = await paymentsApi.upgradeTier(tier, billing)
        toast.success(message)
        qc.invalidateQueries({ queryKey: ['my-profile'] })
        qc.invalidateQueries({ queryKey: ['subscription'] })
        setPendingChange(null)
        if (tier === 'premium' || tier === 'elite') {
          navigate('/dashboard/profile')
        }
      }
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Could not process. Please try again.')
    } finally {
      setConfirmLoading(false)
    }
  }

  const handleDismissSuccess = () => {
    setShowSuccess(false)
    setSearchParams(prev => { prev.delete('payment'); return prev }, { replace: true })
  }

  return (
    <DashboardLayout>
      <Helmet><title>Plans & Billing — Bluechips London</title></Helmet>

      {/* Post-payment success overlay */}
      <AnimatePresence>
        {showSuccess && (
          <SuccessView tier={currentTier} onDismiss={handleDismissSuccess} />
        )}
      </AnimatePresence>

      {/* Plan change confirmation modal */}
      <AnimatePresence>
        {pendingChange && (
          <PlanChangeModal
            preview={pendingChange.preview}
            planName={pendingChange.planName}
            onConfirm={handleConfirm}
            onCancel={() => { if (!confirmLoading) setPendingChange(null) }}
            loading={confirmLoading}
            currentPhotoCount={escort.photos?.length ?? 0}
          />
        )}
      </AnimatePresence>

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

        {/* Billing info note */}
        <div className="flex items-start gap-2.5 p-3 rounded-xl bg-blue-900/10 border border-blue-800/20 text-blue-400 text-xs">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          <p>
            All subscriptions bill on the <strong>1st of each month</strong> (annual: 1st January).
            Your first payment is pro-rated for the remaining days in the current month.
            Upgrades charge only the pro-rata difference — you'll see the exact amount before confirming.
          </p>
        </div>

        {/* Billing toggle + Plans */}
        <section className="space-y-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h2 className="font-serif text-2xl text-ivory-100">Choose Your Plan</h2>
              <p className="text-stone-500 text-sm mt-1">All plans include your listing and searchable profile.</p>
            </div>

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

          {/* Plans grid — Free + 3 paid tiers */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {/* Free tier card */}
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              className={cn(
                'card-surface rounded-2xl p-6 space-y-6 relative',
                currentTier === 'free' && 'border-emerald-500/40'
              )}
            >
              {currentTier === 'free' && (
                <div className="absolute -top-3 right-4 bg-emerald-500 text-white text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-wide">
                  Active
                </div>
              )}
              <div className="space-y-1">
                <div className="w-9 h-9 rounded-lg bg-stone-800 border border-stone-700 flex items-center justify-center mb-3">
                  <Sparkles className="w-4 h-4 text-stone-400" />
                </div>
                <h3 className="font-serif text-xl text-ivory-100">Free</h3>
                <div className="flex items-baseline gap-1">
                  <span className="font-serif text-3xl text-stone-300">£0</span>
                  <span className="text-stone-500 text-sm">/month</span>
                </div>
              </div>
              <ul className="space-y-2.5">
                {FREE_FEATURES.map((f) => (
                  <li key={f.text} className="flex items-start gap-2.5 text-sm">
                    {f.included
                      ? <Check className="w-4 h-4 text-stone-400 shrink-0 mt-0.5" />
                      : <X className="w-4 h-4 text-stone-700 shrink-0 mt-0.5" />
                    }
                    <span className={f.included ? 'text-stone-400' : 'text-stone-600'}>{f.text}</span>
                  </li>
                ))}
              </ul>
              {currentTier === 'free'
                ? <Button variant="ghost" fullWidth disabled>Current Plan</Button>
                : <p className="text-stone-600 text-xs text-center pt-2">Your default plan</p>
              }
            </motion.div>

            {PLAN_META.map((plan, i) => {
              const isActive = plan.id === currentTier
              const Icon = plan.icon
              const isLoadingThis = previewLoading === plan.id
              const monthlyPence = pricing[plan.monthlyKey]
              const annualPence = pricing[plan.annualKey]
              const price = billing === 'annual' ? annualPence : monthlyPence
              const perMonth = billing === 'annual' ? Math.round(annualPence / 12) : monthlyPence
              const saving = monthlyPence * 12 - annualPence

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
                      loading={isLoadingThis}
                      onClick={() => handleSubscribeClick(plan.id, plan.name)}
                    >
                      {currentTier === 'free' ? `Subscribe — ${fmt(billing === 'annual' ? price : price)}/mo` : `Switch to ${plan.name}`}
                    </Button>
                  )}
                </motion.div>
              )
            })}
          </div>
        </section>

        {/* Promo / Referral Code — only for new subscribers */}
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

        {/* Verification Badge section */}
        <section className="space-y-4">
          {currentTier === 'elite' ? (
            <>
              <div>
                <h2 className="font-serif text-2xl text-ivory-100">Purple Tick</h2>
                <p className="text-stone-500 text-sm mt-1">
                  Exclusive to Elite subscribers — replaces the Blue Tick with a premium purple badge.
                </p>
              </div>
              <div className="card-surface rounded-2xl p-6 space-y-5 max-w-lg border-purple-500/20">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h3 className="font-serif text-lg text-ivory-100 flex items-center gap-2">
                      Purple Tick
                      {escort.verification_level >= 2 && (
                        <span className="bg-purple-500/10 text-purple-400 border border-purple-500/30 text-[10px] font-bold px-2 py-0.5 rounded-full">ACTIVE</span>
                      )}
                    </h3>
                    <p className="text-stone-500 text-sm mt-1">Elite-exclusive badge. Activates automatically when your identity is verified.</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-purple-400 font-semibold text-sm">Free</p>
                    <p className="text-stone-600 text-xs">Elite exclusive</p>
                  </div>
                </div>
                <ul className="space-y-2">
                  {[
                    'Purple tick badge — Elite exclusive',
                    'Appears in "Verified" filter',
                    'Reviewed by our team within 1 hour',
                    'Included with your Elite plan',
                  ].map((f) => (
                    <li key={f} className="flex items-center gap-2 text-sm text-stone-300">
                      <Check className="w-4 h-4 text-purple-400 shrink-0" />
                      {f}
                    </li>
                  ))}
                </ul>
                {escort.verification_level >= 2 ? (
                  <div className="flex items-center gap-2 p-3 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 text-sm">
                    <CheckCircle className="w-4 h-4 shrink-0" />
                    Purple Tick is active on your profile.
                  </div>
                ) : (
                  <div className="space-y-2">
                    <p className="text-amber-500 text-xs p-3 rounded-lg bg-amber-900/20 border border-amber-800/30">
                      Submit identity verification — your Purple Tick will activate automatically when approved.
                    </p>
                    <Link to="/dashboard/verify">
                      <Button variant="outline-gold" fullWidth size="sm">Verify Identity to Activate →</Button>
                    </Link>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <div>
                <h2 className="font-serif text-2xl text-ivory-100">Blue Tick</h2>
                <p className="text-stone-500 text-sm mt-1">
                  {currentTier === 'premium'
                    ? 'Included free with your plan — activates automatically when your identity is approved.'
                    : currentTier === 'essential'
                      ? 'Optional add-on for Essential subscribers. Requires identity verification first.'
                      : 'Requires an active paid subscription.'}
                </p>
              </div>

              {currentTier === 'premium' ? (
                <div className="card-surface rounded-2xl p-6 space-y-5 max-w-lg">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h3 className="font-serif text-lg text-ivory-100 flex items-center gap-2">
                        Blue Tick
                        {escort.blue_tick_active && (
                          <span className="bg-blue-500/10 text-blue-400 border border-blue-500/30 text-[10px] font-bold px-2 py-0.5 rounded-full">ACTIVE</span>
                        )}
                      </h3>
                      <p className="text-stone-500 text-sm mt-1">Prove your photos are genuinely yours. Included free with Premium.</p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-emerald-400 font-semibold text-sm">Free</p>
                      <p className="text-stone-600 text-xs">with Premium</p>
                    </div>
                  </div>
                  <ul className="space-y-2">
                    {[
                      'Blue tick badge on your profile',
                      'Appears in "Blue Tick verified" filter',
                      'Reviewed by our team within 1 hour',
                      'Included with Premium plan',
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
                <div className="card-surface rounded-2xl p-6 space-y-5 max-w-lg">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h3 className="font-serif text-lg text-ivory-100 flex items-center gap-2">
                        Blue Tick
                        {escort.blue_tick_active && (
                          <span className="bg-blue-500/10 text-blue-400 border border-blue-500/30 text-[10px] font-bold px-2 py-0.5 rounded-full">ACTIVE</span>
                        )}
                        {!escort.blue_tick_active && (escort as any).blue_tick_stripe_subscription_id && (
                          <span className="bg-amber-500/10 text-amber-400 border border-amber-500/30 text-[10px] font-bold px-2 py-0.5 rounded-full">PENDING REVIEW</span>
                        )}
                      </h3>
                      <p className="text-stone-500 text-sm mt-1">Prove your photos are genuinely yours. Hugely increases client trust and bookings.</p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="text-gold-400 font-semibold">{fmt(pricing.blue_tick_setup_pence)} setup</p>
                      <p className="text-stone-500 text-xs">then {fmt(pricing.blue_tick_monthly_pence)}/month</p>
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
                  {(escort as any).blue_tick_stripe_subscription_id ? (
                    <Link to="/dashboard/subscriptions">
                      <Button variant="ghost" fullWidth>
                        {escort.blue_tick_active ? 'Manage Blue Tick' : 'View Blue Tick Status →'}
                      </Button>
                    </Link>
                  ) : escort.verification_level < 2 ? (
                    <div className="space-y-2">
                      <div className="p-3 rounded-lg bg-amber-900/20 border border-amber-800/30 text-amber-500 text-xs">
                        Complete identity verification first before applying for Blue Tick
                      </div>
                      <Link to="/dashboard/verify">
                        <Button variant="outline-gold" fullWidth size="sm">Go to Identity Verification →</Button>
                      </Link>
                    </div>
                  ) : (
                    <Link to="/dashboard/verify">
                      <Button variant="gold" fullWidth>Apply for Blue Tick — {fmt(pricing.blue_tick_setup_pence)} + {fmt(pricing.blue_tick_monthly_pence)}/mo</Button>
                    </Link>
                  )}
                </div>
              ) : (
                <div className="card-surface rounded-2xl p-6 max-w-lg">
                  <p className="text-stone-500 text-sm text-center">
                    Subscribe to a paid plan to unlock the Blue Tick add-on.
                  </p>
                </div>
              )}
            </>
          )}
        </section>

        <div className="text-center p-6 rounded-xl border border-stone-800 bg-stone-900/20 max-w-lg mx-auto space-y-1">
          <p className="text-stone-400 text-sm">All plans renew on the 1st of each month. Cancel anytime from <Link to="/dashboard/subscriptions" className="text-gold-400 hover:text-gold-300 underline underline-offset-2">My Subscriptions</Link>.</p>
          <p className="text-stone-600 text-xs">Payments processed securely by Stripe. We never store your card details.</p>
        </div>
      </div>
    </DashboardLayout>
  )
}
