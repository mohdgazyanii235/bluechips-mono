import { useQuery } from '@tanstack/react-query'
import { Helmet } from 'react-helmet-async'
import { Link } from 'react-router-dom'
import { Crown, BadgeCheck, Sparkles, ShieldCheck, Star, ArrowRight } from 'lucide-react'
import { Layout } from '@/components/layout/Layout'
import { foundingApi } from '@/api/founding'

const TIER_LABELS: Record<string, string> = {
  essential: 'Essential',
  premium: 'Premium',
  elite: 'Elite',
}

export function FoundingMembersPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['founding-status'],
    queryFn: foundingApi.status,
    refetchInterval: 30_000, // poll every 30s so the counter feels live
  })

  const filled = data ? Math.round((data.signups / Math.max(1, data.limit)) * 100) : 0

  if (!isLoading && data && !data.active) {
    return (
      <Layout>
        <Helmet>
          <title>Founding Member Programme — Bluechips London</title>
          <meta name="robots" content="noindex, follow" />
        </Helmet>
        <div className="page-container py-32 text-center max-w-xl space-y-6">
          <Crown className="w-12 h-12 mx-auto text-gold-400/40" />
          <h1 className="font-serif text-3xl text-ivory-100">Founding programme closed</h1>
          <p className="text-stone-500">All founding spots have been filled. Browse our directory or list your profile on a standard plan.</p>
          <div className="flex items-center justify-center gap-3">
            <Link to="/escorts" className="px-5 py-2.5 rounded-lg bg-gold-400 text-black font-semibold hover:bg-gold-300 text-sm">Browse companions</Link>
            <Link to="/join" className="px-5 py-2.5 rounded-lg border border-gold-400/30 text-gold-400 hover:bg-gold-400/10 text-sm">List your profile</Link>
          </div>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <Helmet>
        <title>{data ? `Founding ${data.limit} — ${data.remaining} spots left | Bluechips London` : 'Founding Members — Bluechips London'}</title>
        <meta name="description" content="Be one of the first to list on Bluechips London. Six months free, free Blue Tick verification, lifetime discount." />
        <link rel="canonical" href="https://bluechips.live/founding-50" />
      </Helmet>

      <section className="relative pt-20 pb-12">
        <div className="absolute inset-0 bg-gradient-to-b from-gold-900/10 via-transparent to-transparent pointer-events-none" />
        <div className="page-container relative space-y-10">
          <div className="text-center space-y-5 max-w-3xl mx-auto">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-gold-400/30 bg-gold-400/5 text-gold-400 text-xs uppercase tracking-widest font-medium">
              <Crown className="w-3.5 h-3.5" /> Founding Programme
            </div>
            <h1 className="font-serif text-5xl sm:text-6xl text-ivory-100 leading-[1.05] tracking-tight">
              The first <span className="gold-text">{data?.limit ?? 50}</span> companions<br />
              get something nobody else will.
            </h1>
            <p className="text-stone-400 text-lg leading-relaxed max-w-2xl mx-auto">
              We're handpicking the founding {data?.limit ?? 50} independent companions to launch Bluechips London. If you're one of them, here's what you get.
            </p>
          </div>

          {/* Live counter */}
          <div className="max-w-2xl mx-auto">
            <div className="bg-gradient-to-br from-gold-900/20 via-stone-900 to-stone-900 border border-gold-400/20 rounded-2xl p-8 space-y-5">
              <div className="flex items-baseline justify-between flex-wrap gap-2">
                <div>
                  <p className="text-xs uppercase tracking-widest text-gold-500">Founding spots</p>
                  <p className="font-serif text-5xl text-ivory-100 mt-1">
                    {data ? `${data.signups} / ${data.limit}` : '— / —'}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-stone-500 text-xs">Remaining</p>
                  <p className="font-serif text-3xl text-gold-400">{data?.remaining ?? '—'}</p>
                </div>
              </div>
              <div className="h-3 bg-stone-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-gold-500 to-gold-300 transition-all duration-700"
                  style={{ width: `${filled}%` }}
                />
              </div>
              <p className="text-stone-600 text-xs">Counter updates in real time. Once all spots are taken, the offer ends — no exceptions.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Offer breakdown */}
      <section className="py-12">
        <div className="page-container max-w-4xl space-y-8">
          <h2 className="font-serif text-3xl text-ivory-100 text-center">What founding members get</h2>

          <div className="grid sm:grid-cols-2 gap-4">
            <Perk
              icon={Sparkles}
              title={data ? `${data.duration_months} months free` : '6 months free'}
              body={data ? `Full ${TIER_LABELS[data.tier] ?? data.tier} tier on us. No card required upfront for the founding period.` : 'Full Premium tier on us.'}
            />
            <Perk
              icon={BadgeCheck}
              title={data?.includes_blue_tick ? 'Free Blue Tick verification' : 'Blue Tick add-on available'}
              body={data?.includes_blue_tick ? 'Skip the £10 setup fee. Your identity verification is included.' : 'Standard Blue Tick available as an add-on.'}
            />
            <Perk
              icon={Crown}
              title={data?.badge_label ?? 'Founding Member badge'}
              body="Permanent badge on your profile. Visible to clients. A signal you were here first."
            />
            <Perk
              icon={Star}
              title={data ? `${data.lifetime_discount_percent}% lifetime discount` : '50% lifetime discount'}
              body="After the founding period ends, you keep the discount on your subscription. Forever."
            />
            <Perk
              icon={ShieldCheck}
              title="Independent, no commission"
              body="Bluechips never sees, handles, or takes a cut of anything you earn from clients. Subscription fees only."
            />
            <Perk
              icon={Sparkles}
              title="Direct line to the founders"
              body="Founding members can reach the team directly with feedback, requests, or issues. We listen."
            />
          </div>
        </div>
      </section>

      {/* How to claim */}
      <section className="py-12 bg-stone-950/40 border-y border-surface-border">
        <div className="page-container max-w-3xl space-y-8">
          <h2 className="font-serif text-3xl text-ivory-100 text-center">How to claim your spot</h2>

          <ol className="space-y-5">
            <Step
              n={1}
              title="Get a personal code"
              body="Founding spots are by invitation. If we've reached out to you on X or via a partner, you'll already have a code that looks like FM-XXXXXX. If you haven't been contacted but think you should be, message us and we'll review."
            />
            <Step
              n={2}
              title="Register with the code"
              body="Sign up at /join — enter your code when prompted, or use the personalised link you were sent (the code applies automatically)."
            />
            <Step
              n={3}
              title="Verify your identity"
              body="Complete the standard ID verification. We review every submission manually — typically within an hour during business hours."
            />
            <Step
              n={4}
              title="Build your profile and go live"
              body="Upload your photos, set your rates, choose your areas. The moment you're approved, you're live — with full features unlocked and your founding badge displayed."
            />
          </ol>

          <div className="text-center pt-6">
            <Link
              to="/join"
              className="inline-flex items-center gap-2 bg-gold-400 hover:bg-gold-300 text-black font-semibold px-7 py-3 rounded-lg text-sm transition-colors"
            >
              Claim my founding spot
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-16">
        <div className="page-container max-w-2xl space-y-8">
          <h2 className="font-serif text-3xl text-ivory-100 text-center">Quick answers</h2>
          <div className="space-y-5">
            <Faq q="Do I have to give card details?">
              No — for the founding period there's no payment to make. After the free period ends, you'll be asked to set up payment, and that's when the lifetime discount kicks in.
            </Faq>
            <Faq q="What if I don't have a code?">
              Message us on X (we'll find you) or reply to whatever channel you saw this on. We're handpicking the founding cohort — if your profile fits, we'll send a code.
            </Faq>
            <Faq q="Is this really independent? No agency?">
              Bluechips is a directory only. We don't manage you, don't book on your behalf, and don't take any commission on what clients pay you. We are exactly Gumtree-for-companions, nothing more.
            </Faq>
            <Faq q={`What does the ${data ? `${data.lifetime_discount_percent}%` : '50%'} lifetime discount apply to?`}>
              Your subscription, forever, as long as you remain an active companion. If you leave and come back, the discount comes with you.
            </Faq>
          </div>
        </div>
      </section>
    </Layout>
  )
}

