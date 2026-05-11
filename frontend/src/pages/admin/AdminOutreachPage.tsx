import React, { useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus, Save, Loader2, X, Copy, Sparkles, RefreshCw, Trash2,
  CheckCircle2, MessageSquare, Send, ChevronDown, Mail,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { AdminLayout } from './AdminLayout'
import { adminApi, OutreachProspect, OutreachRowInput } from '@/api/admin'
import { cn } from '@/utils/cn'

type Status = OutreachProspect['status']

const STATUSES: { value: Status; label: string; colour: string }[] = [
  { value: 'not_contacted', label: 'Not contacted', colour: 'bg-stone-800 text-stone-400 border-stone-700' },
  { value: 'contacted',     label: 'Contacted',     colour: 'bg-blue-900/30 text-blue-300 border-blue-700/40' },
  { value: 'replied',       label: 'Replied',       colour: 'bg-amber-900/30 text-amber-300 border-amber-700/40' },
  { value: 'signed_up',     label: 'Signed up',     colour: 'bg-emerald-900/30 text-emerald-300 border-emerald-700/40' },
  { value: 'declined',      label: 'Declined',      colour: 'bg-red-900/20 text-red-400 border-red-800/40' },
]

const statusMeta = (s: Status) => STATUSES.find(x => x.value === s) ?? STATUSES[0]

type DraftRow = {
  // Unique key for React; mirrors server id when persisted
  key: string
  id?: string
  x_handle: string
  stage_name: string
  area: string
  specialty: string
  note: string
  status: Status
  generated_message: string | null
  discount_code: string | null
  admin_notes: string
  contacted_at: string | null
  signed_up_at: string | null
  dirty: boolean
  isNew: boolean
}

function emptyDraft(): DraftRow {
  return {
    key: crypto.randomUUID(),
    x_handle: '',
    stage_name: '',
    area: '',
    specialty: '',
    note: '',
    status: 'not_contacted',
    generated_message: null,
    discount_code: null,
    admin_notes: '',
    contacted_at: null,
    signed_up_at: null,
    dirty: true,
    isNew: true,
  }
}

function fromServer(p: OutreachProspect): DraftRow {
  return {
    key: p.id,
    id: p.id,
    x_handle: p.x_handle,
    stage_name: p.stage_name,
    area: p.area ?? '',
    specialty: p.specialty ?? '',
    note: p.note ?? '',
    status: p.status,
    generated_message: p.generated_message,
    discount_code: p.discount_code,
    admin_notes: p.admin_notes ?? '',
    contacted_at: p.contacted_at,
    signed_up_at: p.signed_up_at,
    dirty: false,
    isNew: false,
  }
}

function toUpsert(d: DraftRow): OutreachRowInput {
  return {
    id: d.id,
    x_handle: d.x_handle.trim().replace(/^@/, ''),
    stage_name: d.stage_name.trim(),
    area: d.area.trim() || null,
    specialty: d.specialty.trim() || null,
    note: d.note.trim() || null,
    status: d.status,
    admin_notes: d.admin_notes || null,
  }
}

export function AdminOutreachPage() {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: ['admin-outreach'], queryFn: adminApi.listOutreach })

  const [draftRows, setDraftRows] = useState<DraftRow[]>([])
  const [messageModal, setMessageModal] = useState<{ open: boolean; key: string; message: string; code: string } | null>(null)
  const [statusFilter, setStatusFilter] = useState<Status | 'all'>('all')

  // Merge server data + local drafts (new unsaved rows)
  const allRows = useMemo<DraftRow[]>(() => {
    const serverRows: DraftRow[] = (data?.items ?? []).map(fromServer)
    // Apply any local edits on top of server rows
    const localById: Record<string, DraftRow> = {}
    for (const dr of draftRows) {
      if (dr.id) localById[dr.id] = dr
    }
    const merged = serverRows.map(sr => localById[sr.id!] ?? sr)
    const newRows = draftRows.filter(r => r.isNew)
    return [...newRows, ...merged]
  }, [data, draftRows])

  const visibleRows = useMemo(() => {
    if (statusFilter === 'all') return allRows
    return allRows.filter(r => r.status === statusFilter)
  }, [allRows, statusFilter])

  const counts = data?.counts ?? {}
  const dirtyCount = draftRows.filter(r => r.dirty).length

  // ── Mutations ────────────────────────────────────────────────────────────

  const saveMutation = useMutation({
    mutationFn: async (rows: OutreachRowInput[]) => adminApi.bulkUpsertOutreach(rows),
    onSuccess: (res) => {
      if (res.failures.length > 0) {
        toast.error(`${res.failures.length} row(s) failed: ${res.failures[0].reason}`)
      }
      const okLabel = []
      if (res.created) okLabel.push(`${res.created} created`)
      if (res.updated) okLabel.push(`${res.updated} updated`)
      if (okLabel.length) toast.success(okLabel.join(' · '))
      setDraftRows([])
      qc.invalidateQueries({ queryKey: ['admin-outreach'] })
    },
    onError: (err: any) => toast.error(err?.response?.data?.detail ?? 'Save failed'),
  })

  const deleteMutation = useMutation({
    mutationFn: adminApi.deleteOutreach,
    onSuccess: () => {
      toast.success('Deleted')
      qc.invalidateQueries({ queryKey: ['admin-outreach'] })
    },
  })

  const generateMutation = useMutation({
    mutationFn: async (vars: { id: string; regenerate: boolean }) =>
      adminApi.generateOutreachMessage(vars.id, vars.regenerate),
    onSuccess: (res, vars) => {
      setMessageModal({ open: true, key: vars.id, message: res.message, code: res.code })
      qc.invalidateQueries({ queryKey: ['admin-outreach'] })
    },
    onError: (err: any) => toast.error(err?.response?.data?.detail ?? 'Generation failed'),
  })

  const markContactedMutation = useMutation({
    mutationFn: adminApi.markOutreachContacted,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-outreach'] }),
  })

  const updateStatusMutation = useMutation({
    mutationFn: async (vars: { id: string; status: Status }) => adminApi.updateOutreach(vars.id, { status: vars.status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin-outreach'] }),
  })

  // ── Row handlers ──────────────────────────────────────────────────────────

  const addRow = () => {
    setDraftRows(rows => [emptyDraft(), ...rows])
  }

  const addBatch = (n: number) => {
    setDraftRows(rows => [...Array.from({ length: n }, () => emptyDraft()), ...rows])
  }

  const updateLocal = (key: string, patch: Partial<DraftRow>) => {
    setDraftRows(rows => {
      // If this row is in drafts, update it; else, push a new draft based on the server row
      const existing = rows.find(r => r.key === key)
      if (existing) {
        return rows.map(r => r.key === key ? { ...r, ...patch, dirty: true } : r)
      }
      const serverRow = data?.items.find(p => p.id === key)
      if (!serverRow) return rows
      return [...rows, { ...fromServer(serverRow), ...patch, dirty: true }]
    })
  }

  const cancelDraft = (key: string) => {
    setDraftRows(rows => rows.filter(r => r.key !== key))
  }

  const removeRow = (row: DraftRow) => {
    if (row.isNew) {
      cancelDraft(row.key)
      return
    }
    if (!row.id) return
    if (!confirm(`Delete prospect @${row.x_handle}?`)) return
    deleteMutation.mutate(row.id)
  }

  const saveAll = () => {
    const dirty = draftRows.filter(r => r.dirty)
    const valid = dirty.filter(r => r.x_handle.trim() && r.stage_name.trim())
    if (valid.length === 0) {
      toast.error('Add at least an X handle and stage name')
      return
    }
    saveMutation.mutate(valid.map(toUpsert))
  }

  const generateForRow = (row: DraftRow, regenerate = false) => {
    if (!row.id) {
      toast.error('Save the row first')
      return
    }
    generateMutation.mutate({ id: row.id, regenerate })
  }

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <AdminLayout>
      <div className="space-y-6 max-w-[1400px]">
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <h1 className="font-serif text-2xl text-ivory-100">Outreach CRM</h1>
            <p className="text-stone-500 text-sm mt-1">
              X DM outreach to companion prospects. Each row gets a unique founding code automatically.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => addRow()}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-surface-border bg-stone-900 text-stone-300 hover:border-gold-400/40 hover:text-ivory-100 text-sm transition-colors"
            >
              <Plus className="w-4 h-4" /> Add row
            </button>
            <button
              onClick={() => addBatch(10)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-surface-border bg-stone-900 text-stone-300 hover:border-gold-400/40 hover:text-ivory-100 text-sm transition-colors"
            >
              +10 rows
            </button>
            <button
              onClick={saveAll}
              disabled={dirtyCount === 0 || saveMutation.isPending}
              className="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-gold-400 text-black font-semibold hover:bg-gold-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            >
              {saveMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              Save {dirtyCount > 0 && `(${dirtyCount})`}
            </button>
          </div>
        </div>

        {/* Funnel metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <FunnelCard label="Total" value={counts.total ?? 0} onClick={() => setStatusFilter('all')} active={statusFilter === 'all'} colour="bg-surface-card border-surface-border" />
          {STATUSES.map(s => (
            <FunnelCard
              key={s.value}
              label={s.label}
              value={counts[s.value] ?? 0}
              onClick={() => setStatusFilter(s.value)}
              active={statusFilter === s.value}
              colour={s.colour}
            />
          ))}
        </div>

        {/* Table */}
        <div className="bg-stone-900 border border-surface-border rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-border bg-black/30 text-stone-500 text-[11px] uppercase tracking-widest">
                  <th className="text-left px-3 py-3 font-medium">X handle</th>
                  <th className="text-left px-3 py-3 font-medium">Stage name</th>
                  <th className="text-left px-3 py-3 font-medium">Area</th>
                  <th className="text-left px-3 py-3 font-medium">Specialty</th>
                  <th className="text-left px-3 py-3 font-medium">Note (what you saw)</th>
                  <th className="text-left px-3 py-3 font-medium">Code</th>
                  <th className="text-left px-3 py-3 font-medium">Status</th>
                  <th className="text-right px-3 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {isLoading && (
                  <tr><td colSpan={8} className="text-center py-16 text-stone-500"><Loader2 className="w-5 h-5 animate-spin inline mr-2" /> Loading…</td></tr>
                )}
                {!isLoading && visibleRows.length === 0 && (
                  <tr><td colSpan={8} className="text-center py-16 text-stone-500">
                    No prospects yet. Click <strong className="text-stone-300">Add row</strong> to start.
                  </td></tr>
                )}
                {visibleRows.map(row => (
                  <Row
                    key={row.key}
                    row={row}
                    onChange={(patch) => updateLocal(row.key, patch)}
                    onCancel={() => cancelDraft(row.key)}
                    onDelete={() => removeRow(row)}
                    onGenerate={() => generateForRow(row)}
                    onRegenerate={() => generateForRow(row, true)}
                    onShowMessage={() => row.id && row.generated_message ? setMessageModal({ open: true, key: row.id, message: row.generated_message, code: row.discount_code ?? '' }) : null}
                    onMarkContacted={() => row.id && markContactedMutation.mutate(row.id)}
                    onStatusChange={(status) => {
                      // If row is unsaved, just update locally; if saved, persist immediately
                      if (row.id) {
                        updateStatusMutation.mutate({ id: row.id, status })
                      }
                      updateLocal(row.key, { status })
                    }}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Help banner */}
        <div className="p-4 rounded-xl border border-stone-800 bg-stone-950 text-stone-500 text-xs leading-relaxed">
          <p className="mb-1.5"><strong className="text-stone-400">Workflow:</strong> add rows → fill in X handle + stage name (minimum) → save → click ✨ to generate a unique DM → copy → paste into X → mark Contacted.</p>
          <p>The founding offer terms (months, %, tier) come from <a href="/admin/founding-offer" className="text-gold-400 hover:text-gold-300">Founding Offer settings</a>. Each prospect gets a unique <strong className="text-stone-400">FM-XXXXX</strong> discount code visible in the <a href="/admin/discounts" className="text-gold-400 hover:text-gold-300">Discounts page</a> alongside your other codes.</p>
        </div>

        {/* Email drip for incomplete profiles */}
        <DripCard />
      </div>

      {/* Message modal */}
      {messageModal?.open && (
        <MessageModal
          message={messageModal.message}
          code={messageModal.code}
          onClose={() => setMessageModal(null)}
          onRegenerate={() => generateMutation.mutate({ id: messageModal.key, regenerate: true })}
          onMarkContacted={() => {
            markContactedMutation.mutate(messageModal.key)
            setMessageModal(null)
          }}
        />
      )}
    </AdminLayout>
  )
}

function DripCard() {
  const [daysOld, setDaysOld] = useState(2)
  const previewQuery = useQuery({
    queryKey: ['drip-preview', daysOld],
    queryFn: () => adminApi.previewProfileCompletionDrip(daysOld),
  })
  const sendMutation = useMutation({
    mutationFn: () => adminApi.sendProfileCompletionDrip(daysOld),
    onSuccess: (res) => {
      toast.success(res.message)
      previewQuery.refetch()
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? 'Send failed'),
  })

  const eligibleCount = previewQuery.data?.count ?? 0

  return (
    <div className="bg-stone-900 border border-surface-border rounded-xl p-5 space-y-4">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h3 className="font-serif text-lg text-ivory-100 flex items-center gap-2"><Mail className="w-4 h-4 text-gold-400" /> Profile completion drip</h3>
          <p className="text-stone-500 text-sm mt-1">Send a reminder email to escorts who verified their email but haven't completed their profile.</p>
        </div>
        <div className="flex items-center gap-3">
          <label className="text-stone-500 text-xs flex items-center gap-2">
            Min age (days):
            <input
              type="number"
              value={daysOld}
              min={1}
              max={30}
              onChange={e => setDaysOld(Number(e.target.value))}
              className="w-16 bg-surface border border-surface-border rounded px-2 py-1 text-ivory-200 text-sm focus:outline-none focus:border-gold-400/60"
            />
          </label>
          <button
            onClick={() => {
              if (eligibleCount === 0) return
              if (!confirm(`Send completion-reminder email to ${eligibleCount} escort(s)?`)) return
              sendMutation.mutate()
            }}
            disabled={eligibleCount === 0 || sendMutation.isPending}
            className="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-gold-400 text-black font-semibold hover:bg-gold-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
          >
            {sendMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            Send to {eligibleCount}
          </button>
        </div>
      </div>
      {previewQuery.isLoading ? (
        <p className="text-stone-600 text-xs">Loading eligible escorts…</p>
      ) : eligibleCount === 0 ? (
        <p className="text-stone-600 text-xs">No eligible escorts right now. Anyone who registered more than {daysOld} day(s) ago, verified email, and hasn't finished their profile will appear here.</p>
      ) : (
        <details className="text-xs">
          <summary className="text-stone-400 cursor-pointer hover:text-ivory-200">Show {eligibleCount} eligible escort(s)</summary>
          <div className="mt-2 max-h-48 overflow-y-auto space-y-1 pl-2">
            {previewQuery.data?.items.map(item => (
              <div key={item.id} className="flex items-center gap-2 text-stone-500">
                <span className="text-ivory-200">{item.stage_name}</span>
                <span className="text-stone-600">·</span>
                <span className="font-mono">{item.email}</span>
                <span className="text-stone-700">·</span>
                <span>registered {new Date(item.created_at).toLocaleDateString('en-GB')}</span>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  )
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function FunnelCard({ label, value, onClick, active, colour }: { label: string; value: number; onClick: () => void; active: boolean; colour: string }) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'text-left p-3 rounded-lg border transition-all',
        colour,
        active ? 'ring-1 ring-gold-400/40' : 'opacity-70 hover:opacity-100',
      )}
    >
      <p className="text-[10px] uppercase tracking-widest opacity-70">{label}</p>
      <p className="text-xl font-serif mt-1">{value}</p>
    </button>
  )
}

function Cell({ value, onChange, placeholder, mono }: { value: string; onChange: (v: string) => void; placeholder?: string; mono?: boolean }) {
  return (
    <input
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className={cn(
        'w-full bg-transparent border border-transparent hover:border-stone-700 focus:border-gold-400/60 focus:bg-black/40 rounded px-2 py-1.5 text-ivory-100 text-sm outline-none transition-colors placeholder-stone-700',
        mono && 'font-mono',
      )}
    />
  )
}

function Row({
  row, onChange, onCancel, onDelete, onGenerate, onRegenerate, onShowMessage, onMarkContacted, onStatusChange,
}: {
  row: DraftRow
  onChange: (p: Partial<DraftRow>) => void
  onCancel: () => void
  onDelete: () => void
  onGenerate: () => void
  onRegenerate: () => void
  onShowMessage: () => void
  onMarkContacted: () => void
  onStatusChange: (s: Status) => void
}) {
  const meta = statusMeta(row.status)
  return (
    <tr className={cn(
      'border-b border-surface-border last:border-b-0 hover:bg-black/20 transition-colors',
      row.isNew && 'bg-gold-900/5',
      row.dirty && !row.isNew && 'bg-blue-900/5',
    )}>
      <td className="px-2 py-1 w-40">
        <Cell value={row.x_handle} onChange={v => onChange({ x_handle: v.replace(/^@/, '') })} placeholder="@handle" mono />
      </td>
      <td className="px-2 py-1 w-36">
        <Cell value={row.stage_name} onChange={v => onChange({ stage_name: v })} placeholder="Stage name" />
      </td>
      <td className="px-2 py-1 w-32">
        <Cell value={row.area} onChange={v => onChange({ area: v })} placeholder="Mayfair, etc." />
      </td>
      <td className="px-2 py-1 w-32">
        <Cell value={row.specialty} onChange={v => onChange({ specialty: v })} placeholder="GFE, etc." />
      </td>
      <td className="px-2 py-1 min-w-[200px]">
        <Cell value={row.note} onChange={v => onChange({ note: v })} placeholder="e.g. her own website, complains about fees" />
      </td>
      <td className="px-2 py-1 w-32">
        {row.discount_code ? (
          <button
            onClick={() => { navigator.clipboard.writeText(row.discount_code!); toast.success('Code copied') }}
            className="text-xs font-mono text-gold-400 hover:text-gold-300 flex items-center gap-1"
            title="Copy code"
          >
            <Copy className="w-3 h-3" /> {row.discount_code}
          </button>
        ) : (
          <span className="text-stone-700 text-xs italic">save to generate</span>
        )}
      </td>
      <td className="px-2 py-1 w-36">
        <select
          value={row.status}
          onChange={e => onStatusChange(e.target.value as Status)}
          disabled={!row.id}
          className={cn(
            'text-xs px-2 py-1 rounded border outline-none cursor-pointer',
            meta.colour,
            !row.id && 'opacity-50 cursor-not-allowed',
          )}
        >
          {STATUSES.map(s => (
            <option key={s.value} value={s.value} className="bg-black text-ivory-200">{s.label}</option>
          ))}
        </select>
      </td>
      <td className="px-2 py-1 w-auto">
        <div className="flex items-center gap-1 justify-end">
          {row.isNew ? (
            <button onClick={onCancel} title="Cancel" className="p-1.5 rounded hover:bg-red-900/20 text-stone-500 hover:text-red-400 transition-colors">
              <X className="w-4 h-4" />
            </button>
          ) : (
            <>
              {row.generated_message ? (
                <button onClick={onShowMessage} title="View message" className="p-1.5 rounded hover:bg-blue-900/20 text-stone-400 hover:text-blue-400 transition-colors">
                  <MessageSquare className="w-4 h-4" />
                </button>
              ) : null}
              <button onClick={onGenerate} title="Generate message" className="p-1.5 rounded hover:bg-gold-900/20 text-stone-400 hover:text-gold-400 transition-colors">
                <Sparkles className="w-4 h-4" />
              </button>
              {row.status === 'not_contacted' && (
                <button onClick={onMarkContacted} title="Mark contacted" className="p-1.5 rounded hover:bg-emerald-900/20 text-stone-400 hover:text-emerald-400 transition-colors">
                  <Send className="w-4 h-4" />
                </button>
              )}
              <button onClick={onDelete} title="Delete" className="p-1.5 rounded hover:bg-red-900/20 text-stone-500 hover:text-red-400 transition-colors">
                <Trash2 className="w-4 h-4" />
              </button>
            </>
          )}
        </div>
      </td>
    </tr>
  )
}

function MessageModal({ message, code, onClose, onRegenerate, onMarkContacted }: { message: string; code: string; onClose: () => void; onRegenerate: () => void; onMarkContacted: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4" onClick={onClose}>
      <div className="bg-stone-950 border border-surface-border rounded-2xl max-w-2xl w-full p-6 space-y-5" onClick={e => e.stopPropagation()}>
        <div className="flex items-start justify-between">
          <div>
            <h3 className="font-serif text-xl text-ivory-100">Generated DM</h3>
            <p className="text-stone-500 text-xs mt-1">Code: <span className="font-mono text-gold-400">{code}</span></p>
          </div>
          <button onClick={onClose} className="p-1 rounded hover:bg-stone-900 text-stone-500 hover:text-ivory-200">
            <X className="w-5 h-5" />
          </button>
        </div>

        <pre className="whitespace-pre-wrap text-sm text-ivory-200 leading-relaxed bg-black/40 rounded-lg p-4 border border-surface-border font-sans">
          {message}
        </pre>

        <div className="flex items-center justify-between gap-2 flex-wrap">
          <button onClick={onRegenerate} className="flex items-center gap-2 px-3 py-2 rounded-lg border border-surface-border bg-stone-900 hover:border-gold-400/40 text-stone-300 hover:text-ivory-100 text-sm transition-colors">
            <RefreshCw className="w-4 h-4" /> Regenerate
          </button>
          <div className="flex items-center gap-2">
            <button onClick={() => { navigator.clipboard.writeText(message); toast.success('Copied') }} className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gold-400 text-black font-semibold hover:bg-gold-300 text-sm transition-colors">
              <Copy className="w-4 h-4" /> Copy DM
            </button>
            <button onClick={onMarkContacted} className="flex items-center gap-2 px-4 py-2 rounded-lg border border-emerald-700/50 bg-emerald-900/20 text-emerald-300 hover:bg-emerald-900/30 text-sm transition-colors">
              <CheckCircle2 className="w-4 h-4" /> Mark contacted
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
