export interface User {
  id: number
  subject_id: string
  display_name: string
  email: string
  role_codes: string[]
  is_asp: boolean
  is_active: boolean
  created_at_utc: string
  updated_at_utc: string
}

export interface LoginRequest {
  email: string
  password: string
  client_metadata?: {
    device?: string
    ip?: string
  }
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
}
