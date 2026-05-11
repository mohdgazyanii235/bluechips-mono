import { Helmet } from 'react-helmet-async'
import { Layout } from '@/components/layout/Layout'

export function PrivacyPage() {
  return (
    <Layout>
      <Helmet>
        <title>Privacy Policy — Bluechips London</title>
        <meta name="description" content="Bluechips London privacy policy. How we collect, use, and protect your personal data in compliance with UK GDPR and the Data Protection Act 2018." />
        <link rel="canonical" href="https://bluechips.live/privacy" />
        <meta name="robots" content="noindex, follow" />
      </Helmet>

      <div className="page-container py-16 max-w-3xl space-y-10">
        <div className="space-y-3">
          <h1 className="font-serif text-4xl text-ivory-100">Privacy Policy</h1>
          <p className="text-stone-500 text-sm">Last updated: May 2025</p>
        </div>

        <div className="prose-custom space-y-8 text-stone-400 leading-relaxed">
          <section className="space-y-4">
            <h2 className="font-serif text-xl text-ivory-200">1. Who We Are</h2>
            <p>
              Bluechips London operates the website at <strong className="text-stone-300">bluechips.live</strong>. We are a UK-based technology platform providing advertising services to self-employed adult entertainers. We are not an escort agency.
            </p>
            <p>
              For data protection purposes, Bluechips London is the data controller for personal data collected on this platform.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="font-serif text-xl text-ivory-200">2. Data We Collect</h2>
            <p>We collect the following categories of personal data:</p>
            <ul className="list-disc list-inside space-y-1.5 text-stone-500">
              <li><strong className="text-stone-400">Account data</strong> — email address, encrypted password, stage name</li>
              <li><strong className="text-stone-400">Profile data</strong> — age, borough, physical attributes, rates, photos, about text</li>
              <li><strong className="text-stone-400">Identity documents</strong> — government-issued ID and selfie photos (paid subscribers only, for verification)</li>
              <li><strong className="text-stone-400">Payment data</strong> — processed by Stripe; we store only the Stripe customer ID, not card details</li>
              <li><strong className="text-stone-400">Usage data</strong> — profile view counts, contact click counts, last-seen timestamps</li>
              <li><strong className="text-stone-400">Technical data</strong> — IP address (used for rate limiting, not stored long-term)</li>
            </ul>
          </section>

          <section className="space-y-4">
            <h2 className="font-serif text-xl text-ivory-200">3. How We Use Your Data</h2>
            <ul className="list-disc list-inside space-y-1.5 text-stone-500">
              <li>To create and manage your companion listing</li>
              <li>To process subscription payments via Stripe</li>
              <li>To verify your identity for Blue Tick or paid tier approval</li>
              <li>To send you transactional emails (account, payment, verification status)</li>
              <li>To prevent fraud and abuse of the platform</li>
            </ul>
          </section>

          <section className="space-y-4">
            <h2 className="font-serif text-xl text-ivory-200">4. Data Retention</h2>
            <p>
              We retain your account data for as long as your account is active. Identity documents submitted for verification are retained for a maximum of 90 days after the review is completed, then deleted. Payment records are retained for 7 years as required by UK law.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="font-serif text-xl text-ivory-200">5. Your Rights (UK GDPR)</h2>
            <p>Under the UK General Data Protection Regulation (UK GDPR), you have the right to:</p>
            <ul className="list-disc list-inside space-y-1.5 text-stone-500">
              <li>Access the personal data we hold about you</li>
              <li>Correct inaccurate personal data</li>
              <li>Request deletion of your personal data ("right to be forgotten")</li>
              <li>Object to processing of your data</li>
              <li>Data portability</li>
            </ul>
            <p>To exercise any of these rights, contact us at <a href="mailto:support@bluechips.live" className="text-gold-400 hover:text-gold-300">support@bluechips.live</a>.</p>
          </section>

          <section className="space-y-4">
            <h2 className="font-serif text-xl text-ivory-200">6. Third Parties</h2>
            <ul className="list-disc list-inside space-y-1.5 text-stone-500">
              <li><strong className="text-stone-400">Stripe</strong> — payment processing (stripe.com/privacy)</li>
              <li><strong className="text-stone-400">Cloudflare / AWS</strong> — media storage and CDN</li>
              <li><strong className="text-stone-400">Google (SMTP)</strong> — transactional email delivery</li>
            </ul>
            <p>We do not sell or share your personal data with third parties for marketing purposes.</p>
          </section>

          <section className="space-y-4">
            <h2 className="font-serif text-xl text-ivory-200">7. Cookies</h2>
            <p>
              Bluechips London uses only essential cookies required for authentication (JWT tokens stored in browser localStorage). We do not use tracking, advertising, or analytics cookies.
            </p>
          </section>

          <section className="space-y-4">
            <h2 className="font-serif text-xl text-ivory-200">8. Contact</h2>
            <p>
              For any privacy-related queries or to exercise your data rights, contact us at:{' '}
              <a href="mailto:support@bluechips.live" className="text-gold-400 hover:text-gold-300">
                support@bluechips.live
              </a>
            </p>
          </section>
        </div>
      </div>
    </Layout>
  )
}
