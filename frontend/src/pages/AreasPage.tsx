import { Link } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { Layout } from '@/components/layout/Layout'
import { useBoroughs } from '@/hooks/useBoroughs'
import { Spinner } from '@/components/ui/Spinner'
import { Star } from 'lucide-react'

export function AreasPage() {
  const { data: boroughs = [], isLoading } = useBoroughs()
  const premium = boroughs.filter((b) => b.is_premium_area)
  const regular = boroughs.filter((b) => !b.is_premium_area)

  return (
    <Layout>
      <Helmet>
        <title>London Areas — Browse by Borough | Bluechips London</title>
        <meta name="description" content="Browse independent companion listings across all 32 London boroughs. From Mayfair to Stratford — find companions near you." />
      </Helmet>

      <div className="page-container py-10 space-y-12">
        <div className="space-y-3">
          <h1 className="font-serif text-4xl lg:text-5xl text-ivory-100">Browse London Areas</h1>
          <p className="text-stone-500 max-w-xl leading-relaxed">
            Explore companion listings across all 32 London boroughs. Each area page is dedicated to helping you find the right companion, wherever you are.
          </p>
        </div>

        {isLoading && <Spinner fullPage />}

        {/* Premium Areas */}
        {premium.length > 0 && (
          <section className="space-y-5">
            <div className="flex items-center gap-3">
              <Star className="w-4 h-4 text-gold-400" />
              <h2 className="text-xs uppercase tracking-widest text-gold-500 font-medium">Premium Areas</h2>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {premium.map((b) => (
                <Link key={b.slug} to={`/escorts?borough_slug=${b.slug}`}>
                  <div className="group card-surface-hover p-5 rounded-xl space-y-2">
                    <div className="flex items-start justify-between">
                      <h3 className="font-serif text-xl text-ivory-100 group-hover:text-gold-400 transition-colors">{b.name}</h3>
                      <span className="text-gold-400 text-xs font-medium bg-gold-400/10 px-2 py-0.5 rounded-full border border-gold-400/20">
                        {b.escort_count}
                      </span>
                    </div>
                    {b.description && (
                      <p className="text-stone-500 text-sm leading-relaxed line-clamp-2">{b.description}</p>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          </section>
        )}

        {/* All Areas */}
        {regular.length > 0 && (
          <section className="space-y-5">
            <h2 className="text-xs uppercase tracking-widest text-stone-500 font-medium">All London Areas</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
              {regular.map((b) => (
                <Link key={b.slug} to={`/escorts?borough_slug=${b.slug}`}>
                  <div className="group flex items-center justify-between p-4 rounded-xl border border-surface-border bg-surface-card hover:border-gold-400/30 transition-all">
                    <span className="text-ivory-300 text-sm group-hover:text-gold-400 transition-colors">{b.name}</span>
                    <span className="text-stone-600 text-xs">{b.escort_count} listings</span>
                  </div>
                </Link>
              ))}
            </div>
          </section>
        )}
      </div>
    </Layout>
  )
}