function Perk({ icon: Icon, title, body }: { icon: any; title: string; body: string }) {
  return (
    <div className="p-5 rounded-xl bg-stone-900 border border-surface-border hover:border-gold-400/20 transition-colors">
      <div className="w-10 h-10 rounded-lg bg-gold-400/10 border border-gold-400/20 flex items-center justify-center mb-3">
        <Icon className="w-5 h-5 text-gold-400" />
      </div>
      <h3 className="font-serif text-lg text-ivory-100 mb-1">{title}</h3>
      <p className="text-stone-500 text-sm leading-relaxed">{body}</p>
    </div>
  )
}

function Step({ n, title, body }: { n: number; title: string; body: string }) {
  return (
    <li className="flex gap-4">
      <div className="shrink-0 w-9 h-9 rounded-full bg-gold-400/10 border border-gold-400/30 text-gold-400 font-serif text-lg flex items-center justify-center">{n}</div>
      <div>
        <h3 className="font-serif text-lg text-ivory-100">{title}</h3>
        <p className="text-stone-500 text-sm leading-relaxed mt-0.5">{body}</p>
      </div>
    </li>
  )
}

function Faq({ q, children }: { q: string; children: React.ReactNode }) {
  return (
    <details className="group bg-stone-900/40 border border-surface-border rounded-xl p-5 open:bg-stone-900">
      <summary className="cursor-pointer flex items-center justify-between font-serif text-base text-ivory-200 hover:text-gold-400 transition-colors">
        {q}
        <span className="text-stone-500 group-open:rotate-180 transition-transform">▾</span>
      </summary>
      <p className="text-stone-500 text-sm mt-3 leading-relaxed">{children}</p>
    </details>
  )
}
