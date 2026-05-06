export interface EscortCard {
  id: string
  stage_name: string
  slug: string
  age: number | null
  nationality: string | null
  ethnicity: string | null
  borough_name: string | null
  borough_slug: string | null
  availability_type: string | null
  rate_1hour: number | null
  subscription_tier: 'free' | 'essential' | 'premium' | 'elite'
  verification_level: 0 | 1 | 2 | 3
  blue_tick_active: boolean
  available_now: boolean
  std_tested: boolean
  primary_photo_url: string | null
  service_tags: string[]
  profile_type: 'individual' | 'couple'
}

export interface Photo {
  id: string
  url: string
  thumbnail_url: string | null
  is_primary: boolean
  sort_order: number
}

export interface EscortProfile {
  id: string
  stage_name: string
  slug: string
  age: number | null
  nationality: string | null
  ethnicity: string | null
  height_cm: number | null
  build: string | null
  hair_colour: string | null
  eye_colour: string | null
  dress_size: string | null
  chest: string | null
  borough_name: string | null
  borough_slug: string | null
  availability_type: string | null
  rate_30min: number | null
  rate_1hour: number | null
  rate_2hours: number | null
  rate_overnight: number | null
  about_me: string | null
  languages: string[] | null
  booking_notice: string | null
  std_tested: boolean
  std_tested_date: string | null
  subscription_tier: string
  verification_level: number
  blue_tick_active: boolean
  available_now: boolean
  profile_views: number
  service_tags: string[]
  photos: Photo[]
  created_at: string
  profile_type: 'individual' | 'couple'
  whatsapp_number: string | null
  phone_number: string | null
}

export interface EscortDashboard extends EscortProfile {
  email: string
  borough_id: string | null
  rate_30min: number | null
  rate_2hours: number | null
  rate_overnight: number | null
  is_email_verified: boolean
  profile_complete: boolean
  subscription_expires_at: string | null
  contact_clicks: number
  photo_limit: number
  whatsapp_number: string | null
  phone_number: string | null
  blue_tick_active: boolean
  blue_tick_stripe_subscription_id: string | null
  stripe_subscription_id: string | null
  profile_type: 'individual' | 'couple'
}

export interface Borough {
  id: string
  name: string
  slug: string
  description: string | null
  seo_title: string | null
  seo_description: string | null
  is_premium_area: boolean
  escort_count: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  pages: number
}

export interface SearchFilters {
  borough_slug?: string
  ethnicity?: string
  availability_type?: string
  profile_type?: string
  min_age?: number
  max_age?: number
  min_rate?: number
  max_rate?: number
  std_tested?: boolean
  available_now?: boolean
  blue_tick_only?: boolean
  service_tag?: string
  page?: number
  per_page?: number
}

export const SERVICE_TAGS = [
  'GFE', 'PSE', 'OWO', 'OWO-CIM', 'CIM', 'CIMWS', 'COB', 'CIF',
  'Massage', 'Erotic Massage', 'Tantric Massage', 'Body Slide', 'Nude Massage',
  'Happy Ending', 'Hand Relief', 'DFK', '69', 'Anal', 'A-Level',
  'Deep Throat', 'BBBJ', 'Rimming', 'Squirting',
  'BDSM', 'Bondage', 'Domination', 'Submission', 'Fetish', 'Role Play',
  'Tie & Tease', 'S&M', 'Watersports', 'CBT', 'Strapon',
  'Duo', 'Threesome', 'Couples Welcome',
  'Dinner Date', 'Travel Companion', 'Overnight',
  'Striptease', 'Lap Dance', 'Foot Fetish', 'Shower Together',
  'Toys', 'Party Friendly', 'Webcam',
] as const

export const ETHNICITIES = [
  'White', 'Black', 'Asian', 'Latin', 'Mixed', 'Middle Eastern', 'Indian', 'Other',
] as const

export const BUILD_TYPES = [
  { value: 'slim', label: 'Slim' },
  { value: 'athletic', label: 'Athletic' },
  { value: 'curvy', label: 'Curvy' },
  { value: 'petite', label: 'Petite' },
  { value: 'bbw', label: 'BBW' },
] as const

export const LANGUAGES = [
  'English', 'Romanian', 'Spanish', 'Russian', 'Polish', 'Portuguese',
  'Brazilian Portuguese', 'Thai', 'Hungarian', 'Italian', 'French', 'German',
  'Arabic', 'Mandarin', 'Japanese', 'Korean', 'Turkish', 'Greek',
  'Swedish', 'Dutch', 'Czech', 'Ukrainian', 'Albanian', 'Bulgarian',
  'Serbian', 'Lithuanian', 'Hindi', 'Punjabi', 'Urdu', 'Persian',
  'Bengali', 'Somali', 'Other',
] as const

export const SUBSCRIPTION_TIERS = {
  free: { label: 'Free', price: 0, color: 'stone' },
  essential: { label: 'Essential', price: 2499, color: 'silver' },
  premium: { label: 'Premium', price: 4999, color: 'gold' },
  elite: { label: 'Elite', price: 8999, color: 'gold' },
} as const
