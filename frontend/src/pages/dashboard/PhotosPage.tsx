import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Helmet } from 'react-helmet-async'
import { Link } from 'react-router-dom'
import { ChevronLeft, Upload, Trash2, Star, ImagePlus } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { DashboardLayout } from '@/components/layout/Layout'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import { useMyProfile } from '@/hooks/useEscorts'
import { uploadApi } from '@/api/upload'
import { useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { cn } from '@/utils/cn'

export function PhotosPage() {
  const { data: escort, isLoading } = useMyProfile()
  const qc = useQueryClient()

  const refresh = () => qc.invalidateQueries({ queryKey: ['escort', 'me'] })

  const onDrop = useCallback(async (files: File[]) => {
    if (!escort) return
    if (escort.photos.length >= escort.photo_limit) {
      toast.error(`You can upload up to ${escort.photo_limit} photos on your current plan.`)
      return
    }

    const toUpload = files.slice(0, escort.photo_limit - escort.photos.length)
    const uploadPromises = toUpload.map(async (file) => {
      try {
        await uploadApi.uploadPhoto(file)
      } catch (err: any) {
        toast.error(err?.response?.data?.detail ?? `Failed to upload ${file.name}`)
      }
    })

    toast.promise(Promise.all(uploadPromises), {
      loading: `Uploading ${toUpload.length} photo${toUpload.length > 1 ? 's' : ''}...`,
      success: 'Photos uploaded!',
      error: 'Some uploads failed.',
    })

    await Promise.all(uploadPromises)
    refresh()
  }, [escort])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/jpeg': [], 'image/png': [], 'image/webp': [] },
    maxSize: 10 * 1024 * 1024,
    multiple: true,
  })

  const handleDelete = async (photoId: string) => {
    try {
      await uploadApi.deletePhoto(photoId)
      toast.success('Photo deleted')
      refresh()
    } catch {
      toast.error('Failed to delete photo')
    }
  }

  const handleSetPrimary = async (photoId: string) => {
    try {
      await uploadApi.setPrimaryPhoto(photoId)
      toast.success('Cover photo updated')
      refresh()
    } catch {
      toast.error('Failed to update cover photo')
    }
  }

  if (isLoading) return <DashboardLayout><Spinner fullPage /></DashboardLayout>
  if (!escort) return null

  const canUploadMore = escort.photos.length < escort.photo_limit

  return (
    <DashboardLayout>
      <Helmet><title>My Photos — Bluechips London</title></Helmet>

      <div className="page-container py-10">
        <div className="max-w-3xl mx-auto space-y-8">
          <div className="flex items-center gap-3">
            <Link to="/dashboard" className="text-stone-500 hover:text-gold-400 transition-colors">
              <ChevronLeft className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="font-serif text-3xl text-ivory-100">My Photos</h1>
              <p className="text-stone-500 text-sm mt-0.5">{escort.photos.length} of {escort.photo_limit} photos used</p>
            </div>
          </div>

          {/* Progress bar */}
          <div>
            <div className="h-1.5 bg-surface rounded-full overflow-hidden">
              <div
                className="h-full bg-gold-400 rounded-full transition-all"
                style={{ width: `${(escort.photos.length / escort.photo_limit) * 100}%` }}
              />
            </div>
            {escort.subscription_tier === 'free' && (
              <p className="text-stone-600 text-xs mt-2">
                You're on the free plan (3 photos).{' '}
                <Link to="/dashboard/subscription" className="text-gold-400 hover:text-gold-300">Upgrade for up to 50 photos →</Link>
              </p>
            )}
          </div>

          {/* Upload Zone */}
          {canUploadMore && (
            <div
              {...getRootProps()}
              className={cn(
                'border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all',
                isDragActive
                  ? 'border-gold-400 bg-gold-400/5'
                  : 'border-surface-border hover:border-gold-400/40 hover:bg-surface/50'
              )}
            >
              <input {...getInputProps()} />
              <div className="space-y-3">
                <div className="flex justify-center">
                  <div className="w-14 h-14 rounded-full bg-gold-400/10 border border-gold-400/20 flex items-center justify-center">
                    <Upload className="w-6 h-6 text-gold-400" />
                  </div>
                </div>
                <div>
                  <p className="text-ivory-200 font-medium">
                    {isDragActive ? 'Drop your photos here' : 'Drag photos here, or click to select'}
                  </p>
                  <p className="text-stone-500 text-sm mt-1">JPEG, PNG or WebP · Max 10MB each</p>
                </div>
              </div>
            </div>
          )}

          {/* Photo grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            <AnimatePresence>
              {escort.photos.map((photo) => (
                <motion.div
                  key={photo.id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="relative group aspect-[3/4] rounded-xl overflow-hidden bg-surface border border-surface-border"
                >
                  <img src={photo.thumbnail_url || photo.url} alt="" className="w-full h-full object-cover" />

                  {/* Overlay on hover */}
                  <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-3">
                    <button
                      onClick={() => handleSetPrimary(photo.id)}
                      title="Set as cover photo"
                      className="w-9 h-9 rounded-full bg-gold-400/90 flex items-center justify-center hover:bg-gold-300 transition-colors"
                    >
                      <Star className="w-4 h-4 text-black" />
                    </button>
                    <button
                      onClick={() => handleDelete(photo.id)}
                      title="Delete photo"
                      className="w-9 h-9 rounded-full bg-red-600/90 flex items-center justify-center hover:bg-red-500 transition-colors"
                    >
                      <Trash2 className="w-4 h-4 text-white" />
                    </button>
                  </div>

                  {/* Primary badge */}
                  {photo.is_primary && (
                    <div className="absolute top-2 left-2 bg-gold-400 text-black text-[10px] font-bold px-2 py-0.5 rounded-full">
                      Cover
                    </div>
                  )}
                </motion.div>
              ))}

              {/* Empty slots */}
              {Array.from({ length: Math.max(0, escort.photo_limit - escort.photos.length) }).map((_, i) => (
                i < 3 && (
                  <div
                    key={`empty-${i}`}
                    className="aspect-[3/4] rounded-xl border-2 border-dashed border-surface-border flex items-center justify-center text-stone-700"
                  >
                    <ImagePlus className="w-6 h-6" />
                  </div>
                )
              ))}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
