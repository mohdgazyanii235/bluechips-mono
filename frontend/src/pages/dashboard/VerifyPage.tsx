import { useState, useRef, useEffect } from 'react'
import { Helmet } from 'react-helmet-async'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import {
  ChevronLeft, ShieldCheck, BadgeCheck, CheckCircle, Clock,
  X, Lock, XCircle, Camera, RotateCcw, AlertCircle,
} from 'lucide-react'
import { motion } from 'framer-motion'
import { DashboardLayout } from '@/components/layout/Layout'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import { useMyProfile } from '@/hooks/useEscorts'
import { uploadApi } from '@/api/upload'
import { paymentsApi } from '@/api/payments'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/api/client'
import toast from 'react-hot-toast'
import { cn } from '@/utils/cn'

// ─── Live camera capture component ───────────────────────────────────────────

type CaptureState = 'idle' | 'opening' | 'live' | 'captured'

function CameraCapture({ label, hint, mirror = false, onCapture }: {
  label: string
  hint: string
  mirror?: boolean
  onCapture: (file: File | null) => void
}) {
  const [captureState, setCaptureState] = useState<CaptureState>('idle')
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const stopStream = () => {
    streamRef.current?.getTracks().forEach(t => t.stop())
    streamRef.current = null
  }

  useEffect(() => () => {
    stopStream()
    if (previewUrl) URL.revokeObjectURL(previewUrl)
  }, [])

  const openCamera = async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      setError('Camera not available. Please use a modern browser (Chrome, Safari, Firefox) and ensure you are on HTTPS.')
      return
    }
    setError(null)
    setCaptureState('opening')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: mirror ? 'user' : { ideal: 'environment' }, width: { ideal: 1280 }, height: { ideal: 720 } },
      })
      streamRef.current = stream
      setCaptureState('live')
      // Let the video element mount before assigning srcObject
      requestAnimationFrame(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream
          videoRef.current.play().catch(() => {})
        }
      })
    } catch (err: any) {
      setCaptureState('idle')
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setError('Camera access denied. Please allow camera access in your browser settings and try again.')
      } else if (err.name === 'NotFoundError') {
        setError('No camera found on this device.')
      } else {
        setError('Could not start camera. Please try again or use a different browser.')
      }
    }
  }

  const capturePhoto = () => {
    if (!videoRef.current) return
    const video = videoRef.current
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth || 640
    canvas.height = video.videoHeight || 480
    const ctx = canvas.getContext('2d')!
    if (mirror) {
      ctx.translate(canvas.width, 0)
      ctx.scale(-1, 1)
    }
    ctx.drawImage(video, 0, 0)
    canvas.toBlob((blob) => {
      if (!blob) return
      const file = new File([blob], 'capture.jpg', { type: 'image/jpeg' })
      const url = URL.createObjectURL(blob)
      stopStream()
      if (previewUrl) URL.revokeObjectURL(previewUrl)
      setPreviewUrl(url)
      setCaptureState('captured')
      onCapture(file)
    }, 'image/jpeg', 0.92)
  }

  const retake = () => {
    stopStream()
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setPreviewUrl(null)
    setCaptureState('idle')
    onCapture(null)
  }

  if (captureState === 'idle' || captureState === 'opening') {
    return (
      <div className="space-y-2">
        <p className="text-xs uppercase tracking-wider text-stone-500 font-medium">{label}</p>
        {error && (
          <div className="flex items-start gap-2 p-3 rounded-lg bg-red-900/20 border border-red-800/30 text-red-400 text-xs">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            {error}
          </div>
        )}
        <button
          type="button"
          disabled={captureState === 'opening'}
          onClick={openCamera}
          className="w-full border-2 border-dashed border-surface-border hover:border-gold-400/40 rounded-xl p-8 text-center transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {captureState === 'opening' ? (
            <div className="space-y-2">
              <Spinner className="mx-auto" />
              <p className="text-stone-400 text-sm">Starting camera…</p>
            </div>
          ) : (
            <div className="space-y-2">
              <Camera className="w-8 h-8 text-stone-600 mx-auto" />
              <p className="text-stone-400 text-sm">Click to open camera</p>
              <p className="text-stone-600 text-xs">{hint}</p>
            </div>
          )}
        </button>
      </div>
    )
  }

  if (captureState === 'live') {
    return (
      <div className="space-y-2">
        <p className="text-xs uppercase tracking-wider text-stone-500 font-medium">{label}</p>
        <div className="relative rounded-xl overflow-hidden bg-black">
          <video
            ref={videoRef}
            className={cn('w-full max-h-72 object-cover', mirror && '[transform:scaleX(-1)]')}
            autoPlay
            playsInline
            muted
          />
          <div className="absolute inset-x-0 bottom-0 p-4 bg-gradient-to-t from-black/80 flex items-center justify-between gap-3">
            <p className="text-white/60 text-xs leading-tight max-w-[55%]">{hint}</p>
            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                onClick={() => { stopStream(); setCaptureState('idle') }}
                className="px-3 py-2 rounded-lg text-white/60 hover:text-white text-sm transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={capturePhoto}
                className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-white text-black font-semibold text-sm hover:bg-gray-100 transition-colors"
              >
                <Camera className="w-4 h-4" /> Take Photo
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // captured
  return (
    <div className="space-y-2">
      <p className="text-xs uppercase tracking-wider text-stone-500 font-medium">{label}</p>
      <div className="relative rounded-xl overflow-hidden border border-emerald-500/30">
        {previewUrl && (
          <img
            src={previewUrl}
            alt="Captured"
            className={cn('w-full max-h-72 object-cover', mirror && '[transform:scaleX(-1)]')}
          />
        )}
        <div className="absolute inset-x-0 bottom-0 p-3 bg-gradient-to-t from-black/70 flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-emerald-400 text-xs font-medium">
            <CheckCircle className="w-3.5 h-3.5" /> Photo captured
          </span>
          <button
            type="button"
            onClick={retake}
            className="flex items-center gap-1.5 text-white/60 hover:text-white text-xs transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" /> Retake
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export function VerifyPage() {
  const { data: escort, isLoading } = useMyProfile()
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [idFile, setIdFile] = useState<File | null>(null)
  const [selfieFile, setSelfieFile] = useState<File | null>(null)
  const [matchSelfieFile, setMatchSelfieFile] = useState<File | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [blueTickLoading, setBlueTickLoading] = useState(false)
  const [searchParams] = useSearchParams()
  const paymentSuccess = searchParams.get('payment') === 'success'

  const { data: verificationStatus } = useQuery({
    queryKey: ['verification-status'],
    queryFn: () => apiClient.get('/verification/status').then(r => r.data),
    enabled: !!escort,
  })

  const blueTickStatus = searchParams.get('blue_tick')

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ['escort', 'me'] })
    qc.invalidateQueries({ queryKey: ['verification-status'] })
  }

  const handleIdentitySubmit = async () => {
    if (!idFile || !selfieFile) {
      toast.error('Please take both photos before submitting')
      return
    }
    setSubmitting(true)
    try {
      await uploadApi.submitIdentityVerification(idFile, selfieFile)
      toast.success('Documents submitted! Review takes less than 1 hour — update your profile while you wait.')
      navigate('/dashboard/profile')
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Submission failed')
    } finally {
      setSubmitting(false)
    }
  }

  const handleBlueTickSubmit = async () => {
    if (!matchSelfieFile) {
      toast.error('Please take your matching selfie')
      return
    }
    setSubmitting(true)
    try {
      await uploadApi.submitBlueTick(matchSelfieFile)
      toast.success('Blue Tick request submitted! We will review within 1 hour.')
      refresh()
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Submission failed')
    } finally {
      setSubmitting(false)
    }
  }

  const handleBlueTickCheckout = async () => {
    setBlueTickLoading(true)
    try {
      const { url } = await paymentsApi.createBlueTickCheckout()
      window.location.href = url
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Could not start Blue Tick checkout')
    } finally {
      setBlueTickLoading(false)
    }
  }

  if (isLoading) return <DashboardLayout><Spinner fullPage /></DashboardLayout>
  if (!escort) return null

  const level = escort.verification_level
  const isPaid = escort.subscription_tier !== 'free'
  const isFree = !isPaid
  const hasBlueTickSub = escort.blue_tick_active || !!(escort as any).blue_tick_stripe_subscription_id

  const submissions: any[] = verificationStatus?.submissions ?? []
  const lastBlueTick = submissions.find((s: any) => s.level === 3)
  const lastIdentity = submissions.find((s: any) => s.level === 2)
  const blueTickRejected = lastBlueTick?.status === 'rejected'
  const identityRejected = lastIdentity?.status === 'rejected'
  const identityPending = lastIdentity?.status === 'pending'
  const blueTickPending = lastBlueTick?.status === 'pending'

  const tierLabel = escort.subscription_tier.charAt(0).toUpperCase() + escort.subscription_tier.slice(1)

  return (
    <DashboardLayout>
      <Helmet><title>Verification — Bluechips London</title></Helmet>

      <div className="page-container py-10">
        <div className="max-w-2xl mx-auto space-y-8">
          <div className="flex items-center gap-3">
            <Link to="/dashboard" className="text-stone-500 hover:text-gold-400 transition-colors">
              <ChevronLeft className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="font-serif text-3xl text-ivory-100">Verification</h1>
              <p className="text-stone-500 text-sm mt-0.5">Build trust. Get more clients.</p>
            </div>
          </div>

          {/* Payment success banner — redirected here after subscription checkout */}
          {paymentSuccess && (
            <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-3 p-4 rounded-xl bg-emerald-900/20 border border-emerald-500/30 text-emerald-400">
              <CheckCircle className="w-5 h-5 shrink-0" />
              <div>
                <p className="font-medium text-sm">Payment confirmed — your plan is now active!</p>
                <p className="text-emerald-600 text-xs mt-0.5">Next step: verify your identity below. Reviewed within 1 hour.</p>
              </div>
            </motion.div>
          )}

          {/* Blue tick payment result banners */}
          {blueTickStatus === 'success' && (
            <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-3 p-4 rounded-xl bg-blue-900/20 border border-blue-500/30 text-blue-400">
              <CheckCircle className="w-5 h-5 shrink-0" />
              <div>
                <p className="font-medium text-sm">Blue Tick subscription active!</p>
                <p className="text-blue-600 text-xs mt-0.5">Now take your matching selfie below to start the review.</p>
              </div>
            </motion.div>
          )}
          {blueTickStatus === 'cancelled' && (
            <div className="flex items-center gap-3 p-4 rounded-xl bg-stone-900/40 border border-stone-700 text-stone-400">
              <X className="w-5 h-5 shrink-0" />
              <p className="text-sm">Blue Tick checkout cancelled — no charge was made.</p>
            </div>
          )}

          {/* Step 1: Identity Verification */}
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="card-surface p-6 rounded-2xl space-y-6">
            <div className="flex items-start gap-4">
              <div className={cn('w-12 h-12 rounded-full border flex items-center justify-center shrink-0',
                level >= 2 ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-surface border-surface-border'
              )}>
                <ShieldCheck className={cn('w-6 h-6', level >= 2 ? 'text-emerald-400' : 'text-stone-600')} />
              </div>
              <div className="flex-1">
                <h2 className="font-serif text-xl text-ivory-100">
                  {isPaid ? 'Identity & Blue Tick Verification' : 'Step 1 — Identity Verification'}
                </h2>
                <p className="text-stone-500 text-sm mt-0.5">
                  {isPaid
                    ? `Included with your ${tierLabel} plan · Reviewed within 1 hour`
                    : 'Requires a paid subscription · Reviewed within 1 hour'}
                </p>
              </div>
              {level >= 2 && (
                <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-xs font-medium px-3 py-1 rounded-full flex items-center gap-1 shrink-0">
                  <CheckCircle className="w-3.5 h-3.5" /> Verified
                </span>
              )}
            </div>

            {!isPaid ? (
              <div className="space-y-3">
                <div className="flex items-start gap-3 p-4 rounded-xl bg-amber-900/20 border border-amber-800/30 text-amber-500">
                  <Lock className="w-5 h-5 shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-sm">Subscription required</p>
                    <p className="text-amber-700 text-xs mt-0.5">
                      Identity verification is available to Essential, Premium, and Elite subscribers. Subscribe first — if your verification is denied, you get a full refund.
                    </p>
                  </div>
                </div>
                <Link to="/dashboard/subscription">
                  <Button variant="gold" fullWidth>View Plans & Subscribe →</Button>
                </Link>
              </div>
            ) : level >= 2 ? (
              <div className="space-y-2">
                <p className="text-stone-500 text-sm">Your identity has been verified.</p>
                {isPaid && level >= 3 && (
                  <p className="text-blue-400 text-sm flex items-center gap-1.5">
                    <BadgeCheck className="w-4 h-4" /> Blue Tick badge is active on your profile.
                  </p>
                )}
              </div>
            ) : identityPending ? (
              <div className="flex items-center gap-3 p-4 rounded-xl bg-amber-900/15 border border-amber-800/30 text-amber-400">
                <Clock className="w-5 h-5 shrink-0" />
                <div>
                  <p className="font-medium text-sm">Under review</p>
                  <p className="text-amber-700 text-xs mt-0.5">Your documents are being reviewed. This takes less than 1 hour.</p>
                </div>
              </div>
            ) : (
              <>
                {identityRejected && (
                  <div className="flex items-start gap-3 p-4 rounded-xl bg-red-900/20 border border-red-800/30 text-red-400">
                    <XCircle className="w-5 h-5 shrink-0 mt-0.5" />
                    <div>
                      <p className="font-medium text-sm">Application not approved</p>
                      {lastIdentity?.admin_notes && (
                        <p className="text-stone-400 text-sm mt-1">{lastIdentity.admin_notes}</p>
                      )}
                      <p className="text-stone-600 text-xs mt-1">Your subscription has been refunded. Please re-subscribe and submit again.</p>
                    </div>
                  </div>
                )}

                {isPaid && (
                  <div className="flex items-start gap-3 p-3 rounded-xl bg-blue-900/10 border border-blue-500/20 text-blue-400 text-xs">
                    <BadgeCheck className="w-4 h-4 shrink-0 mt-0.5" />
                    <p>Your <strong>{tierLabel}</strong> plan includes the Blue Tick badge for free. Verifying your identity will activate it automatically — no extra charge.</p>
                  </div>
                )}

                <div className="p-4 rounded-xl bg-surface border border-surface-border text-stone-400 text-sm space-y-3">
                  <p className="font-medium text-ivory-300">What you need to do:</p>
                  <ol className="space-y-2 text-stone-500 text-sm list-decimal list-inside">
                    <li>Take a clear live selfie — your face must be fully visible</li>
                    <li>Take a photo of your government-issued ID (passport or driving licence)</li>
                  </ol>
                  <p className="text-stone-600 text-xs border-t border-surface-border pt-3">
                    🔒 Your documents are never stored permanently. They are deleted automatically as soon as our team reviews your application — whether approved or rejected.
                  </p>
                </div>

                <div className="space-y-5">
                  <CameraCapture
                    label="Live Selfie"
                    hint="Look directly at the camera. Your face must be clearly visible and well-lit."
                    mirror={true}
                    onCapture={setSelfieFile}
                  />
                  <CameraCapture
                    label="Government-issued ID"
                    hint="Hold your passport or driving licence clearly in front of the camera. Ensure all text is readable."
                    onCapture={setIdFile}
                  />
                </div>

                <Button
                  variant="gold"
                  fullWidth
                  size="lg"
                  loading={submitting}
                  disabled={!idFile || !selfieFile}
                  onClick={handleIdentitySubmit}
                >
                  Submit for Review
                </Button>
              </>
            )}
          </motion.div>

          {/* Step 2: Blue Tick — only shown for Essential tier (paid add-on for £10 + £3.99/mo) */}
          {/* Premium/Elite get Blue Tick automatically on identity approval — no separate step needed */}
          {escort.subscription_tier === 'essential' && (
            <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="card-surface p-6 rounded-2xl space-y-6">
              <div className="flex items-start gap-4">
                <div className={cn('w-12 h-12 rounded-full border flex items-center justify-center shrink-0',
                  level >= 3 ? 'bg-blue-500/10 border-blue-500/30' : 'bg-surface border-surface-border'
                )}>
                  <BadgeCheck className={cn('w-6 h-6', level >= 3 ? 'text-blue-400' : 'text-stone-600')} />
                </div>
                <div className="flex-1">
                  <h2 className="font-serif text-xl text-ivory-100">Blue Tick Add-on</h2>
                  <p className="text-stone-500 text-sm mt-0.5">£10 setup + £3.99/month · Reviewed within 1 hour</p>
                </div>
                {level >= 3 && (
                  <span className="bg-blue-500/10 text-blue-400 border border-blue-500/30 text-xs font-medium px-3 py-1 rounded-full flex items-center gap-1 shrink-0">
                    <BadgeCheck className="w-3.5 h-3.5" /> Active
                  </span>
                )}
              </div>

              {level < 2 ? (
                <div className="flex items-center gap-2 text-stone-500 text-sm p-4 rounded-xl bg-surface border border-surface-border">
                  <Clock className="w-4 h-4 shrink-0" />
                  Complete identity verification (Step 1 above) first.
                </div>
              ) : level >= 3 ? (
                <p className="text-stone-500 text-sm">You have the Blue Tick. Your profile photos are verified as genuine.</p>
              ) : blueTickPending ? (
                <div className="flex items-center gap-3 p-4 rounded-xl bg-amber-900/15 border border-amber-800/30 text-amber-400">
                  <Clock className="w-5 h-5 shrink-0" />
                  <div>
                    <p className="font-medium text-sm">Under review</p>
                    <p className="text-amber-700 text-xs mt-0.5">Your selfie has been submitted and is being reviewed. This takes less than 1 hour.</p>
                  </div>
                </div>
              ) : !hasBlueTickSub ? (
                <div className="space-y-4">
                  {blueTickRejected && (
                    <div className="flex items-start gap-3 p-4 rounded-xl bg-red-900/20 border border-red-800/30 text-red-400">
                      <XCircle className="w-5 h-5 shrink-0 mt-0.5" />
                      <div>
                        <p className="font-medium text-sm">Blue Tick application not approved</p>
                        {lastBlueTick?.admin_notes && (
                          <p className="text-stone-400 text-sm mt-1">{lastBlueTick.admin_notes}</p>
                        )}
                        <p className="text-stone-600 text-xs mt-1">Your payment has been refunded. You can apply again below.</p>
                      </div>
                    </div>
                  )}
                  <div className="p-4 rounded-xl bg-blue-900/10 border border-blue-500/20 text-stone-400 text-sm space-y-1">
                    <p><strong className="text-ivory-200">What is the Blue Tick?</strong></p>
                    <p className="text-stone-500 text-sm">We compare a live selfie to your profile photos to confirm you are genuine. Once approved, a blue tick badge appears on your profile — clients trust blue tick profiles significantly more.</p>
                    <div className="flex items-center gap-4 pt-2 text-xs text-stone-600">
                      <span>£10 one-time application fee</span>
                      <span>·</span>
                      <span>£3.99/month to keep it active</span>
                      <span>·</span>
                      <span>Cancel anytime</span>
                    </div>
                  </div>
                  <Button variant="gold" fullWidth size="lg" loading={blueTickLoading} onClick={handleBlueTickCheckout}>
                    Subscribe to Blue Tick — £10 + £3.99/mo
                  </Button>
                </div>
              ) : (
                <>
                  <div className="p-4 rounded-xl bg-blue-500/5 border border-blue-500/20 text-stone-400 text-sm space-y-2">
                    <p><strong className="text-ivory-300">Take your matching selfie:</strong></p>
                    <ul className="list-disc list-inside space-y-1 text-stone-500 text-sm">
                      <li>Take a selfie in the same pose or setting as one of your profile photos</li>
                      <li>Our team will compare them to confirm your photos are genuinely you</li>
                    </ul>
                    <p className="text-stone-600 text-xs border-t border-surface-border pt-3">
                      🔒 This photo is deleted automatically once our team reviews your application.
                    </p>
                  </div>
                  <CameraCapture
                    label="Matching selfie"
                    hint="Match the pose or setting from one of your profile photos. Face must be clearly visible."
                    mirror={true}
                    onCapture={setMatchSelfieFile}
                  />
                  <Button
                    variant="gold"
                    fullWidth
                    size="lg"
                    loading={submitting}
                    disabled={!matchSelfieFile}
                    onClick={handleBlueTickSubmit}
                  >
                    Submit Blue Tick Application
                  </Button>
                </>
              )}
            </motion.div>
          )}

          <p className="text-center text-stone-700 text-xs leading-relaxed">
            All verification photos are reviewed by our team and deleted immediately after a decision is made. They are never shared publicly or with third parties.
          </p>
        </div>
      </div>
    </DashboardLayout>
  )
}
