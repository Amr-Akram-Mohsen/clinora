/**
 * types/auth.ts
 *
 * TypeScript types for authentication domain objects.
 * Mirror the Pydantic response schemas from api/schemas/auth.py.
 */

export interface User {
  id: string;
  email: string;
  full_name: string;
  organization_id: string;
  is_active: boolean;
  is_verified: boolean;
  roles: string[];
  created_at: string; // ISO-8601 UTC string
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number; // seconds
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  organization_name?: string;
  role?: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

export interface VerifyEmailRequest {
  token: string;
}

export interface ResendVerificationRequest {
  email: string;
}

export interface GoogleAuthRequest {
  credential: string;
}

export interface MessageResponse {
  message: string;
  success: boolean;
}

/**
 * Auth state managed by AuthProvider.
 */
export interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
