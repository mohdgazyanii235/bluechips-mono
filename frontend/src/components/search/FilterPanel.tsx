import { useState } from 'react'
import { SlidersHorizontal, X } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Select'
import { useBoroughs } from '@/hooks/useBoroughs'
import type { SearchFilters } from '@/types/escort'
import { ETHNICITIES } from '@/types/escort'
import { cn } from '@/utils/cn'
import { AnimatePresence, motion } from 'framer-motion'

interface FilterPanelProps {
  filters: SearchFilters
  onChange: (filters: SearchFilters) => void
}

const rateOptions = [
  { value: '', label: 'Any rate' },
  { value: '100', label: 'Up to £100/hr' },
  { value: '150', label: 'Up to £150/hr' },
  { value: '200', label: 'Up to £200/hr' },
  { value: '300', label: 'Up to £300/hr' },
  { value: '500', label: 'Up to £500/hr' },
]

const ageOptions = [
  { value: '', label: 'Any age' },
  { value: '18-25', label: '18 – 25' },
  { value: '25-30', label: '25 – 30' },
  { value: '30-40', label: '30 – 40' },
  { value: '40+', label: '40+' },
]

export function FilterPanel({ filters, onChange }: FilterPanelProps) {
  const [open, setOpen] = useState(false)
  const { data: boroughs = [] } = useBoroughs()

  const boroughOptions = [
    { value: '', label: 'All London Areas' },
    ...boroughs.map((b) => ({ value: b.slug, label: `${b.name} (${b.escort_count})` })),
  ]

  const ethnicityOptions = [
    { value: '', label: 'Any ethnicity' },
    ...ETHNICITIES.map((e) => ({ value: e, label: e })),
  ]

  const availabilityOptions = [
    { value: '', label: 'Any' },
    { value: 'incall', label: 'Incall' },
    { value: 'outcall', label: 'Outcall' },
    { value: 'both', label: 'Incall & Outcall' },
  ]

  const activeFilterCount = [
    filters.borough_slug, filters.ethnicity, filters.availability_type,
    filters.max_rate, filters.available_now, filters.blue_tick_only, filters.std_tested,
    filters.profile_type,
  ].filter(Boolean).length

  const handleAgeRange = (value: string) => {
    if (!value) return onChange({ ...filters, min_age: undefined, max_age: undefined })
    if (value === '40+') return onChange({ ...filters, min_age: 40, max_age: undefined })
    const [min, max] = value.split('-').map(Number)
    onChange({ ...filters, min_age: min, max_age: max })
  }

  const clearAll = () => onChange({ page: 1 })

  return (
    <div>
      {/* Mobile toggle */}
      <div className="flex items-center gap-3 flex-wrap">
        <Button
          variant="outline-gold"
          size="sm"
          onClick={() => setOpen(!open)}
          className="lg:hidden"
        >
          <SlidersHorizontal className="w-4 h-4" />
          Filters
          {activeFilterCount > 0 && (
            <span className="bg-gold-400 text-black text-[10px] font-bold w-4 h-4 rounded-full flex items-center justify-center">
              {activeFilterCount}
            </span>
          )}
        </Button>

        {/* Desktop quick filters always visible */}
        <div className="hidden lg:flex items-center gap-3 flex-wrap">
          <FilterControls
            filters={filters}
            onChange={onChange}
            boroughOptions={boroughOptions}
            ethnicityOptions={ethnicityOptions}
            availabilityOptions={availabilityOptions}
            rateOptions={rateOptions}
            ageOptions={ageOptions}
            handleAgeRange={handleAgeRange}
          />
          {activeFilterCount > 0 && (
            <button onClick={clearAll} className="text-stone-500 text-xs hover:text-stone-300 flex items-center gap-1">
              <X className="w-3 h-3" /> Clear
            </button>
          )}
        </div>
      </div>

      {/* Mobile drawer */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="lg:hidden overflow-hidden mt-4"
          >
            <div className="card-surface p-4 space-y-4">
              <FilterControls
                filters={filters}
                onChange={onChange}
                boroughOptions={boroughOptions}
                ethnicityOptions={ethnicityOptions}
                availabilityOptions={availabilityOptions}
                rateOptions={rateOptions}
                ageOptions={ageOptions}
                handleAgeRange={handleAgeRange}
                vertical
              />
              <div className="flex gap-3 pt-2">
                {activeFilterCount > 0 && (
                  <Button variant="ghost" size="sm" onClick={clearAll} fullWidth>Clear all</Button>
                )}
                <Button variant="gold" size="sm" fullWidth onClick={() => setOpen(false)}>
                  Apply Filters
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function FilterControls({
  filters, onChange, boroughOptions, ethnicityOptions, availabilityOptions,
  rateOptions, ageOptions, handleAgeRange, vertical,
}: any) {
  const wrapClass = vertical ? 'grid grid-cols-1 gap-3' : 'flex items-center gap-3 flex-wrap'

  return (
    <div className={wrapClass}>
      <div className={vertical ? '' : 'w-44'}>
        <Select
          options={boroughOptions}
          value={filters.borough_slug || ''}
          onChange={(e) => onChange({ ...filters, borough_slug: e.target.value || undefined, page: 1 })}
          placeholder="All London Areas"
        />
      </div>
      <div className={vertical ? '' : 'w-36'}>
        <Select
          options={ethnicityOptions}
          value={filters.ethnicity || ''}
          onChange={(e) => onChange({ ...filters, ethnicity: e.target.value || undefined, page: 1 })}
          placeholder="Any ethnicity"
        />
      </div>
      <div className={vertical ? '' : 'w-36'}>
        <Select
          options={availabilityOptions}
          value={filters.availability_type || ''}
          onChange={(e) => onChange({ ...filters, availability_type: e.target.value || undefined, page: 1 })}
          placeholder="Any"
        />
      </div>
      <div className={vertical ? '' : 'w-36'}>
        <Select
          options={rateOptions}
          value={filters.max_rate ? `${filters.max_rate}` : ''}
          onChange={(e) => onChange({ ...filters, max_rate: e.target.value ? Number(e.target.value) : undefined, page: 1 })}
          placeholder="Any rate"
        />
      </div>

      {/* Toggle chips */}
      <div className="flex gap-2 flex-wrap">
        {[
          { key: 'available_now', label: 'Available Now' },
          { key: 'blue_tick_only', label: '✓ Verified Only' },
          { key: 'std_tested', label: 'STD Tested' },
        ].map(({ key, label }) => (
          <button
            key={key}
            onClick={() => onChange({ ...filters, [key]: !(filters as any)[key] || undefined, page: 1 })}
            className={cn(
              'px-3 py-1.5 rounded-full text-xs font-medium border transition-all',
              (filters as any)[key]
                ? 'bg-gold-400 text-black border-gold-400'
                : 'bg-surface border-surface-border text-stone-400 hover:border-gold-400/50'
            )}
          >
            {label}
          </button>
        ))}
        {/* Couples filter */}
        <button
          onClick={() => onChange({
            ...filters,
            profile_type: filters.profile_type === 'couple' ? undefined : 'couple',
            page: 1,
          })}
          className={cn(
            'px-3 py-1.5 rounded-full text-xs font-medium border transition-all',
            filters.profile_type === 'couple'
              ? 'bg-gold-400 text-black border-gold-400'
              : 'bg-surface border-surface-border text-stone-400 hover:border-gold-400/50'
          )}
        >
          💑 Couples
        </button>
      </div>
    </div>
  )
}
