import React from 'react'
import { Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { motion } from 'framer-motion'
import {
  Eye, Phone, User, Camera, BadgeCheck, ShieldCheck, AlertCircle,
  TrendingUp, ToggleLeft, ToggleRight, Star, ChevronRight, Mail,
  Sparkles, Zap, Crown, ArrowRight, XCircle, Gift, Copy, Check,
} from 'lucide-react'
import { DashboardLayout } from '@/components/layout/Layout'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { VerificationBadge } from '@/components/escort/VerificationBadge'
import { useMyProfile, useToggleAvailableNow } from '@/hooks/useEscorts'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/api/client'
import { Spinner } from '@/components/ui/Spinner'
import { completionPercentage } from '@/utils/formatters'
import { cn } from '@/utils/cn'

function StatCard({ icon: Icon, label, value, color = 'gold' }: any) {
  return (
    <div className="card-surface p-5 rounded-xl space-y-3">
      <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center',
        color === 'gold' ? 'bg-gold-400/10 border border-gold-400/20' : 'bg-emerald-500/10 border border-emerald-500/20'
      )}>
        <Icon className={cn('w-5 h-5', color === 'gold' ? 'text-gold-400' : 'text-emerald-400')} />
      </div>
      <div>
        <p className="font-serif text-2xl text-ivory-100">{value}</p>
        <p className="text-stone-500 text-xs mt-0.5">{label}</p>
      </div>
    </div>
  )
}

