import { BadgeCheck, ShieldCheck, Mail } from 'lucide-react'
import { cn } from '@/utils/cn'

interface VerificationBadgeProps {
  level: number
  size?: 'sm' | 'md'
  showLabel?: boolean
}

export function VerificationBadge({ level, size = 'sm', showLabel }: VerificationBadgeProps) {
  if (level === 0) return null

  const isSm = size === 'sm'

  if (level >= 3) {
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

  if (level >= 1) {
    return (
      <span className={cn(
        'inline-flex items-center gap-1 font-medium rounded-full',
        isSm ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm',
        'bg-stone-500/10 text-stone-400 border border-stone-500/30'
      )}>
        <Mail className={isSm ? 'w-3 h-3' : 'w-4 h-4'} />
        {showLabel && 'Email Verified'}
      </span>
    )
  }

  return null
}
