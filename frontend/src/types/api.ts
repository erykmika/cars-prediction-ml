export interface Token {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface UserResponse {
  id: number
  username: string
  is_active: boolean
  created_at: string
}

export type FeatureValue = string | number | boolean | null
export type PredictionValue = number | string | number[]

export interface PredictionRequest {
  features: Record<string, FeatureValue> | number[]
}

export interface PredictionResponse {
  prediction: PredictionValue
}