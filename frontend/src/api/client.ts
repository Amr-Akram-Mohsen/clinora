/**
 * api/client.ts
 *
 * Axios HTTP client configured for the Clinora backend.
 *
 * Responsibilities:
 * - Set base URL and default headers.
 * - Attach Authorization header from in-memory access token.
 * - Normalize all error responses into ApiError instances.
 * - Expose X-Request-ID from responses for error correlation.
 * - Provide a token setter called by AuthProvider on login/refresh.
 *
 * Design decisions:
 * - Access token is stored in module-level memory (not localStorage) to reduce
 *   XSS exposure. It is set by AuthProvider after login/refresh.
 * - Refresh token is in an HTTP-only cookie managed by the browser.
 * - On 401, the client does NOT automatically retry with refresh here —
 *   that logic lives in AuthProvider to avoid circular dependency.
 */

import axios, {
  type AxiosError,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from "axios";
import { ApiError, type ApiErrorResponse } from "@/types/api";

// In-memory access token — never stored in localStorage
let _accessToken: string | null = null;

export function setAccessToken(token: string | null): void {
  _accessToken = token;
}

export function getAccessToken(): string | null {
  return _accessToken;
}

export const apiClient = axios.create({
  baseURL: "/",
  withCredentials: true, // Send cookies (refresh token)
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

// --- Request interceptor: attach Authorization header ---
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (_accessToken) {
    config.headers.Authorization = `Bearer ${_accessToken}`;
  }
  return config;
});

// --- Response interceptor: normalize errors ---
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError<ApiErrorResponse>) => {
    if (error.response) {
      const status = error.response.status;
      const body = error.response.data;
      const requestId =
        (error.response.headers["x-request-id"] as string | undefined) ??
        body?.error?.request_id;

      if (body?.error) {
        // Backend returned a structured error — normalize to ApiError
        const detail = {
          ...body.error,
          request_id: requestId ?? body.error.request_id,
        };
        throw new ApiError(status, detail);
      }

      // Unexpected error shape — wrap with generic code
      throw new ApiError(status, {
        code: "INTERNAL_ERROR",
        message: `Request failed with status ${status}`,
        request_id: requestId,
      });
    }

    if (error.request) {
      // Network error — no response received
      throw new ApiError(0, {
        code: "EXTERNAL_SERVICE_ERROR",
        message: "Network error — please check your connection",
      });
    }

    // Unknown error
    throw new ApiError(0, {
      code: "INTERNAL_ERROR",
      message: error.message || "An unexpected error occurred",
    });
  }
);
