import { Helmet } from 'react-helmet-async'
import { Layout } from '@/components/layout/Layout'
import { Mail, Clock, Shield } from 'lucide-react'

export function ContactPage() {
  return (
    <Layout>
      <Helmet>
        <title>Contact Bluechips London — Get in Touch</title>
        <meta name="description" content="Contact the Bluechips London team for support, account queries, or reporting concerns." />
        <link rel="canonical" href="https://bluechips.live/contact" />
      </Helmet>

      <div className="page-container py-16 max-w-2xl space-y-12">
        <div className="space-y-3">
          <h1 className="font-serif text-4xl text-ivory-100">Contact Us</h1>
          <p className="text-stone-400 leading-relaxed">
            We're a small team. Email is the fastest way to reach us — we aim to respond within one business day.
          </p>
        </div>

        <div className="space-y-5">
          <div className="card-surface p-6 rounded-2xl flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-gold-400/10 border border-gold-400/20 flex items-center justify-center shrink-0 mt-0.5">
              <Mail className="w-5 h-5 text-gold-400" />
            </div>
            <div className="space-y-1">
              <p className="font-medium text-ivory-200">General Enquiries</p>
              <p className="text-stone-500 text-sm">Account support, billing, and general questions</p>
              <a href="mailto:mohdgazyanii235@gmail.com" className="text-gold-400 hover:text-gold-300 text-sm transition-colors">
                mohdgazyanii235@gmail.com
              </a>
            </div>
          </div>

          <div className="card-surface p-6 rounded-2xl flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center shrink-0 mt-0.5">
              <Shield className="w-5 h-5 text-blue-400" />
            </div>
            <div className="space-y-1">
              <p className="font-medium text-ivory-200">Report a Concern</p>
              <p className="text-stone-500 text-sm">To report content that may be illegal or violate our terms, email us with the subject line "Report"</p>
              <a href="mailto:mohdgazyanii235@gmail.com?subject=Report" className="text-gold-400 hover:text-gold-300 text-sm transition-colors">
                mohdgazyanii235@gmail.com
              </a>
            </div>
          </div>

          <div className="card-surface p-6 rounded-2xl flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-stone-500/10 border border-stone-500/20 flex items-center justify-center shrink-0 mt-0.5">
              <Clock className="w-5 h-5 text-stone-400" />
            </div>
            <div className="space-y-1">
              <p className="font-medium text-ivory-200">Response Times</p>
              <p className="text-stone-500 text-sm leading-relaxed">
                General enquiries: within 1 business day<br />
                Verification reviews: within 1 hour during business hours<br />
                Legal / urgent: same day where possible
              </p>
            </div>
          </div>
        </div>

        <div className="p-5 rounded-xl border border-stone-800 bg-stone-900/20">
          <p className="text-stone-500 text-sm leading-relaxed">
            <strong className="text-stone-400">Please note:</strong> We are not able to facilitate bookings, pass messages to companions, or provide contact details for any listed individual. All contact with companions must be made directly through the details shown on their profile.
          </p>
        </div>
      </div>
    </Layout>
  )
}
