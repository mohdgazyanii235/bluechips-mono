export function formatHeight(cm: number | null): string {
  if (!cm) return '—'
  const totalInches = Math.round(cm / 2.54)
  const feet = Math.floor(totalInches / 12)
  const inches = totalInches % 12
  return `${feet}'${inches}" / ${cm}cm`
}

export function formatRate(amount: number | null): string {
  if (!amount) return '—'
  return `£${amount.toLocaleString()}`
}

export function formatVerificationLabel(level: number): string {
  const labels: Record<number, string> = {
    0: 'Unverified',
    1: 'Email Verified',
    2: 'ID Verified',
    3: 'Blue Tick',
  }
  return labels[level] ?? 'Unknown'
}

export function timeAgo(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = (now.getTime() - date.getTime()) / 1000

  if (diff < 60) return 'Just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

export function slugToTitle(slug: string): string {
  return slug
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

export function completionPercentage(profile: Record<string, unknown>): number {
  const fields = ['age', 'about_me', 'borough_id', 'availability_type', 'rate_1hour', 'nationality', 'ethnicity', 'height_cm']
  const filled = fields.filter(f => profile[f] != null && profile[f] !== '').length
  return Math.round((filled / fields.length) * 100)
}
