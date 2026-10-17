/**
 * api/auth.ts
 *
 * Typed API functions for authentication endpoints.
 * All paths come from ENDPOINTS — no hardcoded strings here.
 */

import { apiClient } from "./client";
import { ENDPOINTS } from "./endpoints";
import type {
  ForgotPasswordRequest,
  GoogleAuthRequest,
  LoginRequest,
  MessageResponse,
  RegisterRequest,
  ResendVerificationRequest,
  ResetPasswordRequest,
  TokenResponse,
  User,
  VerifyEmailRequest,
} from "@/types/auth";

export async function login(credentials: LoginRequest): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>(
    ENDPOINTS.auth.login,
    credentials
  );
  return response.data;
}

export async function register(data: RegisterRequest): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>(
    ENDPOINTS.auth.register,
    data
  );
  return response.data;
}

export async function refreshToken(): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>(ENDPOINTS.auth.refresh);
  return response.data;
}

export async function logout(): Promise<void> {
  await apiClient.post(ENDPOINTS.auth.logout);
}

export async function getCurrentUser(): Promise<User> {
  const response = await apiClient.get<User>(ENDPOINTS.auth.me);
  return response.data;
}

export async function forgotPassword(data: ForgotPasswordRequest): Promise<MessageResponse> {
  const response = await apiClient.post<MessageResponse>(ENDPOINTS.auth.forgotPassword, data);
  return response.data;
}

export async function resetPassword(data: ResetPasswordRequest): Promise<MessageResponse> {
  const response = await apiClient.post<MessageResponse>(ENDPOINTS.auth.resetPassword, data);
  return response.data;
}

export async function verifyEmail(data: VerifyEmailRequest): Promise<MessageResponse> {
  const response = await apiClient.post<MessageResponse>(ENDPOINTS.auth.verifyEmail, data);
  return response.data;
}

export async function resendVerification(data: ResendVerificationRequest): Promise<MessageResponse> {
  const response = await apiClient.post<MessageResponse>(ENDPOINTS.auth.resendVerification, data);
  return response.data;
}

export async function googleAuth(data: GoogleAuthRequest): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>(ENDPOINTS.auth.google, data);
  return response.data;
}