export function DashboardPage() {
  const { data: escort, isLoading } = useMyProfile()
  const toggleAvailable = useToggleAvailableNow()
  const [codeCopied, setCodeCopied] = React.useState(false)

  const { data: verificationStatus } = useQuery({
    queryKey: ['verification-status'],
    queryFn: () => apiClient.get('/verification/status').then(r => r.data),
    enabled: !!escort,
  })

  if (isLoading) return <DashboardLayout><Spinner fullPage /></DashboardLayout>
  if (!escort) return null

  const completion = completionPercentage(escort as any)

  const submissions: any[] = verificationStatus?.submissions ?? []
  const lastBlueTick = submissions.find((s: any) => s.level === 3)
  const lastIdentity = submissions.find((s: any) => s.level === 2)
  const blueTickRejected = lastBlueTick?.status === 'rejected'
  const identityRejected = lastIdentity?.status === 'rejected'
  const tierColors: Record<string, string> = { free: 'stone', essential: 'blue', premium: 'gold', elite: 'gold' }

  return (
    <DashboardLayout>
      <Helmet><title>Dashboard — Bluechips London</title></Helmet>

      <div className="page-container py-10 space-y-8">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <p className="text-stone-500 text-sm">Welcome back</p>
            <h1 className="font-serif text-3xl text-ivory-100">{escort.stage_name}</h1>
          </div>

          {/* Available Now toggle */}
          <button
            onClick={() => toggleAvailable.mutate(!escort.available_now)}
            className={cn(
              'flex items-center gap-2 px-5 py-2.5 rounded-full border font-medium text-sm transition-all',
              escort.available_now
                ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-400'
                : 'bg-surface border-surface-border text-stone-400 hover:border-stone-600'
            )}
          >
            {escort.available_now
              ? <><ToggleRight className="w-5 h-5" /> Available Now</>
              : <><ToggleLeft className="w-5 h-5" /> Set Available</>
            }
          </button>
        </div>

        {/* Alerts */}
        <div className="space-y-3">
          {!escort.is_email_verified && (
            <div className="flex items-start gap-3 p-4 rounded-xl bg-amber-900/20 border border-amber-800/40 text-amber-400">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-medium text-sm">Verify your email</p>
                <p className="text-amber-600 text-xs mt-0.5">Check your inbox for a verification link to activate your profile.</p>
              </div>
            </div>
          )}

          {escort.subscription_tier !== 'free' && escort.verification_level < 2 && (
            <div className="flex items-start justify-between gap-3 p-4 rounded-xl bg-blue-900/20 border border-blue-800/30 text-blue-400">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-sm">Submit identity verification</p>
                  <p className="text-blue-600 text-xs mt-0.5">
                    You're subscribed — now verify your identity to activate your profile features. Reviewed within 1 hour. If denied, you get a full refund.
                  </p>
                </div>
              </div>
              <Link to="/dashboard/verify" className="shrink-0">
                <Button variant="outline-gold" size="sm">Verify →</Button>
              </Link>
            </div>
          )}

          {completion < 80 && (
            <div className="p-4 rounded-xl bg-gold-900/20 border border-gold-800/30">
              <div className="flex items-center justify-between mb-2">
                <p className="text-gold-400 text-sm font-medium">Complete your profile</p>
                <span className="text-gold-400 text-sm font-bold">{completion}%</span>
              </div>
              <div className="h-1.5 bg-surface rounded-full overflow-hidden">
                <div className="h-full bg-gold-400 rounded-full transition-all" style={{ width: `${completion}%` }} />
              </div>
              <p className="text-stone-500 text-xs mt-2">A complete profile gets 3× more views. <Link to="/dashboard/profile" className="text-gold-400 hover:text-gold-300">Complete now →</Link></p>
            </div>
          )}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard icon={Eye} label="Profile Views" value={escort.profile_views.toLocaleString()} />
          <StatCard icon={Phone} label="Contact Clicks" value={escort.contact_clicks.toLocaleString()} color="emerald" />
          <StatCard icon={Camera} label="Photos" value={`${escort.photos.length} / ${escort.photo_limit}`} />
          <Link to="/dashboard/subscription" className="block">
            <div className={cn('card-surface p-5 rounded-xl space-y-3 transition-all', escort.subscription_tier === 'free' && 'hover:border-gold-400/30 cursor-pointer')}>
              <div className="w-10 h-10 rounded-lg flex items-center justify-center bg-gold-400/10 border border-gold-400/20">
                <TrendingUp className="w-5 h-5 text-gold-400" />
              </div>
              <div>
                <p className="font-serif text-2xl text-ivory-100">
                  {escort.subscription_tier.charAt(0).toUpperCase() + escort.subscription_tier.slice(1)}
                </p>
                <p className="text-stone-500 text-xs mt-0.5">
                  {escort.subscription_tier === 'free' ? 'Tap to upgrade →' : 'Current plan'}
                </p>
              </div>
            </div>
          </Link>
        </div>

        {/* Upgrade upsell — free tier only */}
        {escort.subscription_tier === 'free' && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="relative overflow-hidden rounded-2xl border border-gold-400/30 bg-gradient-to-br from-gold-900/20 via-stone-900 to-stone-950 p-6"
          >
            <div className="absolute -right-8 -top-8 w-32 h-32 rounded-full bg-gold-400/5 blur-2xl" />
            <div className="absolute -right-4 bottom-0 w-24 h-24 rounded-full bg-gold-400/5 blur-xl" />

            <div className="relative flex flex-col sm:flex-row sm:items-center gap-6 justify-between">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-gold-400" />
                  <span className="text-gold-400 text-xs font-bold uppercase tracking-widest">Unlock Your Full Potential</span>
                </div>
                <h3 className="font-serif text-xl text-ivory-100">Get more bookings with a paid plan</h3>
                <p className="text-stone-400 text-sm max-w-md">
                  Free profiles get buried. Paid escorts get contact buttons, featured search placement, identity verification, and up to 50 photos — all shown to clients actively browsing London.
                </p>
                <div className="flex items-center gap-4 pt-1">
                  <div className="flex items-center gap-1.5 text-xs text-stone-400">
                    <Zap className="w-3.5 h-3.5 text-gold-400" />
                    Essential from <span className="text-gold-400 font-bold">£11.99/mo</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-stone-400">
                    <Crown className="w-3.5 h-3.5 text-gold-400" />
                    2 months free on annual
                  </div>
                </div>
              </div>
              <div className="shrink-0">
                <Link to="/dashboard/subscription">
                  <button className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gold-400 text-black font-bold text-sm hover:bg-gold-300 transition-colors whitespace-nowrap">
                    See Plans <ArrowRight className="w-4 h-4" />
                  </button>
                </Link>
              </div>
            </div>
          </motion.div>
        )}

        {/* Quick actions */}
        <div className="grid sm:grid-cols-2 gap-4">
          {[
            { icon: User, label: 'Edit Profile', desc: 'Update details, photos and services', href: '/dashboard/profile', cta: 'Edit' },
            { icon: Star, label: 'Subscription', desc: escort.subscription_tier === 'free' ? 'Upgrade for more visibility' : 'Manage your plan', href: '/dashboard/subscription', cta: 'View' },
          ].map(({ icon: Icon, label, desc, href, cta }) => (
            <Link key={label} to={href}>
              <motion.div whileHover={{ y: -2 }} className="card-surface-hover p-5 rounded-xl space-y-3 h-full">
                <div className="flex items-center justify-between">
                  <div className="w-10 h-10 rounded-lg bg-gold-400/10 border border-gold-400/20 flex items-center justify-center">
                    <Icon className="w-5 h-5 text-gold-400" />
                  </div>
                  <ChevronRight className="w-4 h-4 text-stone-600 group-hover:text-gold-400" />
                </div>
                <div>
                  <p className="text-ivory-200 font-medium text-sm">{label}</p>
                  <p className="text-stone-500 text-xs mt-0.5">{desc}</p>
                </div>
                <span className="text-gold-400 text-xs font-medium">{cta} →</span>
              </motion.div>
            </Link>
          ))}
        </div>

        {/* Verification section */}
        <div className="card-surface p-6 rounded-2xl space-y-5">
          <div className="flex items-center justify-between">
            <h2 className="font-serif text-xl text-ivory-100">Verification Status</h2>
            <VerificationBadge level={escort.verification_level} size="md" showLabel />
          </div>

          <div className="space-y-3">
            {(() => {
              const blueTickSubscribed = !!(escort as any).blue_tick_stripe_subscription_id
              const blueTickApproved = escort.verification_level >= 3
              const identityApproved = escort.verification_level >= 2
              const identityPending = lastIdentity?.status === 'pending'
              const blueTickPending = blueTickSubscribed && !blueTickApproved && !blueTickRejected

              const rows = [
                {
                  level: 1, icon: Mail, label: 'Email Verified', desc: 'Confirm your email address',
                  done: escort.is_email_verified, pending: false, rejected: false, action: null,
                },
                {
                  level: 2, icon: ShieldCheck, label: 'Identity & Age Verified', desc: 'Submit a government ID and selfie',
                  done: identityApproved, pending: identityPending, rejected: identityRejected && !identityApproved,
                  action: '/dashboard/verify',
                },
                {
                  level: 3, icon: BadgeCheck, label: 'Blue Tick', desc: 'Prove your photos are genuine',
                  done: blueTickApproved, pending: blueTickPending, rejected: blueTickRejected,
                  action: '/dashboard/verify',
                },
              ]

              return rows.map(({ level, icon: Icon, label, desc, done, pending, rejected, action }) => (
                <div key={level} className={cn(
                  'flex items-center gap-4 p-4 rounded-xl border transition-colors',
                  done ? 'border-emerald-500/20 bg-emerald-500/5'
                    : rejected ? 'border-red-500/20 bg-red-500/5'
                    : pending ? 'border-amber-500/20 bg-amber-500/5'
                    : 'border-surface-border bg-surface'
                )}>
                  <div className={cn('w-10 h-10 rounded-full border flex items-center justify-center shrink-0',
                    done ? 'bg-emerald-500/10 border-emerald-500/30'
                      : rejected ? 'bg-red-500/10 border-red-500/30'
                      : pending ? 'bg-amber-500/10 border-amber-500/30'
                      : 'bg-surface-border border-surface-border'
                  )}>
                    {rejected
                      ? <XCircle className="w-5 h-5 text-red-400" />
                      : <Icon className={cn('w-5 h-5', done ? 'text-emerald-400' : pending ? 'text-amber-400' : 'text-stone-600')} />
                    }
                  </div>
                  <div className="flex-1">
                    <p className={cn('text-sm font-medium',
                      done ? 'text-emerald-300' : rejected ? 'text-red-300' : pending ? 'text-amber-300' : 'text-ivory-300'
                    )}>{label}</p>
                    <p className="text-stone-500 text-xs">{desc}</p>
                  </div>
                  {done ? (
                    <span className="text-emerald-400 text-xs font-medium">Complete</span>
                  ) : rejected ? (
                    <Link to={action ?? '#'}>
                      <Button variant="outline-gold" size="sm">Re-apply →</Button>
                    </Link>
                  ) : pending ? (
                    <span className="text-amber-400 text-xs font-medium">Pending review</span>
                  ) : action && escort.is_email_verified ? (
                    <Link to={action}>
                      <Button variant="outline-gold" size="sm">Submit</Button>
                    </Link>
                  ) : null}
                </div>
              ))
            })()}
          </div>
        </div>

        {/* Referral Code */}
        {(escort as any).referral_code && (
          <div className="card-surface p-6 rounded-2xl space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gold-400/10 border border-gold-400/20 flex items-center justify-center shrink-0">
                <Gift className="w-5 h-5 text-gold-400" />
              </div>
              <div>
                <h2 className="font-serif text-xl text-ivory-100">Your Referral Code</h2>
                <p className="text-stone-500 text-xs mt-0.5">Share with other companions to earn rewards</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex-1 flex items-center justify-center bg-surface border border-surface-border rounded-xl px-6 py-4">
                <span className="font-mono text-2xl font-bold tracking-[0.2em] gold-text">
                  {(escort as any).referral_code}
                </span>
              </div>
              <button
                onClick={() => {
                  navigator.clipboard.writeText((escort as any).referral_code)
                  setCodeCopied(true)
                  setTimeout(() => setCodeCopied(false), 2000)
                }}
                className="flex items-center gap-2 px-4 py-4 rounded-xl border border-surface-border bg-surface hover:border-gold-400/40 hover:text-gold-400 text-stone-400 transition-all text-sm font-medium whitespace-nowrap"
              >
                {codeCopied ? <><Check className="w-4 h-4 text-emerald-400" /> Copied!</> : <><Copy className="w-4 h-4" /> Copy</>}
              </button>
            </div>

            <div className="grid sm:grid-cols-2 gap-3 text-sm">
              <div className="p-3 rounded-xl bg-surface border border-surface-border">
                <p className="text-ivory-300 font-medium text-xs mb-1">Their reward</p>
                <p className="text-stone-400 text-xs">New escorts who use your code get <span className="text-gold-400 font-semibold">50% off for 3 months</span></p>
              </div>
              <div className="p-3 rounded-xl bg-surface border border-surface-border">
                <p className="text-ivory-300 font-medium text-xs mb-1">Your reward</p>
                <p className="text-stone-400 text-xs">You earn <span className="text-gold-400 font-semibold">1 free month</span> of your plan when they make their first payment</p>
              </div>
            </div>

            <p className="text-stone-600 text-xs text-center">
              Share your code on social media, WhatsApp, or anywhere companions gather in London
            </p>
          </div>
        )}

        {/* Profile preview link */}
        {escort.slug && escort.is_email_verified && (
          <div className="text-center">
            <Link to={`/escorts/${escort.slug}`} target="_blank" rel="noopener noreferrer">
              <Button variant="ghost">View my public profile →</Button>
            </Link>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
