import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { AdminLayout } from './AdminLayout'
import { adminApi } from '@/api/admin'
import { Spinner } from '@/components/ui/Spinner'
import { Button } from '@/components/ui/Button'
import { ChevronLeft, CheckCircle, XCircle, ExternalLink } from 'lucide-react'
import toast from 'react-hot-toast'

function DocImage({ url, label }: { url: string | null; label: string }) {
  if (!url) return (
    <div className="aspect-[4/3] rounded-xl bg-surface border border-surface-border flex items-center justify-center">
      <p className="text-stone-600 text-sm">No {label} uploaded</p>
    </div>
  )
  return (
    <div className="space-y-2">
      <p className="text-xs uppercase tracking-wider text-stone-500">{label}</p>
      <a href={url} target="_blank" rel="noopener noreferrer" className="block group">
        <div className="relative rounded-xl overflow-hidden border border-surface-border bg-surface">
          <img src={url} alt={label} className="w-full object-cover max-h-80" />
          <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
            <ExternalLink className="w-6 h-6 text-white" />
          </div>
        </div>
      </a>
    </div>
  )
}

export function AdminVerificationDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [v, setV] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [notes, setNotes] = useState('')
  const [approving, setApproving] = useState(false)
  const [rejecting, setRejecting] = useState(false)

  useEffect(() => {
    if (id) adminApi.getVerification(id).then(setV).finally(() => setLoading(false))
  }, [id])

  const handleApprove = async () => {
    if (!id) return
    setApproving(true)
    try {
      await adminApi.approveVerification(id)
      toast.success('Verification approved. Escort notified.')
      navigate('/admin/verifications')
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Failed to approve')
    } finally {
      setApproving(false)
    }
  }

  const handleReject = async () => {
    if (!id) return
    if (!notes.trim()) {
      toast.error('Please add a reason for rejection — the escort will receive this in their email.')
      return
    }
    if (!confirm('Reject this verification? This will refund the escort\'s payment.')) return
    setRejecting(true)
    try {
      await adminApi.rejectVerification(id, notes)
      toast.success('Verification rejected. Escort notified and refunded.')
      navigate('/admin/verifications')
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Failed to reject')
    } finally {
      setRejecting(false)
    }
  }

  if (loading) return <AdminLayout><Spinner fullPage /></AdminLayout>
  if (!v) return <AdminLayout><p className="text-stone-400">Verification not found</p></AdminLayout>

  const isPending = v.status === 'pending'

  return (
    <AdminLayout>
      <div className="max-w-3xl space-y-8">
        <div className="flex items-center gap-3">
          <Link to="/admin/verifications" className="text-stone-500 hover:text-gold-400 transition-colors">
            <ChevronLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="font-serif text-2xl text-ivory-100">
              {v.level_name} — {v.escort?.stage_name}
            </h1>
            <p className="text-stone-500 text-sm mt-0.5">
              {v.escort?.email} · {v.escort?.subscription_tier} plan ·
              Submitted {new Date(v.submitted_at).toLocaleString('en-GB')}
            </p>
          </div>
          <span className={`ml-auto text-xs px-3 py-1 rounded-full border font-bold uppercase ${
            v.status === 'pending' ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
              : v.status === 'approved' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                : 'bg-red-500/10 text-red-400 border-red-500/30'
          }`}>
            {v.status}
          </span>
        </div>

        {/* Documents */}
        <div className="card-surface p-6 rounded-2xl space-y-5">
          <h2 className="font-serif text-lg text-ivory-100">Submitted Documents</h2>
          <div className="grid sm:grid-cols-2 gap-5">
            {v.id_document_signed_url && (
              <DocImage url={v.id_document_signed_url} label="Government ID" />
            )}
            {v.selfie_signed_url && (
              <DocImage url={v.selfie_signed_url} label="Selfie with date" />
            )}
            {v.match_selfie_signed_url && (
              <DocImage url={v.match_selfie_signed_url} label="Matching selfie" />
            )}
            {!v.id_document_signed_url && !v.selfie_signed_url && !v.match_selfie_signed_url && (
              <p className="text-stone-500 text-sm col-span-2">No documents were uploaded with this submission.</p>
            )}
          </div>
        </div>

        {/* Review */}
        {isPending && (
          <div className="card-surface p-6 rounded-2xl space-y-5">
            <h2 className="font-serif text-lg text-ivory-100">Review Decision</h2>

            <div className="space-y-2">
              <label className="block text-xs font-medium text-stone-400 uppercase tracking-wider">
                Notes / Rejection reason
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={4}
                placeholder="Required if rejecting. The escort will receive this in their email (keep it clear and professional)."
                className="input-field resize-none w-full"
              />
              <p className="text-stone-600 text-xs">This message will be sent directly to the escort.</p>
            </div>

            <div className="flex gap-3">
              <Button
                variant="gold"
                className="flex-1"
                loading={approving}
                onClick={handleApprove}
              >
                <CheckCircle className="w-4 h-4" />
                Approve
              </Button>
              <Button
                variant="ghost"
                className="flex-1 border border-red-800/40 text-red-400 hover:bg-red-900/10"
                loading={rejecting}
                onClick={handleReject}
              >
                <XCircle className="w-4 h-4" />
                Reject & Refund
              </Button>
            </div>
          </div>
        )}

        {!isPending && v.admin_notes && (
          <div className="card-surface p-5 rounded-xl space-y-2">
            <p className="text-stone-500 text-xs uppercase tracking-wider">Admin Notes</p>
            <p className="text-stone-300 text-sm">{v.admin_notes}</p>
            {v.reviewed_at && (
              <p className="text-stone-600 text-xs">Reviewed {new Date(v.reviewed_at).toLocaleString('en-GB')}</p>
            )}
          </div>
        )}
      </div>
    </AdminLayout>
  )
}
