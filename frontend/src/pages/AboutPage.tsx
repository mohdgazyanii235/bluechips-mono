import { Helmet } from 'react-helmet-async'
import { Layout } from '@/components/layout/Layout'
import { Shield, BadgeCheck, Eye, Heart, Scale, Users } from 'lucide-react'

export function AboutPage() {
  return (
    <Layout>
      <Helmet>
        <title>About Bluechips London — What We Are & What We're Not</title>
        <meta name="description" content="Bluechips London is an independent advertising platform for adult companions in London, operating like Gumtree or Fiverr for self-employed entertainers. We are not an escort agency." />
      </Helmet>

      <div className="page-container py-16 max-w-3xl space-y-14">
        <div className="space-y-4">
          <h1 className="font-serif text-5xl text-ivory-100">About Bluechips London</h1>
          <p className="text-stone-400 text-lg leading-relaxed">
            An independent advertising platform for self-employed adult entertainers in London. Think Fiverr or Gumtree — for companionship services.
          </p>
        </div>

        <div className="space-y-6 text-stone-400 leading-relaxed">
          <h2 className="font-serif text-2xl text-ivory-100">What we are</h2>
          <p>
            Bluechips London is a technology platform where self-employed adult entertainers can advertise their
            companionship and time-based services to potential clients. We operate as a classified advertising
            directory — the same legal and commercial model as Gumtree, Fiverr, or advertising in a
            specialist magazine.
          </p>
          <p>
            We are a platform intermediary. We publish listings created and controlled entirely by independent
            self-employed individuals. We do not create, curate, or endorse any listing content. Each
            companion is solely responsible for the accuracy, legality, and conduct of their own listing and
            all arrangements made through it.
          </p>
          <p>
            Our companions set their own rates, manage their own availability, communicate directly with
            clients, and receive all payments directly into their own accounts. Bluechips London never
            sees, handles, holds, or takes any percentage of any payment that passes between a client and
            a companion.
          </p>
        </div>

        <div className="space-y-6 text-stone-400 leading-relaxed">
          <h2 className="font-serif text-2xl text-ivory-100">What we are not</h2>
          <div className="grid sm:grid-cols-2 gap-4">
            {[
              { icon: Shield, text: 'We are not an escort agency. We do not book, manage, represent, or employ any companion.' },
              { icon: Eye, text: 'We do not handle bookings. All contact and arrangements happen directly between client and companion.' },
              { icon: Heart, text: 'We do not take commission. Companions keep 100% of everything they earn.' },
              { icon: BadgeCheck, text: 'We do not guarantee any services. Companions self-declare what they offer.' },
              { icon: Users, text: 'We do not vet or screen clients on behalf of companions. Always screen clients yourself.' },
              { icon: Scale, text: 'We do not advise on the legality of specific services. Each individual is responsible for their own legal compliance.' },
            ].map(({ icon: Icon, text }) => (
              <div key={text} className="flex gap-3 p-4 card-surface rounded-xl">
                <Icon className="w-5 h-5 text-gold-400 shrink-0 mt-0.5" />
                <p className="text-sm">{text}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-6 text-stone-400 leading-relaxed">
          <h2 className="font-serif text-2xl text-ivory-100">Why we built this</h2>
          <p>
            The existing escort directory market is plagued with fake profiles, unresponsive platforms, extortionary
            pricing, and a complete disregard for the safety of both companions and clients.
          </p>
          <p>
            We built Bluechips London to do it properly: transparent pricing, rigorous photo verification to eliminate
            catfishing, a premium experience that attracts quality clients who pay fairly, and a platform that actually
            supports the companions who use it.
          </p>
        </div>

        <div className="p-6 rounded-xl border border-gold-400/20 bg-gold-900/10 space-y-4">
          <h3 className="font-serif text-xl text-ivory-100">Legal & Compliance</h3>
          <p className="text-stone-400 text-sm leading-relaxed">
            Escort advertising directories are completely legal in the United Kingdom. Escorting (paid companionship)
            is legal in England, Scotland, and Wales. Bluechips London operates as an advertising platform under the
            same legal framework as any classified advertising service.
          </p>
          <p className="text-stone-400 text-sm leading-relaxed">
            We comply with the <strong className="text-stone-300">UK Online Safety Act 2023</strong>, <strong className="text-stone-300">UK GDPR</strong> and the Data Protection Act 2018, and all applicable advertising regulations enforced by the Advertising Standards Authority. We maintain mechanisms for reporting illegal content and take action on any verified reports.
          </p>
          <p className="text-stone-400 text-sm leading-relaxed">
            All companions listed on this platform are adults who self-certify their age (18+) at registration. Paid subscribers undergo identity and age verification by our review team before their profile is activated.
          </p>
        </div>

        <div className="p-6 rounded-xl border border-stone-800 bg-stone-900/20 space-y-3">
          <h3 className="font-serif text-xl text-ivory-100">Platform Liability</h3>
          <p className="text-stone-500 text-sm leading-relaxed">
            Bluechips London is a technology platform and not the author, publisher, or endorser of any listing content. As a platform intermediary (analogous to Gumtree, Fiverr, or Airbnb), we are not liable for the accuracy of listings or for the conduct, services, or arrangements of the individuals who advertise on our platform. All arrangements are made between clients and companions on a private, direct, and voluntary basis. Users of this platform are solely responsible for ensuring their activities comply with applicable law.
          </p>
          <p className="text-stone-500 text-sm leading-relaxed">
            To report a profile or illegal content, use the Report button on the relevant listing or contact us at <a href="mailto:mohdgazyanii235@gmail.com" className="text-gold-400 hover:text-gold-300">mohdgazyanii235@gmail.com</a>.
          </p>
        </div>
      </div>
    </Layout>
  )
}
