import { Helmet } from 'react-helmet-async'
import { Layout } from '@/components/layout/Layout'

export function TermsPage() {
  return (
    <Layout>
      <Helmet>
        <title>Terms of Service — Bluechips London</title>
        <meta name="description" content="Bluechips London terms of service. Rules, conditions, and legal basis for using our platform as a client or companion." />
        <link rel="canonical" href="https://bluechips.live/terms" />
        <meta name="robots" content="noindex, follow" />
      </Helmet>

      <div className="page-container py-16 max-w-3xl space-y-10">
        <div className="space-y-3">
          <h1 className="font-serif text-4xl text-ivory-100">Terms of Service</h1>
          <p className="text-stone-500 text-sm">Last updated: May 2025</p>
        </div>

        <div className="space-y-8 text-stone-400 leading-relaxed">
          <section className="space-y-4">
            <h2 className="font-serif text-xl text-ivory-200">1. Acceptance</h2>
            <p>
              By accessing or using Bluechips London ("the Platform", "we", "us"), you agree to be bound by these Terms. If you do not agree, do not use the Platform.
            </p>
            <p>
              You must be 18 years of age or older to use this Platform. By using it, you confirm you are 18+.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="font-serif text-xl text-ivory-200">2. Platform Nature</h2>
            <p>
              Bluechips London is a <strong className="text-stone-300">technology advertising platform</strong> — an intermediary directory where self-employed adult entertainers advertise their services. We are not an escort agency. We do not employ, represent, manage, or provide any companion. We have no involvement in any arrangement or payment between clients and companions.
            </p>
            <p>
              All listings are created and controlled solely by self-employed individuals. Each companion is independently responsible for the accuracy, legality, and conduct of their listing and all arrangements made through it.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="font-serif text-xl text-ivory-200">3. Companion Accounts</h2>
            <p>By creating a companion account, you agree that:</p>
            <ul className="list-disc list-inside space-y-1.5 text-stone-500">
              <li>You are at least 18 years of age</li>
              <li>You are self-employed and operate independently</li>
              <li>All content, photos, and information you provide are accurate and you hold all necessary rights</li>
              <li>You will not use the Platform to facilitate anything unlawful under UK law</li>
              <li>You are responsible for all tax and legal obligations arising from your activities</li>
            </ul>
          </section>

          <section className="space-y-4">
            <h2 className="font-serif text-xl text-ivory-200">4. Subscriptions & Payments</h2>
            <p>
              Subscription fees are charged monthly or annually in advance. All fees are in GBP and include VAT where applicable. Subscriptions automatically renew unless cancelled before the renewal date.
            </p>
            <p>
              Refunds are only issued in cases of verification denial (where a refund is processed automatically) or at our sole discretion. Partial refunds for unused subscription time are not provided.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="font-serif text-xl text-ivory-200">5. Prohibited Content</h2>
            <p>You must not post content that:</p>
            <ul className="list-disc list-inside space-y-1.5 text-stone-500">
              <li>Involves or depicts anyone under 18 years of age</li>
              <li>Is fraudulent, misleading, or impersonates another person</li>
              <li>Violates any applicable UK law</li>
              <li>Contains malware, spam, or unsolicited communications</li>
            </ul>
            <p>We reserve the right to remove any content and terminate any account that breaches these terms, without notice or refund.</p>
          </section>

          <section className="space-y-4">
            <h2 className="font-serif text-xl text-ivory-200">6. Client Use</h2>
            <p>
              Clients using this Platform to browse listings do so for personal, private purposes only. You agree not to scrape, harvest, or systematically collect data from the Platform. You agree not to contact companions for any purpose other than genuine personal inquiry.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="font-serif text-xl text-ivory-200">7. Limitation of Liability</h2>
            <p>
              To the fullest extent permitted by law, Bluechips London is not liable for any loss, damage, injury, or harm arising from: the conduct of any companion or client; the accuracy or completeness of any listing; or any arrangement, transaction, or interaction between a client and companion.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="font-serif text-xl text-ivory-200">8. Governing Law</h2>
            <p>
              These Terms are governed by the laws of England and Wales. Any disputes shall be subject to the exclusive jurisdiction of the courts of England and Wales.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="font-serif text-xl text-ivory-200">9. Contact</h2>
            <p>
              For any questions regarding these Terms, contact:{' '}
              <a href="mailto:mohdgazyanii235@gmail.com" className="text-gold-400 hover:text-gold-300">
                mohdgazyanii235@gmail.com
              </a>
            </p>
          </section>
        </div>
      </div>
    </Layout>
  )
}
