import { Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { BadgeCheck, ShieldCheck, Eye, Zap, Star, Crown, Check, ChevronRight, Sparkles } from 'lucide-react'
import { Layout } from '@/components/layout/Layout'
import { Button } from '@/components/ui/Button'
import { apiClient } from '@/api/client'
import { foundingApi } from '@/api/founding'

type Pricing = {
  essential_monthly_pence: number
  premium_monthly_pence: number
  elite_monthly_pence: number
  blue_tick_setup_pence: number
  blue_tick_monthly_pence: number
}

const DEFAULT_PRICING: Pricing = {
  essential_monthly_pence: 1199,
  premium_monthly_pence: 1899,
  elite_monthly_pence: 2399,
  blue_tick_setup_pence: 1000,
  blue_tick_monthly_pence: 399,
}

const fmt = (pence: number) => `£${(pence / 100).toFixed(2)}`

export function JoinPage() {
  const { data: pricing = DEFAULT_PRICING } = useQuery<Pricing>({
    queryKey: ['pricing'],
    queryFn: () => apiClient.get('/pricing').then(r => r.data),
    staleTime: 5 * 60 * 1000,
  })

  const { data: founding } = useQuery({
    queryKey: ['founding-status'],
    queryFn: foundingApi.status,
    refetchInterval: 30_000,
  })

  const plans = [
    { name: 'Free', price: 0, features: ['3 photos', 'Basic searchable listing', 'Phone & WhatsApp shown', 'Email verification'] },
    { name: 'Essential', price: pricing.essential_monthly_pence, icon: Zap, popular: false, features: ['8 photos', 'Identity verified badge', 'Borough search placement', '"Available now" indicator', '+ All Free features'] },
    { name: 'Premium', price: pricing.premium_monthly_pence, icon: Star, popular: true, features: ['50 photos', 'Featured search placement', 'Blue Tick included free', 'STD tested badge', '+ All Essential features'] },
    { name: 'Elite', price: pricing.elite_monthly_pence, icon: Crown, popular: false, features: ['Homepage rotation', 'Top of all results', 'Elite badge', 'Blue Tick included free', '+ All Premium features'] },
  ]

  const foundingActive = founding?.active && founding.remaining > 0

  return (
    <Layout>
      <Helmet>
        <title>List Your Profile — Join Bluechips London</title>
        <meta name="description" content="Join Bluechips London, London's most exclusive companion directory. Free to start. Upgrade for more visibility and clients." />
      </Helmet>

      {/* Hero */}
      <section className="py-20 text-center">
        <div className="page-container max-w-3xl space-y-6">
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
            {foundingActive && (
              <Link
                to="/founding-50"
                className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-gold-400/30 bg-gold-400/5 text-gold-400 text-xs uppercase tracking-widest hover:bg-gold-400/10 transition-colors"
              >
                <Crown className="w-3.5 h-3.5" />
                Founding {founding.limit} — {founding.remaining} spots left
              </Link>
            )}
            <h1 className="font-serif text-5xl lg:text-6xl text-ivory-100 leading-tight">
              Market yourself on<br />
              <span className="gold-text">London's finest</span> directory
            </h1>
            <p className="text-stone-400 text-lg leading-relaxed max-w-xl mx-auto">
              Free to join. No agency fees. No commission. You keep everything you earn.
              Upgrade whenever you're ready.
            </p>
          </motion.div>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link to="/register">
              <Button variant="gold" size="lg">Start for Free — No Card Needed</Button>
            </Link>
            <a href="#pricing">
              <Button variant="ghost" size="lg">View Pricing <ChevronRight className="w-4 h-4" /></Button>
            </a>
          </div>
        </div>
      </section>

      {/* Founding counter (only while active) */}
      {foundingActive && (
        <section className="pb-8">
          <div className="page-container max-w-2xl">
            <Link to="/founding-50" className="block group">
              <div className="bg-gradient-to-br from-gold-900/20 via-stone-900 to-stone-900 border border-gold-400/20 hover:border-gold-400/40 rounded-2xl p-6 transition-colors">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-gold-400/10 border border-gold-400/20 flex items-center justify-center shrink-0">
                    <Sparkles className="w-5 h-5 text-gold-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs uppercase tracking-widest text-gold-500 mb-1">Founding Programme</p>
                    <p className="text-ivory-100 text-sm">
                      <strong>{founding.signups}/{founding.limit} spots taken.</strong>{' '}
                      <span className="text-stone-400">First {founding.limit} companions get {founding.duration_months} months free + lifetime discount.</span>
                    </p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-gold-400 group-hover:translate-x-0.5 transition-transform" />
                </div>
                <div className="mt-4 h-2 bg-stone-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-gold-500 to-gold-300 transition-all duration-700"
                    style={{ width: `${Math.round((founding.signups / Math.max(1, founding.limit)) * 100)}%` }}
                  />
                </div>
              </div>
            </Link>
          </div>
        </section>
      )}

      {/* Why join */}
      <section className="py-16 border-y border-surface-border bg-surface/20">
        <div className="page-container">
          <div className="grid sm:grid-cols-3 gap-8 max-w-3xl mx-auto">
            {[
              { icon: Eye, title: 'Your privacy, protected', desc: 'You choose your stage name. Your real identity is never displayed to the public.' },
              { icon: ShieldCheck, title: 'You are in control', desc: 'Edit, pause, or delete your profile whenever you want. No contracts. No commitments.' },
              { icon: BadgeCheck, title: 'Get the Blue Tick', desc: 'Verified profiles get significantly more contact requests. The process is free.' },
            ].map(({ icon: Icon, title, desc }) => (
              <div key={title} className="text-center space-y-3">
                <div className="flex justify-center">
                  <div className="w-12 h-12 rounded-xl bg-gold-400/10 border border-gold-400/20 flex items-center justify-center">
                    <Icon className="w-6 h-6 text-gold-400" />
                  </div>
                </div>
                <h3 className="font-serif text-lg text-ivory-100">{title}</h3>
                <p className="text-stone-500 text-sm leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-20">
        <div className="page-container space-y-10">
          <div className="text-center">
            <h2 className="font-serif text-4xl text-ivory-100">Simple, Honest Pricing</h2>
            <p className="text-stone-500 mt-3">No hidden fees. Cancel anytime. One clear monthly price.</p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {plans.map((plan, i) => {
              const Icon = plan.icon
              return (
                <motion.div
                  key={plan.name}
                  initial={{ opacity: 0, y: 16 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.08 }}
                  className={`card-surface rounded-2xl p-6 space-y-6 relative ${plan.popular ? 'border-gold-400/40 shadow-gold' : ''}`}
                >
                  {plan.popular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gold-400 text-black text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-wide">
                      Most Popular
                    </div>
                  )}
                  <div className="space-y-2">
                    {Icon && (
                      <div className="w-8 h-8 rounded-lg bg-gold-400/10 flex items-center justify-center mb-2">
                        <Icon className="w-4 h-4 text-gold-400" />
                      </div>
                    )}
                    <h3 className="font-serif text-xl text-ivory-100">{plan.name}</h3>
                    <div className="flex items-baseline gap-1">
                      <span className="font-serif text-3xl text-gold-400">
                        {plan.price === 0 ? 'Free' : fmt(plan.price)}
                      </span>
                      {plan.price > 0 && <span className="text-stone-500 text-sm">/mo</span>}
                    </div>
                  </div>
                  <ul className="space-y-2.5">
                    {plan.features.map((f) => (
                      <li key={f} className="flex items-start gap-2 text-sm">
                        <Check className="w-4 h-4 text-gold-400 shrink-0 mt-0.5" />
                        <span className="text-stone-300">{f}</span>
                      </li>
                    ))}
                  </ul>
                  <Link to="/register">
                    <Button variant={plan.popular ? 'gold' : 'outline-gold'} fullWidth>
                      {plan.price === 0 ? 'Start Free' : `Get ${plan.name}`}
                    </Button>
                  </Link>
                </motion.div>
              )
            })}
          </div>
        </div>
      </section>

      {/* Verification section */}
      <section id="verification" className="py-20 border-t border-surface-border bg-surface/20">
        <div className="page-container max-w-3xl space-y-10">
          <div className="text-center space-y-3">
            <h2 className="font-serif text-4xl text-ivory-100">Get Your Blue Tick — Free</h2>
            <p className="text-stone-500 leading-relaxed">
              Verified profiles get significantly more views. The process is quick, free, and keeps everyone safe.
            </p>
          </div>

          <div className="space-y-4">
            {[
              { num: 1, title: 'Verify your email', desc: 'Confirm your email address after signup. Instant.' },
              { num: 2, title: 'Submit your ID', desc: 'Send us a photo of your government ID and a selfie holding a piece of paper with today\'s date. This confirms you are 18+ and real.' },
              { num: 3, title: 'Photo match', desc: 'Upload a selfie in the same pose as one of your profile photos. We compare them to confirm your photos are genuinely you.' },
              { num: 4, title: 'Review within 1 hour', desc: 'Our team reviews your submission. Once approved, your Blue Tick badge appears on your profile immediately.' },
            ].map(({ num, title, desc }) => (
              <div key={num} className="flex gap-5 p-5 card-surface rounded-xl">
                <div className="w-10 h-10 rounded-full bg-gold-400/10 border border-gold-400/30 flex items-center justify-center shrink-0 font-serif text-gold-400 text-lg">
                  {num}
                </div>
                <div>
                  <h3 className="font-medium text-ivory-200">{title}</h3>
                  <p className="text-stone-500 text-sm mt-0.5 leading-relaxed">{desc}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="text-center">
            <Link to="/register">
              <Button variant="gold" size="lg">Create Free Account</Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Legal clarity */}
      <section className="py-12">
        <div className="page-container max-w-2xl text-center space-y-3">
          <p className="text-stone-500 text-sm leading-relaxed">
            Bluechips London is a marketing and advertising directory for self-employed adult entertainers.
            By listing your profile, you confirm you are self-employed, 18+ years of age, and that you take
            full legal responsibility for the services you advertise. Bluechips London is not an escort agency,
            does not employ you, and does not handle any financial transactions between you and your clients.
          </p>
        </div>
      </section>
    </Layout>
  )
}
