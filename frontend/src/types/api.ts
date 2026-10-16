/**
 * types/api.ts
 *
 * Shared API response types mirroring the backend's error contract.
 * Every API interaction uses these types — no ad-hoc guessing of response shapes.
 */

export interface FieldErrorDetail {
  field: string;
  message: string;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  request_id?: string;
  details?: FieldErrorDetail[];
}

export interface ApiErrorResponse {
  error: ApiErrorDetail;
}

/**
 * Known API error codes matching core/errors.py
 */
export type ApiErrorCode =
  | "VALIDATION_ERROR"
  | "AUTHENTICATION_REQUIRED"
  | "FORBIDDEN"
  | "NOT_FOUND"
  | "CONFLICT"
  | "INTERNAL_ERROR"
  | "EXTERNAL_SERVICE_ERROR";

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

/**
 * Structured client-side representation of an API error.
 * Created by the API client from the error response body.
 */
export class ApiError extends Error {
  readonly code: ApiErrorCode;
  readonly status: number;
  readonly requestId?: string;
  readonly details?: FieldErrorDetail[];

  constructor(status: number, detail: ApiErrorDetail) {
    super(detail.message);
    this.name = "ApiError";
    this.code = detail.code as ApiErrorCode;
    this.status = status;
    this.requestId = detail.request_id;
    this.details = detail.details;
  }

  get isAuthError(): boolean {
    return this.code === "AUTHENTICATION_REQUIRED";
  }

  get isForbiddenError(): boolean {
    return this.code === "FORBIDDEN";
  }

  get isNotFoundError(): boolean {
    return this.code === "NOT_FOUND";
  }

  get isValidationError(): boolean {
    return this.code === "VALIDATION_ERROR";
  }
}
