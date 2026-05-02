import { Helmet } from 'react-helmet-async'
import { Layout } from '@/components/layout/Layout'
import { Shield, AlertTriangle, Phone, Heart } from 'lucide-react'

export function SafetyPage() {
  return (
    <Layout>
      <Helmet>
        <title>Safety & Trust — Bluechips London</title>
        <meta name="description" content="Safety information for clients and companions using Bluechips London. Our commitment to trust, verification, and safe interactions." />
      </Helmet>

      <div className="page-container py-16 max-w-3xl space-y-12">
        <div className="space-y-4">
          <h1 className="font-serif text-5xl text-ivory-100">Safety & Trust</h1>
          <p className="text-stone-400 text-lg leading-relaxed">
            We take the safety of everyone on our platform seriously. Here's how we help keep interactions safe.
          </p>
        </div>

        {[
          {
            icon: Shield,
            title: 'For Clients',
            items: [
              'Look for the Blue Tick — it means the companion\'s photos have been verified as genuine by our team.',
              'Look for the ID Verified badge — this means the companion has submitted government-issued ID.',
              'Never send money in advance via bank transfer or cash before meeting.',
              'Verify you are communicating with the companion directly, not a third party.',
              'Trust your instincts. If something feels off, walk away.',
              'Use the "Report a profile" button if you encounter a suspicious listing.',
            ],
          },
          {
            icon: Heart,
            title: 'For Companions',
            items: [
              'Screen your clients. You are entitled to decline any booking for any reason.',
              'Never share your home address publicly on your profile — use a general area only.',
              'Trust your instincts. Your safety always comes first.',
              'Keep a record of all client communications.',
              'Tell someone you trust where you are going for outcall appointments.',
              'Consider using a dedicated work phone number to protect your personal number.',
            ],
          },
          {
            icon: AlertTriangle,
            title: 'Reporting Concerns',
            items: [
              'Use the "Report a Profile" button on any listing page to flag suspicious content.',
              'If you suspect exploitation or trafficking, contact the Modern Slavery Helpline: 0800 0121 700.',
              'For emergencies, always call 999.',
              'National Ugly Mugs (NUM) provides safety resources and bad client reports for sex workers: uknswp.org',
            ],
          },
        ].map(({ icon: Icon, title, items }) => (
          <section key={title} className="space-y-5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gold-400/10 border border-gold-400/20 flex items-center justify-center">
                <Icon className="w-5 h-5 text-gold-400" />
              </div>
              <h2 className="font-serif text-2xl text-ivory-100">{title}</h2>
            </div>
            <ul className="space-y-3">
              {items.map((item) => (
                <li key={item} className="flex gap-3 text-stone-400 text-sm leading-relaxed">
                  <span className="text-gold-400 mt-0.5 shrink-0">—</span>
                  {item}
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </Layout>
  )
}
