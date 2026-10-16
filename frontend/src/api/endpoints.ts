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
  },
} as const;
