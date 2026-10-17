/**
 * api/endpoints.ts
 *
 * Central endpoint path registry.
 *
 * Rule: API URL strings MUST NOT be hardcoded in feature components, hooks,
 * or any file other than this one. All API paths have exactly one definition here.
 *
 * When backend routes change, update this file — not individual components.
 */

const API_BASE = "/api/v1";

export const ENDPOINTS = {
  health: "/health",

  auth: {
    login: `${API_BASE}/auth/login`,
    register: `${API_BASE}/auth/register`,
    refresh: `${API_BASE}/auth/refresh`,
    logout: `${API_BASE}/auth/logout`,
    me: `${API_BASE}/auth/me`,
    forgotPassword: `${API_BASE}/auth/forgot-password`,
    resetPassword: `${API_BASE}/auth/reset-password`,
    verifyEmail: `${API_BASE}/auth/verify-email`,
    resendVerification: `${API_BASE}/auth/resend-verification`,
    google: `${API_BASE}/auth/google`,
  },

  patients: {
    list: `${API_BASE}/patients`,
    create: `${API_BASE}/patients`,
    detail: (id: string) => `${API_BASE}/patients/${id}`,
    allergies: (id: string) => `${API_BASE}/patients/${id}/allergies`,
    visits: (id: string) => `${API_BASE}/patients/${id}/visits`,
    observations: (id: string) => `${API_BASE}/patients/${id}/observations`,
    prescriptions: (id: string) => `${API_BASE}/patients/${id}/prescriptions`,
  },

  visits: {
    create: `${API_BASE}/visits`,
    detail: (id: string) => `${API_BASE}/visits/${id}`,
    update: (id: string) => `${API_BASE}/visits/${id}`,
    sign: (id: string) => `${API_BASE}/visits/${id}/sign`,
    observations: (id: string) => `${API_BASE}/visits/${id}/observations`,
    prescriptions: (id: string) => `${API_BASE}/visits/${id}/prescriptions`,
  },
} as const;
