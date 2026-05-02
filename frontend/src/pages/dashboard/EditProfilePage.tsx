import { useState, useEffect, useCallback } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { Helmet } from 'react-helmet-async'
import { Link, useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Upload, Trash2, Star, ImagePlus,
  User, Sparkles, MessageSquare, MapPin, PoundSterling, Phone, Camera,
} from 'lucide-react'
import { DashboardLayout } from '@/components/layout/Layout'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import { useMyProfile } from '@/hooks/useEscorts'
import { useBoroughs } from '@/hooks/useBoroughs'
import { uploadApi } from '@/api/upload'
import { escortsApi } from '@/api/escorts'
import { useQueryClient } from '@tanstack/react-query'
import { SERVICE_TAGS, ETHNICITIES, BUILD_TYPES, LANGUAGES } from '@/types/escort'
import { cn } from '@/utils/cn'
import toast from 'react-hot-toast'

const schema = z.object({
  stage_name: z.string().min(2).max(50).optional().or(z.literal('')),
  age: z.coerce.number().min(18).max(99).optional().or(z.literal('')),
  nationality: z.string().optional(),
  ethnicity: z.string().optional(),
  profile_type: z.enum(['individual', 'couple']).optional(),
  height_cm: z.coerce.number().min(140).max(210).optional().or(z.literal('')),
  build: z.string().optional(),
  hair_colour: z.string().optional(),
  eye_colour: z.string().optional(),
  dress_size: z.string().optional(),
  chest: z.string().optional(),
  about_me: z.string().max(600).optional(),
  borough_id: z.string().optional(),
  availability_type: z.string().optional(),
  booking_notice: z.string().max(100).optional(),
  rate_30min: z.coerce.number().min(0).optional().or(z.literal('')),
  rate_1hour: z.coerce.number().min(0).optional().or(z.literal('')),
  rate_2hours: z.coerce.number().min(0).optional().or(z.literal('')),
  rate_overnight: z.coerce.number().min(0).optional().or(z.literal('')),
  whatsapp_number: z.string().max(30).optional(),
  phone_number: z.string().max(30).optional(),
  std_tested: z.boolean().optional(),
  std_tested_date: z.string().optional(),
})

type FormData = z.infer<typeof schema>

const STEPS = [
  { label: 'Basics',   icon: User,           title: 'The Basics',              subtitle: "Let's start with who you are" },
  { label: 'Look',     icon: Sparkles,        title: 'Your Look',               subtitle: 'Help clients picture you' },
  { label: 'About',    icon: MessageSquare,   title: 'About You',               subtitle: 'Tell clients what you\'re about' },
  { label: 'Location', icon: MapPin,          title: 'Location & Availability', subtitle: 'Where and when can clients book you?' },
  { label: 'Rates',    icon: PoundSterling,   title: 'Your Rates',              subtitle: 'Set your time rates in GBP — leave blank to hide' },
  { label: 'Contact',  icon: Phone,           title: 'Contact & Services',      subtitle: 'How clients reach you and what you offer' },
  { label: 'Photos',   icon: Camera,          title: 'Your Photos',             subtitle: 'Great photos get 10× more enquiries' },
]

function ChipSelect({
  options,
  selected,
  onChange,
}: {
  options: readonly string[]
  selected: string[]
  onChange: (values: string[]) => void
}) {
  const toggle = (val: string) =>
    onChange(selected.includes(val) ? selected.filter(v => v !== val) : [...selected, val])

  return (
    <div className="flex flex-wrap gap-2">
      {options.map(opt => (
        <button
          key={opt}
          type="button"
          onClick={() => toggle(opt)}
          className={cn(
            'px-3 py-1.5 rounded-full text-sm border transition-all',
            selected.includes(opt)
              ? 'bg-gold-400/10 border-gold-400/50 text-gold-400'
              : 'border-surface-border text-stone-500 hover:border-stone-600 hover:text-stone-300'
          )}
        >
          {opt}
        </button>
      ))}
    </div>
  )
}

