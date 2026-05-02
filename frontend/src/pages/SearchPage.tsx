import { useState } from 'react'
import { Helmet } from 'react-helmet-async'
import { Layout } from '@/components/layout/Layout'
import { EscortGrid } from '@/components/escort/EscortGrid'
import { FilterPanel } from '@/components/search/FilterPanel'
import { Button } from '@/components/ui/Button'
import { useEscorts } from '@/hooks/useEscorts'
import type { SearchFilters } from '@/types/escort'
import { ChevronLeft, ChevronRight, BadgeCheck } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'
import { slugToTitle } from '@/utils/formatters'

export function SearchPage() {
  const [searchParams] = useSearchParams()
  const initialFilters: SearchFilters = {
    borough_slug: searchParams.get('borough_slug') || undefined,
    available_now: searchParams.get('available_now') === 'true' || undefined,
    blue_tick_only: searchParams.get('blue_tick_only') === 'true' || undefined,
    std_tested: searchParams.get('std_tested') === 'true' || undefined,
    page: 1,
    per_page: 24,
  }

  const [filters, setFilters] = useState<SearchFilters>(initialFilters)
  const { data, isLoading } = useEscorts(filters)

  const boroughTitle = filters.borough_slug ? slugToTitle(filters.borough_slug) : null
  const pageTitle = boroughTitle ? `Escorts in ${boroughTitle}` : 'Browse Companions'

  const handleFilterChange = (newFilters: SearchFilters) => {
    setFilters({ ...newFilters, page: 1 })
  }

  return (
    <Layout>
      <Helmet>
        <title>{`${pageTitle} — Bluechips London`}</title>
        <meta name="description" content={`Browse verified independent companion listings${boroughTitle ? ` in ${boroughTitle}` : ' across London'}. Discreet, premium, verified.`} />
      </Helmet>

      <div className="page-container py-10 space-y-8">
        {/* Page header */}
        <div>
          <h1 className="font-serif text-3xl lg:text-4xl text-ivory-100">{pageTitle}</h1>
          {data && (
            <p className="text-stone-500 text-sm mt-1">
              {data.total.toLocaleString()} companion{data.total !== 1 ? 's' : ''} found
            </p>
          )}
        </div>

        {/* Blue Tick nudge — hidden once the filter is active */}
        {!filters.blue_tick_only && (
          <div className="flex items-center gap-3 p-4 rounded-xl bg-blue-950/30 border border-blue-500/15">
            <BadgeCheck className="w-5 h-5 text-blue-400 shrink-0" />
            <p className="flex-1 text-sm text-stone-400 leading-snug">
              <span className="text-blue-300 font-medium">Blue Tick companions have been ID-verified by our team</span>
              {' '}— their photos are genuine and they are exactly who they say they are.
            </p>
            <button
              onClick={() => handleFilterChange({ ...filters, blue_tick_only: true })}
              className="shrink-0 text-xs text-blue-400 border border-blue-500/30 px-3 py-1.5 rounded-full hover:bg-blue-500/10 transition-colors whitespace-nowrap"
            >
              Verified only →
            </button>
          </div>
        )}

        {/* Filters */}
        <FilterPanel filters={filters} onChange={handleFilterChange} />

        {/* Results */}
        <EscortGrid
          escorts={data?.items ?? []}
          loading={isLoading}
          skeletonCount={24}
        />

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="flex items-center justify-center gap-4 pt-4">
            <Button
              variant="outline-gold"
              size="sm"
              disabled={filters.page === 1}
              onClick={() => setFilters((f) => ({ ...f, page: (f.page ?? 1) - 1 }))}
            >
              <ChevronLeft className="w-4 h-4" /> Previous
            </Button>
            <span className="text-stone-400 text-sm">
              Page {filters.page} of {data.pages}
            </span>
            <Button
              variant="outline-gold"
              size="sm"
              disabled={filters.page === data.pages}
              onClick={() => setFilters((f) => ({ ...f, page: (f.page ?? 1) + 1 }))}
            >
              Next <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        )}
      </div>
    </Layout>
  )
}
