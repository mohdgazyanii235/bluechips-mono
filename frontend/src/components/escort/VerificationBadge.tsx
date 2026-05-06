import { BadgeCheck, ShieldCheck } from 'lucide-react'
import { cn } from '@/utils/cn'

interface VerificationBadgeProps {
  level: number
  blue_tick_active?: boolean
  subscription_tier?: string
  size?: 'sm' | 'md'
  showLabel?: boolean
}

/** Purple tick badge for Elite subscribers — automatic, no admin approval. */
export function EliteBadge({ size = 'sm', showLabel }: { size?: 'sm' | 'md'; showLabel?: boolean }) {
  const isSm = size === 'sm'
  return (
    <span className={cn(
      'inline-flex items-center gap-1 font-medium rounded-full',
      isSm ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm',
      'bg-purple-500/15 text-purple-400 border border-purple-500/30'
    )}>
      <BadgeCheck className={isSm ? 'w-3 h-3' : 'w-4 h-4'} />
      {showLabel && 'Elite'}
    </span>
  )
}

export function VerificationBadge({ level, blue_tick_active, subscription_tier, size = 'sm', showLabel }: VerificationBadgeProps) {
  const isSm = size === 'sm'
  const isElite = subscription_tier === 'elite'

  // Elite purple tick — only when identity verified (level 2+)
  if (isElite && level >= 2) {
    return (
      <span className={cn(
        'inline-flex items-center gap-1 font-medium rounded-full',
        isSm ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm',
        'bg-purple-500/15 text-purple-400 border border-purple-500/30'
      )}>
        <BadgeCheck className={isSm ? 'w-3 h-3' : 'w-4 h-4'} />
        {showLabel && 'Elite'}
      </span>
    )
  }

  // Blue Tick (admin approved, identity + photos verified)
  if (blue_tick_active || level >= 3) {
    return (
      <span className={cn(
        'inline-flex items-center gap-1 font-medium rounded-full',
        isSm ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm',
        'bg-blue-500/15 text-blue-400 border border-blue-500/30'
      )}>
        <BadgeCheck className={isSm ? 'w-3 h-3' : 'w-4 h-4'} />
        {showLabel && 'Blue Tick'}
      </span>
    )
  }

  // Identity verified
  if (level >= 2) {
    return (
      <span className={cn(
        'inline-flex items-center gap-1 font-medium rounded-full',
        isSm ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm',
        'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
      )}>
        <ShieldCheck className={isSm ? 'w-3 h-3' : 'w-4 h-4'} />
        {showLabel && 'ID Verified'}
      </span>
    )
  }

  return null
}