export function EditProfilePage() {
  const navigate = useNavigate()
  const { data: escort, isLoading } = useMyProfile()
  const { data: boroughs = [] } = useBoroughs()
  const qc = useQueryClient()

  const [step, setStep] = useState(1)
  const [isSaving, setIsSaving] = useState(false)
  const [languages, setLanguages] = useState<string[]>([])
  const [serviceTags, setServiceTags] = useState<string[]>([])

  const { register, watch, reset, setValue } = useForm<FormData>()

  useEffect(() => {
    if (escort) {
      reset({
        stage_name: escort.stage_name ?? '',
        age: escort.age ?? '',
        nationality: escort.nationality ?? '',
        ethnicity: escort.ethnicity ?? '',
        profile_type: (escort.profile_type as 'individual' | 'couple') ?? 'individual',
        height_cm: escort.height_cm ?? '',
        build: escort.build ?? '',
        hair_colour: escort.hair_colour ?? '',
        eye_colour: escort.eye_colour ?? '',
        dress_size: escort.dress_size ?? '',
        chest: escort.chest ?? '',
        about_me: escort.about_me ?? '',
        borough_id: escort.borough_id ?? '',
        availability_type: escort.availability_type ?? '',
        booking_notice: escort.booking_notice ?? '',
        rate_30min: escort.rate_30min ?? '',
        rate_1hour: escort.rate_1hour ?? '',
        rate_2hours: escort.rate_2hours ?? '',
        rate_overnight: escort.rate_overnight ?? '',
        whatsapp_number: escort.whatsapp_number ?? '',
        phone_number: escort.phone_number ?? '',
        std_tested: escort.std_tested ?? false,
        std_tested_date: escort.std_tested_date ?? '',
      })
      setLanguages(escort.languages ?? [])
      setServiceTags(escort.service_tags ?? [])
    }
  }, [escort, reset])

  const values = watch()

  const saveStep = async () => {
    const clean = (v: any) => (v === '' ? undefined : v)
    let payload: Record<string, any> = {}

    switch (step) {
      case 1:
        payload = {
          stage_name: clean(values.stage_name),
          age: clean(values.age),
          nationality: clean(values.nationality),
          ethnicity: clean(values.ethnicity),
          profile_type: values.profile_type,
        }
        break
      case 2:
        payload = {
          height_cm: clean(values.height_cm),
          build: clean(values.build),
          hair_colour: clean(values.hair_colour),
          eye_colour: clean(values.eye_colour),
          dress_size: clean(values.dress_size),
          chest: clean(values.chest),
        }
        break
      case 3:
        payload = { about_me: clean(values.about_me), languages }
        break
      case 4:
        payload = {
          borough_id: clean(values.borough_id),
          availability_type: clean(values.availability_type),
          booking_notice: clean(values.booking_notice),
        }
        break
      case 5:
        payload = {
          rate_30min: clean(values.rate_30min),
          rate_1hour: clean(values.rate_1hour),
          rate_2hours: clean(values.rate_2hours),
          rate_overnight: clean(values.rate_overnight),
        }
        break
      case 6:
        payload = {
          whatsapp_number: clean(values.whatsapp_number),
          phone_number: clean(values.phone_number),
          std_tested: values.std_tested,
          std_tested_date: clean(values.std_tested_date),
          service_tags: serviceTags,
        }
        break
      default:
        return
    }

    // Strip undefined values
    Object.keys(payload).forEach(k => payload[k] === undefined && delete payload[k])
    if (Object.keys(payload).length === 0) return

    setIsSaving(true)
    try {
      await escortsApi.updateMe(payload as any)
      await qc.invalidateQueries({ queryKey: ['escort', 'me'] })
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Failed to save changes')
      throw err
    } finally {
      setIsSaving(false)
    }
  }

  const handleContinue = async () => {
    try {
      if (step < STEPS.length) await saveStep()
      if (step < STEPS.length) {
        setStep(s => s + 1)
      } else {
        navigate('/dashboard')
        toast.success('Profile saved!')
      }
    } catch {
      // saveStep already showed error toast
    }
  }

  // Photo upload logic (step 7)
  const refresh = useCallback(() => qc.invalidateQueries({ queryKey: ['escort', 'me'] }), [qc])

  const onDrop = useCallback(async (files: File[]) => {
    if (!escort) return
    if (escort.photos.length >= escort.photo_limit) {
      toast.error(`You can upload up to ${escort.photo_limit} photos on your current plan.`)
      return
    }
    const toUpload = files.slice(0, escort.photo_limit - escort.photos.length)
    await Promise.all(toUpload.map(async file => {
      try { await uploadApi.uploadPhoto(file) }
      catch (err: any) { toast.error(err?.response?.data?.detail ?? `Failed to upload ${file.name}`) }
    }))
    toast.success(`${toUpload.length} photo${toUpload.length > 1 ? 's' : ''} uploaded!`)
    refresh()
  }, [escort, refresh])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/jpeg': [], 'image/png': [], 'image/webp': [] },
    maxSize: 10 * 1024 * 1024,
    multiple: true,
  })

  const handleDeletePhoto = async (photoId: string) => {
    try { await uploadApi.deletePhoto(photoId); toast.success('Photo removed'); refresh() }
    catch { toast.error('Failed to remove photo') }
  }

  const handleSetPrimary = async (photoId: string) => {
    try { await uploadApi.setPrimaryPhoto(photoId); toast.success('Cover photo updated'); refresh() }
    catch { toast.error('Failed to update cover photo') }
  }

  if (isLoading) return <DashboardLayout><Spinner fullPage /></DashboardLayout>
  if (!escort) return null

  const currentStep = STEPS[step - 1]
  const boroughOptions = [
    { value: '', label: 'Select your area' },
    ...boroughs.map(b => ({ value: b.id, label: b.name })),
  ]
  const aboutText = values.about_me ?? ''
  const canUploadMore = escort.photos.length < escort.photo_limit

  return (
    <DashboardLayout>
      <Helmet><title>Edit Profile — Bluechips London</title></Helmet>

      <div className="page-container py-10">
        <div className="max-w-2xl mx-auto">

          {/* Progress bar */}
          <div className="mb-10">
            <div className="flex items-center justify-between mb-3">
              <span className="text-stone-500 text-sm">Step {step} of {STEPS.length}</span>
              <button
                onClick={() => navigate('/dashboard')}
                className="text-stone-500 text-sm hover:text-stone-300 transition-colors"
              >
                Save & exit
              </button>
            </div>
            <div className="flex gap-1">
              {STEPS.map((_, i) => (
                <button
                  key={i}
                  onClick={() => setStep(i + 1)}
                  className={cn(
                    'flex-1 h-1.5 rounded-full transition-all',
                    i + 1 < step ? 'bg-gold-400' : i + 1 === step ? 'bg-gold-400/60' : 'bg-surface-border'
                  )}
                />
              ))}
            </div>
            <div className="flex gap-1 mt-2">
              {STEPS.map((s, i) => (
                <div
                  key={i}
                  className={cn(
                    'flex-1 text-center text-[10px] transition-colors truncate',
                    i + 1 === step ? 'text-gold-400' : 'text-stone-700'
                  )}
                >
                  {s.label}
                </div>
              ))}
            </div>
          </div>

          {/* Animated step content */}
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.18 }}
            className="space-y-8"
          >
            <div>
              <h1 className="font-serif text-3xl text-ivory-100">{currentStep.title}</h1>
              <p className="text-stone-500 mt-1 text-sm">{currentStep.subtitle}</p>
            </div>

            <div className="min-h-[300px]">

              {/* Step 1 — Basics */}
              {step === 1 && (
                <div className="space-y-6">
                  <div className="grid sm:grid-cols-2 gap-5">
                    <Input label="Stage name" {...register('stage_name')} />
                    <Input label="Age" type="number" min={18} max={99} {...register('age')} />
                    <Input label="Nationality" placeholder="e.g. British, Romanian..." {...register('nationality')} />
                    <Select
                      label="Ethnicity"
                      options={[{ value: '', label: 'Select...' }, ...ETHNICITIES.map(e => ({ value: e, label: e }))]}
                      {...register('ethnicity')}
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-stone-400 uppercase tracking-wider mb-3">
                      Profile type
                    </label>
                    <div className="grid grid-cols-2 gap-3">
                      {(['individual', 'couple'] as const).map(type => (
                        <button
                          key={type}
                          type="button"
                          onClick={() => setValue('profile_type', type)}
                          className={cn(
                            'p-4 rounded-xl border text-left transition-all',
                            values.profile_type === type
                              ? 'border-gold-400/50 bg-gold-400/10 text-gold-400'
                              : 'border-surface-border text-stone-400 hover:border-stone-600'
                          )}
                        >
                          <div className="text-xl mb-1">{type === 'individual' ? '👤' : '👫'}</div>
                          <div className="font-medium text-sm">{type === 'individual' ? 'Individual' : 'Couple'}</div>
                          <div className="text-xs opacity-60 mt-0.5 font-normal">
                            {type === 'individual' ? 'Solo companion' : 'Two companions together'}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Step 2 — Look */}
              {step === 2 && (
                <div className="grid sm:grid-cols-2 gap-5">
                  <Input label="Height (cm)" type="number" min={140} max={210} placeholder="e.g. 165" {...register('height_cm')} />
                  <Select
                    label="Build"
                    options={[{ value: '', label: 'Select...' }, ...BUILD_TYPES.map(b => ({ value: b.value, label: b.label }))]}
                    {...register('build')}
                  />
                  <Input label="Hair colour" placeholder="e.g. Brunette, Blonde..." {...register('hair_colour')} />
                  <Input label="Eye colour" placeholder="e.g. Brown, Blue..." {...register('eye_colour')} />
                  <Input label="Dress size" placeholder="e.g. UK 10, EU 38" {...register('dress_size')} />
                  <Input label="Bust / Chest" placeholder="e.g. 34B, 36C" {...register('chest')} />
                </div>
              )}

              {/* Step 3 — About */}
              {step === 3 && (
                <div className="space-y-6">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="block text-xs font-medium text-stone-400 uppercase tracking-wider">Bio</label>
                      <span className={cn('text-xs', aboutText.length > 540 ? 'text-amber-400' : 'text-stone-600')}>
                        {aboutText.length} / 600
                      </span>
                    </div>
                    <textarea
                      {...register('about_me')}
                      maxLength={600}
                      rows={7}
                      placeholder="Tell clients about your personality, what to expect from time together, and what makes you special..."
                      className="input-field resize-none w-full"
                    />
                  </div>
                  <div className="space-y-3">
                    <label className="block text-xs font-medium text-stone-400 uppercase tracking-wider">
                      Languages you speak
                    </label>
                    <ChipSelect options={LANGUAGES} selected={languages} onChange={setLanguages} />
                  </div>
                </div>
              )}

              {/* Step 4 — Location */}
              {step === 4 && (
                <div className="grid sm:grid-cols-2 gap-5">
                  <div className="sm:col-span-2">
                    <Select label="Your London area" options={boroughOptions} {...register('borough_id')} />
                  </div>
                  <Select
                    label="Availability type"
                    options={[
                      { value: '', label: 'Select...' },
                      { value: 'incall', label: 'Incall only — clients come to you' },
                      { value: 'outcall', label: 'Outcall only — you travel to clients' },
                      { value: 'both', label: 'Incall & Outcall' },
                    ]}
                    {...register('availability_type')}
                  />
                  <Input
                    label="Booking notice"
                    placeholder="e.g. 1 hour notice required"
                    {...register('booking_notice')}
                  />
                </div>
              )}

              {/* Step 5 — Rates */}
              {step === 5 && (
                <div className="space-y-5">
                  <p className="text-stone-500 text-sm">All prices in GBP (£). Leave blank to hide that rate from your public profile.</p>
                  <div className="grid sm:grid-cols-2 gap-5">
                    <Input label="30 minutes (£)" type="number" min={0} placeholder="e.g. 100" {...register('rate_30min')} />
                    <Input label="1 hour (£)" type="number" min={0} placeholder="e.g. 180" {...register('rate_1hour')} />
                    <Input label="2 hours (£)" type="number" min={0} placeholder="e.g. 320" {...register('rate_2hours')} />
                    <Input label="Overnight (£)" type="number" min={0} placeholder="e.g. 1000" {...register('rate_overnight')} />
                  </div>
                </div>
              )}

              {/* Step 6 — Contact & Services */}
              {step === 6 && (
                <div className="space-y-6">
                  <div className="grid sm:grid-cols-2 gap-5">
                    <Input label="WhatsApp number" placeholder="+44 7700 900000" {...register('whatsapp_number')} />
                    <Input label="Phone number (optional)" placeholder="+44 7700 900000" {...register('phone_number')} />
                  </div>
                  <div className="space-y-3 p-4 rounded-xl bg-surface border border-surface-border">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input type="checkbox" {...register('std_tested')} className="accent-gold-400 w-4 h-4 rounded" />
                      <span className="text-stone-300 text-sm font-medium">I have been STD tested</span>
                    </label>
                    <Input label="Date of last test (optional)" placeholder="e.g. March 2026" {...register('std_tested_date')} />
                  </div>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-xs font-medium text-stone-400 uppercase tracking-wider mb-1">
                        Services you offer
                      </label>
                      <p className="text-stone-600 text-xs mb-3">
                        Self-declared — you are solely responsible for accuracy and legality.
                      </p>
                    </div>
                    <ChipSelect options={SERVICE_TAGS} selected={serviceTags} onChange={setServiceTags} />
                  </div>
                </div>
              )}

              {/* Step 7 — Photos */}
              {step === 7 && (
                <div className="space-y-5">
                  <div className="flex items-center justify-between">
                    <p className="text-stone-400 text-sm">{escort.photos.length} of {escort.photo_limit} photos used</p>
                    {escort.subscription_tier === 'free' && (
                      <Link to="/dashboard/subscription" className="text-gold-400 text-xs hover:text-gold-300 transition-colors">
                        Upgrade for more photos →
                      </Link>
                    )}
                  </div>
                  <div className="h-1.5 bg-surface rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gold-400 rounded-full transition-all"
                      style={{ width: `${Math.min(100, (escort.photos.length / escort.photo_limit) * 100)}%` }}
                    />
                  </div>

                  {canUploadMore && (
                    <div
                      {...getRootProps()}
                      className={cn(
                        'border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all',
                        isDragActive
                          ? 'border-gold-400 bg-gold-400/5'
                          : 'border-surface-border hover:border-gold-400/40 hover:bg-surface/50'
                      )}
                    >
                      <input {...getInputProps()} />
                      <div className="space-y-2">
                        <div className="flex justify-center">
                          <div className="w-12 h-12 rounded-full bg-gold-400/10 border border-gold-400/20 flex items-center justify-center">
                            <Upload className="w-5 h-5 text-gold-400" />
                          </div>
                        </div>
                        <p className="text-ivory-200 font-medium text-sm">
                          {isDragActive ? 'Drop your photos here' : 'Drag photos here, or click to select'}
                        </p>
                        <p className="text-stone-500 text-xs">JPEG, PNG or WebP · Max 10MB each</p>
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-3 gap-3">
                    <AnimatePresence>
                      {escort.photos.map(photo => (
                        <motion.div
                          key={photo.id}
                          initial={{ opacity: 0, scale: 0.95 }}
                          animate={{ opacity: 1, scale: 1 }}
                          exit={{ opacity: 0, scale: 0.95 }}
                          className="relative group aspect-[3/4] rounded-xl overflow-hidden bg-surface border border-surface-border"
                        >
                          <img src={photo.thumbnail_url || photo.url} alt="" className="w-full h-full object-cover" />
                          <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                            <button
                              onClick={() => handleSetPrimary(photo.id)}
                              title="Set as cover"
                              className="w-8 h-8 rounded-full bg-gold-400/90 flex items-center justify-center hover:bg-gold-300 transition-colors"
                            >
                              <Star className="w-3.5 h-3.5 text-black" />
                            </button>
                            <button
                              onClick={() => handleDeletePhoto(photo.id)}
                              title="Remove photo"
                              className="w-8 h-8 rounded-full bg-red-600/90 flex items-center justify-center hover:bg-red-500 transition-colors"
                            >
                              <Trash2 className="w-3.5 h-3.5 text-white" />
                            </button>
                          </div>
                          {photo.is_primary && (
                            <div className="absolute top-1.5 left-1.5 bg-gold-400 text-black text-[9px] font-bold px-2 py-0.5 rounded-full">
                              Cover
                            </div>
                          )}
                        </motion.div>
                      ))}
                      {Array.from({ length: Math.min(3, Math.max(0, escort.photo_limit - escort.photos.length)) }).map((_, i) => (
                        <div
                          key={`empty-${i}`}
                          className="aspect-[3/4] rounded-xl border-2 border-dashed border-surface-border flex items-center justify-center text-stone-700"
                        >
                          <ImagePlus className="w-5 h-5" />
                        </div>
                      ))}
                    </AnimatePresence>
                  </div>
                </div>
              )}
            </div>

            {/* Navigation */}
            <div className="flex items-center justify-between pt-6 border-t border-surface-border">
              {step > 1 ? (
                <Button variant="ghost" onClick={() => setStep(s => s - 1)}>
                  ← Back
                </Button>
              ) : (
                <button
                  onClick={() => navigate('/dashboard')}
                  className="text-stone-500 hover:text-stone-300 text-sm transition-colors"
                >
                  ← Dashboard
                </button>
              )}

              <Button variant="gold" onClick={handleContinue} loading={isSaving}>
                {step === STEPS.length ? 'Done ✓' : 'Continue →'}
              </Button>
            </div>
          </motion.div>

        </div>
      </div>
    </DashboardLayout>
  )
}
