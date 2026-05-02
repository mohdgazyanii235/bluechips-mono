export interface TokenResponse {
  access_token: string
  token_type: string
  escort_id: string
  stage_name: string
  subscription_tier: string
  verification_level: number
  profile_complete: boolean
}

export interface AuthState {
  token: string | null
  escort_id: string | null
  stage_name: string | null
  subscription_tier: string | null
  verification_level: number
  profile_complete: boolean
  isAuthenticated: boolean
}
