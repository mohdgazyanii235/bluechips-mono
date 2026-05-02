import { Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { motion } from 'framer-motion'
import { BadgeCheck, ShieldCheck, Eye, Zap, Star, Crown, Check, ChevronRight } from 'lucide-react'
import { Layout } from '@/components/layout/Layout'
import { Button } from '@/components/ui/Button'

const PLANS = [
  { name: 'Free', price: 0, features: ['3 photos', 'Basic searchable listing', 'Phone & WhatsApp shown', 'Email verification'] },
  { name: 'Essential', price: 1199, icon: Zap, popular: false, features: ['8 photos', 'Identity verified badge', 'Borough search placement', '"Available now" indicator', '+ All Free features'] },
  { name: 'Premium', price: 1899, icon: Star, popular: true, features: ['50 photos', 'Featured search placement', 'Blue Tick included free', 'STD tested badge', '+ All Essential features'] },
  { name: 'Elite', price: 2399, icon: Crown, popular: false, features: ['Homepage rotation', 'Top of all results', 'Elite badge', 'Blue Tick included free', '+ All Premium features'] },
]

export function JoinPage() {
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
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-gold-400/20 bg-gold-400/5 text-gold-400 text-xs uppercase tracking-widest">
              Join 500+ companions
            </div>
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
            {PLANS.map((plan, i) => {
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
                        {plan.price === 0 ? 'Free' : `£${(plan.price / 100).toFixed(2)}`}
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
