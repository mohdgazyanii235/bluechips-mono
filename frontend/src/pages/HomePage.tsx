import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Search, BadgeCheck, ShieldCheck, Star, ChevronRight, Users, Eye, Award } from 'lucide-react'
import { HelmetProvider, Helmet } from 'react-helmet-async'
import { Layout } from '@/components/layout/Layout'
import { EscortGrid } from '@/components/escort/EscortGrid'
import { Button } from '@/components/ui/Button'
import { useEscorts } from '@/hooks/useEscorts'
import { useBoroughs } from '@/hooks/useBoroughs'
import { cn } from '@/utils/cn'

const PREMIUM_BOROUGHS = ['mayfair', 'kensington', 'chelsea', 'knightsbridge', 'belgravia', 'covent-garden', 'south-kensington', 'marylebone']

function HeroSection() {
  const [query, setQuery] = useState('')
  const navigate = useNavigate()

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) navigate(`/escorts?q=${encodeURIComponent(query)}`)
    else navigate('/escorts')
  }

  return (
    <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden">
      {/* Ambient background */}
      <div className="absolute inset-0 bg-black">
        <div className="absolute inset-0 bg-gradient-to-br from-gold-900/8 via-transparent to-gold-900/5" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-gold-400/3 blur-[120px] rounded-full" />
      </div>

      <div className="relative page-container text-center space-y-10 py-20">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="space-y-4"
        >
          {/* Premium label */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-gold-400/20 bg-gold-400/5 text-gold-400 text-xs uppercase tracking-widest font-medium mb-2">
            <span className="w-1.5 h-1.5 rounded-full bg-gold-400" />
            London's Premium Companion Directory
          </div>

          <h1 className="font-serif text-5xl sm:text-6xl lg:text-7xl xl:text-8xl text-ivory-100 leading-[1.05] tracking-tight">
            Discover{' '}
            <span className="gold-text">London's</span>
            <br />
            Finest Companions
          </h1>

          <p className="text-stone-400 text-lg sm:text-xl max-w-2xl mx-auto leading-relaxed">
            Verified, discreet, and exceptional. Browse independent companion listings
            across every London borough.
          </p>
        </motion.div>

        {/* Search */}
        <motion.form
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          onSubmit={handleSearch}
          className="max-w-xl mx-auto"
        >
          <div className="relative flex items-center">
            <Search className="absolute left-4 w-5 h-5 text-stone-500 pointer-events-none" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by name or browse below..."
              className="w-full bg-surface/80 backdrop-blur-md border border-surface-border rounded-xl pl-12 pr-32 py-4 text-ivory-200 placeholder-stone-600 focus:outline-none focus:border-gold-400/60 text-sm transition-colors"
            />
            <button
              type="submit"
              className="absolute right-2 btn-gold py-2 px-5 text-sm rounded-lg"
            >
              Search
            </button>
          </div>
        </motion.form>

        {/* Quick stats */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="flex items-center justify-center gap-8 text-sm"
        >
          {[
            { icon: Users, label: 'Active Companions', value: '500+' },
            { icon: BadgeCheck, label: 'Blue Tick Verified', value: '120+' },
            { icon: Eye, label: 'Monthly Visitors', value: '25k+' },
          ].map(({ icon: Icon, label, value }) => (
            <div key={label} className="text-center space-y-0.5">
              <p className="font-serif text-2xl gold-text">{value}</p>
              <p className="text-stone-600 text-xs">{label}</p>
            </div>
          ))}
        </motion.div>

        {/* Scroll hint */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.8 }}
          className="flex justify-center pt-4"
        >
          <div className="flex flex-col items-center gap-1">
            <div className="w-px h-8 bg-gradient-to-b from-transparent to-gold-400/40" />
            <span className="text-stone-600 text-xs uppercase tracking-widest">Browse</span>
          </div>
        </motion.div>
      </div>
    </section>
  )
}

