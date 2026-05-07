import { useParams } from 'react-router-dom'
import { Helmet } from 'react-helmet-async'
import { Layout } from '@/components/layout/Layout'
import { EscortGrid } from '@/components/escort/EscortGrid'
import { useBoroughs } from '@/hooks/useBoroughs'
import { useEscorts } from '@/hooks/useEscorts'
import { Spinner } from '@/components/ui/Spinner'
import { slugToTitle } from '@/utils/formatters'
import { useState } from 'react'
import { Button } from '@/components/ui/Button'
import { ChevronLeft, ChevronRight } from 'lucide-react'

export function BoroughPage() {
  const { slug } = useParams<{ slug: string }>()
  const [page, setPage] = useState(1)
  const { data: boroughs = [] } = useBoroughs()
  const borough = boroughs.find((b) => b.slug === slug)

  const { data, isLoading } = useEscorts({
    borough_slug: slug,
    page,
    per_page: 24,
  })

  const title = borough?.seo_title ?? `Escorts in ${slugToTitle(slug ?? '')} | Bluechips London`
  const description = borough?.seo_description ?? `Browse verified companion listings in ${slugToTitle(slug ?? '')}, London.`

  return (
    <Layout>
      <Helmet>
        <title>{title}</title>
        <meta name="description" content={description} />
        <link rel="canonical" href={`https://bluechips.live/areas/${slug}`} />
        <meta property="og:type" content="website" />
        <meta property="og:title" content={title} />
        <meta property="og:description" content={description} />
        <meta property="og:url" content={`https://bluechips.live/areas/${slug}`} />
      </Helmet>

      <div className="page-container py-10 space-y-8">
        <div className="max-w-2xl space-y-3">
          <p className="text-xs uppercase tracking-widest text-gold-500/70 font-medium">London Area</p>
          <h1 className="font-serif text-4xl lg:text-5xl text-ivory-100">
            Companions in {borough?.name ?? slugToTitle(slug ?? '')}
          </h1>
          {borough?.description && (
            <p className="text-stone-500 leading-relaxed">{borough.description}</p>
          )}
          {data && (
            <p className="text-stone-600 text-sm">{data.total.toLocaleString()} companion{data.total !== 1 ? 's' : ''} listed in this area</p>
          )}
        </div>

        <EscortGrid escorts={data?.items ?? []} loading={isLoading} skeletonCount={24} />

        {data && data.pages > 1 && (
          <div className="flex items-center justify-center gap-4 pt-4">
            <Button variant="outline-gold" size="sm" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
              <ChevronLeft className="w-4 h-4" /> Previous
            </Button>
            <span className="text-stone-400 text-sm">Page {page} of {data.pages}</span>
            <Button variant="outline-gold" size="sm" disabled={page === data.pages} onClick={() => setPage((p) => p + 1)}>
              Next <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        )}
      </div>
    </Layout>
  )
}
