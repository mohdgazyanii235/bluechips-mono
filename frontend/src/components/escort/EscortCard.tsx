import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { MapPin, Star } from 'lucide-react'
import type { EscortCard as EscortCardType } from '@/types/escort'
import { VerificationBadge } from './VerificationBadge'
import { ServiceTags } from './ServiceTags'
import { formatRate } from '@/utils/formatters'
import { cn } from '@/utils/cn'

interface EscortCardProps {
  escort: EscortCardType
  index?: number
}

const PLACEHOLDER_IMG = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='400' viewBox='0 0 300 400'%3E%3Crect width='300' height='400' fill='%23161616'/%3E%3Ctext x='150' y='200' font-family='Georgia' font-size='48' fill='%23C9A84C' text-anchor='middle' dominant-baseline='middle'%3EB%3C/text%3E%3C/svg%3E"

export function EscortCard({ escort, index = 0 }: EscortCardProps) {
  const isElite = escort.subscription_tier === 'elite'
  const isPremium = escort.subscription_tier === 'premium' || isElite

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.35 }}
    >
      <Link to={`/escorts/${escort.slug}`} className="block group">
        <div className={cn(
          'relative overflow-hidden rounded-xl transition-all duration-300',
          'border border-surface-border bg-surface-card',
          'group-hover:border-gold-400/30 group-hover:shadow-card-hover group-hover:-translate-y-0.5',
          isElite && 'border-gold-400/20 shadow-gold'
        )}>
          {/* Photo */}
          <div className="relative aspect-[3/4] overflow-hidden bg-surface">
            <img
              src={escort.primary_photo_url || PLACEHOLDER_IMG}
              alt={escort.stage_name}
              className="w-full h-full object-cover object-top transition-transform duration-500 group-hover:scale-105"
              loading="lazy"
            />

            {/* Gradient overlay */}
            <div className="absolute inset-0 bg-card-gradient pointer-events-none" />

            {/* Top badges */}
            <div className="absolute top-3 left-3 right-3 flex items-start justify-between">
              <div className="flex flex-col gap-1.5">
                {escort.available_now && (
                  <span className="inline-flex items-center gap-1.5 bg-emerald-500/90 backdrop-blur-sm text-white text-[10px] font-semibold px-2 py-0.5 rounded-full">
                    <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
                    Available Now
                  </span>
                )}
                {escort.profile_type === 'couple' && (
                  <span className="inline-flex items-center gap-1 bg-purple-600/90 backdrop-blur-sm text-white text-[10px] font-semibold px-2 py-0.5 rounded-full">
                    💑 Couple
                  </span>
                )}
              </div>
              <div className="flex flex-col items-end gap-1.5">
                {isElite && (
                  <span className="bg-gold-400/90 backdrop-blur-sm text-black text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wide">
                    Elite
                  </span>
                )}
                {escort.std_tested && (
                  <span className="bg-teal-500/80 backdrop-blur-sm text-white text-[10px] font-medium px-2 py-0.5 rounded-full">
                    STD Tested
                  </span>
                )}
              </div>
            </div>

            {/* Bottom info overlay */}
            <div className="absolute bottom-0 left-0 right-0 p-3">
              <div className="flex items-end justify-between">
                <div>
                  <h3 className="font-serif text-lg text-white leading-tight">
                    {escort.stage_name}
                  </h3>
                  <p className="text-ivory-300/70 text-xs">
                    {escort.age && `${escort.age} yrs`}
                    {escort.age && escort.nationality && ' · '}
                    {escort.nationality}
                  </p>
                </div>
                {escort.verification_level >= 2 && (
                  <VerificationBadge level={escort.verification_level} size="sm" />
                )}
              </div>
            </div>
          </div>

          {/* Card Body */}
          <div className="p-3 space-y-2.5">
            {/* Location + Rate */}
            <div className="flex items-center justify-between">
              {escort.borough_name && (
                <span className="flex items-center gap-1 text-stone-500 text-xs">
                  <MapPin className="w-3 h-3" />
                  {escort.borough_name}
                </span>
              )}
              {escort.rate_1hour && (
                <span className="text-gold-400 text-sm font-semibold">
                  {formatRate(escort.rate_1hour)}<span className="text-stone-500 text-xs font-normal">/hr</span>
                </span>
              )}
            </div>

            {/* Service tags */}
            {escort.service_tags.length > 0 && (
              <ServiceTags tags={escort.service_tags} max={3} size="sm" />
            )}
          </div>
        </div>
      </Link>
    </motion.div>
  )
}