function BoroughsSection({ boroughs }: { boroughs: any[] }) {
  const premium = boroughs.filter((b) => b.is_premium_area).slice(0, 8)
  const others = boroughs.filter((b) => !b.is_premium_area).slice(0, 8)

  return (
    <section className="py-20">
      <div className="page-container space-y-12">
        <div className="flex items-end justify-between">
          <div>
            <h2 className="section-title">Browse by Area</h2>
            <p className="section-subtitle">Explore companions across every London borough</p>
          </div>
          <Link to="/areas" className="hidden sm:flex items-center gap-1 text-gold-400 text-sm hover:text-gold-300 transition-colors">
            View all areas <ChevronRight className="w-4 h-4" />
          </Link>
        </div>

        {/* Premium boroughs */}
        <div>
          <p className="text-xs uppercase tracking-widest text-gold-500/70 font-medium mb-4">Premium Areas</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            {premium.map((borough) => (
              <Link key={borough.slug} to={`/escorts?borough_slug=${borough.slug}`}>
                <div className="group card-surface-hover p-4 rounded-xl">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-serif text-base text-ivory-200 group-hover:text-gold-400 transition-colors">{borough.name}</p>
                      <p className="text-stone-600 text-xs mt-0.5">{borough.escort_count} companions</p>
                    </div>
                    <div className="w-6 h-6 rounded-full bg-gold-400/10 border border-gold-400/20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                      <ChevronRight className="w-3 h-3 text-gold-400" />
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Other boroughs */}
        <div>
          <p className="text-xs uppercase tracking-widest text-stone-600 font-medium mb-4">More Areas</p>
          <div className="flex flex-wrap gap-2">
            {others.map((b) => (
              <Link key={b.slug} to={`/escorts?borough_slug=${b.slug}`}>
                <span className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full border border-surface-border text-stone-400 text-sm hover:border-gold-400/40 hover:text-ivory-200 transition-all">
                  {b.name}
                  <span className="text-stone-600 text-xs">({b.escort_count})</span>
                </span>
              </Link>
            ))}
            <Link to="/areas">
              <span className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full border border-gold-400/30 text-gold-400 text-sm hover:bg-gold-400/10 transition-all">
                View all <ChevronRight className="w-3 h-3" />
              </span>
            </Link>
          </div>
        </div>
      </div>
    </section>
  )
}

function TrustSection() {
  const pillars = [
    {
      icon: BadgeCheck,
      title: 'Blue Tick — Know Before You Go',
      description: 'Look for the Blue Tick. It means a companion\'s photos have been verified as genuinely theirs by our team. Who you see is exactly who you\'ll meet — no exceptions.',
      color: 'text-blue-400',
      bg: 'bg-blue-500/10 border-blue-500/20',
    },
    {
      icon: ShieldCheck,
      title: 'Real People, Real Photos',
      description: 'Every Blue Tick companion has submitted government-issued ID and a live selfie matching their profile pictures. We check, so you never have to wonder.',
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10 border-emerald-500/20',
    },
    {
      icon: Star,
      title: 'Independent, Not an Agency',
      description: 'Every companion on Bluechips is self-employed. We are a directory only — no middlemen, no hidden fees, no cut taken from anything.',
      color: 'text-gold-400',
      bg: 'bg-gold-400/10 border-gold-400/20',
    },
    {
      icon: Award,
      title: 'Premium Standard',
      description: 'We hold companions to high standards before approving their listings. You\'re browsing London\'s most curated, quality-focused companion directory.',
      color: 'text-ivory-300',
      bg: 'bg-stone-500/10 border-stone-500/20',
    },
  ]

  return (
    <section className="py-20 border-y border-surface-border bg-surface/30">
      <div className="page-container">
        <div className="text-center mb-14">
          <h2 className="section-title">Why Bluechips London</h2>
          <p className="section-subtitle mx-auto">
            The only directory built around trust, verification, and a premium experience for both companions and clients.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {pillars.map(({ icon: Icon, title, description, color, bg }) => (
            <div key={title} className="card-surface p-6 rounded-xl space-y-4">
              <div className={cn('w-12 h-12 rounded-xl border flex items-center justify-center', bg)}>
                <Icon className={cn('w-6 h-6', color)} />
              </div>
              <h3 className="font-serif text-lg text-ivory-100">{title}</h3>
              <p className="text-stone-500 text-sm leading-relaxed">{description}</p>
            </div>
          ))}
        </div>

        {/* Legal clarity */}
        <div className="mt-10 p-5 rounded-xl border border-stone-800 bg-stone-900/20 text-center">
          <p className="text-stone-500 text-sm leading-relaxed max-w-3xl mx-auto">
            <strong className="text-stone-400">Transparency first:</strong> Bluechips London is a marketing directory for independent adult entertainers based in London. We are not an escort agency. We do not employ, manage, or represent any companion listed on this platform. All arrangements and payments happen exclusively between clients and companions.
          </p>
        </div>
      </div>
    </section>
  )
}

function JoinSection() {
  return (
    <section className="py-24">
      <div className="page-container">
        <div className="relative rounded-2xl overflow-hidden border border-gold-400/20 bg-gradient-to-br from-gold-900/20 via-surface-card to-surface-card p-10 lg:p-16">
          <div className="absolute top-0 right-0 w-[400px] h-[400px] bg-gold-400/5 blur-[100px] rounded-full -translate-y-1/2 translate-x-1/4" />

          <div className="relative grid lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-gold-400/20 bg-gold-400/5 text-gold-400 text-xs uppercase tracking-widest">
                For Companions
              </div>
              <h2 className="font-serif text-4xl lg:text-5xl text-ivory-100 leading-tight">
                Earn more.<br />
                <span className="gold-text">List yourself</span><br />
                on Bluechips.
              </h2>
              <p className="text-stone-400 leading-relaxed">
                Get discovered by London's most discerning clients. Simple pricing, no hidden fees,
                and full control over your profile. Free to join — upgrade when you're ready.
              </p>
              <div className="flex flex-col sm:flex-row gap-3">
                <Link to="/join">
                  <Button variant="gold" size="lg">List Your Profile — Free</Button>
                </Link>
                <Link to="/join#pricing">
                  <Button variant="ghost" size="lg">View Pricing</Button>
                </Link>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              {[
                { label: 'Free forever', desc: 'Basic listing with 3 photos' },
                { label: '£11.99/mo', desc: 'Essential — more visibility' },
                { label: '£18.99/mo', desc: 'Premium — featured placement' },
                { label: '£23.99/mo', desc: 'Elite — top of every search' },
              ].map(({ label, desc }) => (
                <div key={label} className="p-4 rounded-xl bg-surface border border-surface-border space-y-1">
                  <p className="font-serif text-gold-400 text-lg">{label}</p>
                  <p className="text-stone-500 text-xs">{desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export function HomePage() {
  const { data: escortsData, isLoading } = useEscorts({ per_page: 10, page: 1 })
  const { data: boroughs = [] } = useBoroughs()

  return (
    <Layout>
      <Helmet>
        <title>Bluechips London — Premium Companion Directory</title>
        <meta name="description" content="London's most exclusive companion marketing directory. Browse verified, independent companion listings across all London boroughs. Discreet. Premium. Trusted." />
      </Helmet>

      <HeroSection />

      {/* Featured companions */}
      <section className="py-16">
        <div className="page-container space-y-8">
          <div className="flex items-end justify-between">
            <div>
              <h2 className="section-title">Featured Companions</h2>
              <p className="section-subtitle">Our most sought-after, verified profiles</p>
            </div>
            <Link to="/escorts" className="hidden sm:flex items-center gap-1 text-gold-400 text-sm hover:text-gold-300 transition-colors">
              Browse all <ChevronRight className="w-4 h-4" />
            </Link>
          </div>
          <EscortGrid escorts={escortsData?.items ?? []} loading={isLoading} skeletonCount={10} />
          <div className="text-center pt-4">
            <Link to="/escorts">
              <Button variant="outline-gold" size="lg">View All Companions</Button>
            </Link>
          </div>
        </div>
      </section>

      <BoroughsSection boroughs={boroughs} />
      <TrustSection />
      <JoinSection />
    </Layout>
  )
}
