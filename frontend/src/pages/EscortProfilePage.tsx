import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { motion } from 'framer-motion'
import {
  MapPin, Phone, MessageCircle, Shield, Star, ChevronLeft,
  Activity, Clock, Eye, AlertTriangle
} from 'lucide-react'
import { Layout } from '@/components/layout/Layout'
import { VerificationBadge } from '@/components/escort/VerificationBadge'
import { ServiceTags } from '@/components/escort/ServiceTags'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'
import { useEscortProfile } from '@/hooks/useEscorts'
import { escortsApi } from '@/api/escorts'
import { formatHeight, formatRate } from '@/utils/formatters'
import { cn } from '@/utils/cn'

const PLACEHOLDER = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='600' viewBox='0 0 400 600'%3E%3Crect width='400' height='600' fill='%23161616'/%3E%3Ctext x='200' y='300' font-family='Georgia' font-size='72' fill='%23C9A84C' text-anchor='middle' dominant-baseline='middle'%3EB%3C/text%3E%3C/svg%3E"

const WA_MESSAGE = encodeURIComponent(
  "Hey, I found you on Bluechips London and I'd love to arrange a meeting. Are you available?"
)

function ContactButtons({ slug, whatsappNumber, phoneNumber }: {
  slug: string
  whatsappNumber: string | null
  phoneNumber: string | null
}) {
  const waDigits = whatsappNumber?.replace(/\D/g, '')
  // Use dedicated phone number for calls/SMS; fall back to WhatsApp number if only one was provided
  const callNumber = phoneNumber || whatsappNumber
  const hasContact = !!(whatsappNumber || phoneNumber)

  const recordClick = () => escortsApi.recordContactClick(slug)

  if (!hasContact) {
    return (
      <div className="space-y-3">
        <p className="text-xs uppercase tracking-widest text-stone-500 font-medium">Contact</p>
        <div className="p-4 rounded-xl bg-surface border border-surface-border text-center">
          <p className="text-stone-500 text-sm">This companion has not added contact details yet.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <p className="text-xs uppercase tracking-widest text-stone-500 font-medium">Contact</p>
      <div className="space-y-2">
        {waDigits && (
          <a
            href={`https://wa.me/${waDigits}?text=${WA_MESSAGE}`}
            target="_blank"
            rel="noopener noreferrer"
            onClick={recordClick}
            className="flex items-center justify-center gap-3 w-full px-5 py-3.5 rounded-xl bg-[#25D366] hover:bg-[#20bd5c] text-white font-semibold text-sm transition-colors"
          >
            {/* WhatsApp SVG icon */}
            <svg viewBox="0 0 24 24" className="w-5 h-5 fill-current" aria-hidden="true">
              <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
            </svg>
            Message on WhatsApp
          </a>
        )}
        {callNumber && (
          <div className="flex gap-2">
            <a
              href={`tel:${callNumber.replace(/\s/g, '')}`}
              onClick={recordClick}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl border border-surface-border bg-surface hover:border-gold-400/40 hover:bg-surface-hover text-stone-300 hover:text-ivory-100 font-medium text-sm transition-all"
            >
              <Phone className="w-4 h-4" /> Call
            </a>
            <a
              href={`sms:${callNumber.replace(/\s/g, '')}?body=${WA_MESSAGE}`}
              onClick={recordClick}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl border border-surface-border bg-surface hover:border-gold-400/40 hover:bg-surface-hover text-stone-300 hover:text-ivory-100 font-medium text-sm transition-all"
            >
              <MessageCircle className="w-4 h-4" /> Text
            </a>
          </div>
        )}
      </div>
      <p className="text-stone-700 text-[11px] text-center leading-relaxed">
        Bluechips London does not handle payments or bookings. All arrangements are made directly with the companion.
      </p>
    </div>
  )
}

export function EscortProfilePage() {
  const { slug } = useParams<{ slug: string }>()
  const { data: escort, isLoading, isError } = useEscortProfile(slug!)
  const [activePhoto, setActivePhoto] = useState(0)

  if (isLoading) return <Layout><Spinner fullPage /></Layout>
  if (isError || !escort) return (
    <Layout>
      <div className="page-container py-24 text-center space-y-6">
        <p className="font-serif text-3xl text-ivory-200">Profile not found</p>
        <p className="text-stone-400 text-sm">This profile may have been removed or the link is incorrect.</p>
        <Link to="/escorts"><Button variant="outline-gold">Browse All Companions</Button></Link>
      </div>
    </Layout>
  )

  const photos = escort.photos.length > 0 ? escort.photos : [{ id: '0', url: PLACEHOLDER, thumbnail_url: null, is_primary: true, sort_order: 0 }]

  const stats = [
    { label: 'Age', value: escort.age ? `${escort.age} yrs` : '—' },
    { label: 'Nationality', value: escort.nationality || '—' },
    { label: 'Ethnicity', value: escort.ethnicity || '—' },
    { label: 'Height', value: formatHeight(escort.height_cm) },
    { label: 'Build', value: escort.build ? escort.build.charAt(0).toUpperCase() + escort.build.slice(1) : '—' },
    { label: 'Hair', value: escort.hair_colour || '—' },
    { label: 'Eyes', value: escort.eye_colour || '—' },
    { label: 'Languages', value: escort.languages?.join(', ') || '—' },
  ]

  const rates = [
    { label: '30 min', value: escort.rate_30min },
    { label: '1 hour', value: escort.rate_1hour },
    { label: '2 hours', value: escort.rate_2hours },
    { label: 'Overnight', value: escort.rate_overnight },
  ].filter((r) => r.value)

  return (
    <Layout>
      <Helmet>
        <title>{`${escort.stage_name}, ${escort.age} — ${escort.borough_name ?? 'London'} | Bluechips London`}</title>
        <meta name="description" content={`${escort.stage_name}, ${escort.age} year old companion in ${escort.borough_name ?? 'London'}. ${escort.about_me?.slice(0, 120) ?? ''}`} />
      </Helmet>

      <div className="page-container py-8">
        {/* Back */}
        <Link to="/escorts" className="inline-flex items-center gap-1.5 text-stone-500 text-sm hover:text-gold-400 transition-colors mb-6">
          <ChevronLeft className="w-4 h-4" /> Back to Companions
        </Link>

        <div className="grid lg:grid-cols-[1fr_380px] gap-8 xl:gap-12">
          {/* Left: Photos + Info */}
          <div className="space-y-8">
            {/* Photo gallery */}
            <div className="space-y-3">
              <motion.div
                key={activePhoto}
                initial={{ opacity: 0.7, scale: 0.99 }}
                animate={{ opacity: 1, scale: 1 }}
                className="aspect-[4/5] rounded-2xl overflow-hidden bg-surface relative"
              >
                <img
                  src={photos[activePhoto]?.url || PLACEHOLDER}
                  alt={escort.stage_name}
                  className="w-full h-full object-cover object-top"
                />
                {escort.available_now && (
                  <div className="absolute top-4 left-4">
                    <span className="inline-flex items-center gap-2 bg-emerald-500/90 backdrop-blur-sm text-white text-xs font-semibold px-3 py-1.5 rounded-full">
                      <span className="w-2 h-2 rounded-full bg-white animate-pulse" /> Available Now
                    </span>
                  </div>
                )}
              </motion.div>

              {photos.length > 1 && (
                <div className="grid grid-cols-5 gap-2">
                  {photos.map((photo, i) => (
                    <button
                      key={photo.id}
                      onClick={() => setActivePhoto(i)}
                      className={cn(
                        'aspect-square rounded-lg overflow-hidden border-2 transition-all',
                        i === activePhoto ? 'border-gold-400' : 'border-transparent opacity-60 hover:opacity-100'
                      )}
                    >
                      <img src={photo.thumbnail_url || photo.url} alt="" className="w-full h-full object-cover" />
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* About */}
            {escort.about_me && (
              <div className="space-y-3">
                <h2 className="font-serif text-xl text-ivory-100">About {escort.stage_name}</h2>
                <p className="text-stone-400 leading-relaxed">{escort.about_me}</p>
              </div>
            )}

            {/* Services */}
            {escort.service_tags.length > 0 && (
              <div className="space-y-3">
                <h2 className="font-serif text-xl text-ivory-100">Services</h2>
                <ServiceTags tags={escort.service_tags} max={escort.service_tags.length} size="md" />
                <p className="text-stone-700 text-xs">Services are self-declared by the companion. Bluechips London does not guarantee or facilitate any services listed.</p>
              </div>
            )}

            {/* Stats */}
            <div className="space-y-3">
              <h2 className="font-serif text-xl text-ivory-100">Profile Details</h2>
              <div className="grid grid-cols-2 gap-px bg-surface-border rounded-xl overflow-hidden border border-surface-border">
                {stats.map(({ label, value }) => (
                  <div key={label} className="bg-surface-card px-4 py-3">
                    <p className="text-stone-600 text-xs uppercase tracking-wider mb-0.5">{label}</p>
                    <p className="text-ivory-200 text-sm">{value}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right: Sidebar */}
          <div className="space-y-6 lg:sticky lg:top-24 lg:self-start">
            {/* Profile header */}
            <div className="card-surface p-6 rounded-2xl space-y-4">
              <div>
                <div className="flex items-start justify-between">
                  <h1 className="font-serif text-3xl text-ivory-100">{escort.stage_name}</h1>
                  <div className="flex gap-1.5">
                    <VerificationBadge
                      level={escort.verification_level}
                      blue_tick_active={escort.blue_tick_active}
                      subscription_tier={escort.subscription_tier}
                      size="sm"
                    />
                  </div>
                </div>

                <div className="flex items-center gap-3 mt-2 flex-wrap">
                  {escort.borough_name && (
                    <span className="flex items-center gap-1 text-stone-500 text-sm">
                      <MapPin className="w-3.5 h-3.5" /> {escort.borough_name}
                    </span>
                  )}
                  {escort.availability_type && (
                    <Badge variant="subtle">{escort.availability_type === 'both' ? 'Incall & Outcall' : escort.availability_type}</Badge>
                  )}
                  {(escort as any).profile_type === 'couple' && (
                    <Badge variant="subtle">💑 Couple</Badge>
                  )}
                </div>
              </div>

              {/* Badges row */}
              <div className="flex flex-wrap gap-2">
                <VerificationBadge
                  level={escort.verification_level}
                  blue_tick_active={escort.blue_tick_active}
                  subscription_tier={escort.subscription_tier}
                  size="md"
                  showLabel
                />
                {escort.std_tested && (
                  <Badge variant="std">
                    <Activity className="w-3.5 h-3.5" />
                    STD Tested {escort.std_tested_date && `· ${escort.std_tested_date}`}
                  </Badge>
                )}
                {escort.booking_notice && (
                  <Badge variant="subtle">
                    <Clock className="w-3 h-3" /> {escort.booking_notice}
                  </Badge>
                )}
              </div>

              {/* Verification explainer */}
              {escort.subscription_tier === 'elite' && escort.verification_level >= 2 ? (
                <div className="flex items-start gap-2 p-3 rounded-lg bg-purple-950/40 border border-purple-500/20">
                  <Shield className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                  <p className="text-purple-300/80 text-xs leading-relaxed">
                    <span className="font-medium text-purple-300">Elite — Identity independently verified</span> — this companion's government ID was reviewed by the Bluechips London team. Who you see is who you'll meet.
                  </p>
                </div>
              ) : (escort.blue_tick_active || escort.verification_level >= 3) ? (
                <div className="flex items-start gap-2 p-3 rounded-lg bg-blue-950/40 border border-blue-500/20">
                  <Shield className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
                  <p className="text-blue-300/80 text-xs leading-relaxed">
                    <span className="font-medium text-blue-300">Identity & photos independently verified</span> — this companion's government ID and profile photos were reviewed by the Bluechips London team. Who you see is who you'll meet.
                  </p>
                </div>
              ) : null}

              {/* Views */}
              <p className="text-stone-700 text-xs flex items-center gap-1">
                <Eye className="w-3 h-3" /> {escort.profile_views.toLocaleString()} profile views
              </p>
            </div>

            {/* Rates */}
            {rates.length > 0 && (
              <div className="card-surface p-6 rounded-2xl space-y-4">
                <h3 className="font-serif text-lg text-ivory-100">Rates</h3>
                <div className="space-y-2">
                  {rates.map(({ label, value }) => (
                    <div key={label} className="flex items-center justify-between py-2 border-b border-surface-border last:border-0">
                      <span className="text-stone-400 text-sm">{label}</span>
                      <span className="text-gold-400 font-semibold">{formatRate(value!)}</span>
                    </div>
                  ))}
                </div>
                <p className="text-stone-700 text-[11px]">Rates shown are for time only. All services are at the companion's sole discretion.</p>
              </div>
            )}

            {/* Contact */}
            <div className="card-surface p-6 rounded-2xl">
              <ContactButtons
                slug={escort.slug}
                whatsappNumber={(escort as any).whatsapp_number ?? null}
                phoneNumber={(escort as any).phone_number ?? null}
              />
            </div>

            {/* Safety warning */}
            <div className="p-4 rounded-xl border border-stone-800 bg-stone-900/20 space-y-2">
              <div className="flex items-center gap-2 text-stone-500">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <p className="text-xs font-medium">Safety Reminder</p>
              </div>
              <p className="text-stone-600 text-xs leading-relaxed">
                Always verify you are communicating with the companion directly. Never send money in advance. Bluechips London does not handle bookings or payments.
              </p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
