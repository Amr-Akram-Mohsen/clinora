/**
 * States.tsx
 *
 * LoadingState, EmptyState, ErrorState — reusable async operation states.
 *
 * Every meaningful async UI operation must handle these states:
 * Loading → Empty → Success | Error
 *
 * These components provide consistent visual treatment for all three
 * non-success states rather than leaving them to individual feature code.
 */

import { type ReactNode } from "react";
import { Button } from "@/components/Button/Button";
import "./States.css";

// ---- LoadingState -------------------------------------------------------

interface LoadingStateProps {
  message?: string;
}

export function LoadingState({ message = "Loading…" }: LoadingStateProps) {
  return (
    <div
      className="state-container"
      role="status"
      aria-live="polite"
      aria-label={message}
    >
      <span className="state-spinner" aria-hidden="true" />
      <span className="sr-only">{message}</span>
      <span className="state-message" aria-hidden="true">
        {message}
      </span>
    </div>
  );
}

// ---- EmptyState ---------------------------------------------------------

interface EmptyStateProps {
  title: string;
  message?: string;
  action?: ReactNode;
}

export function EmptyState({ title, message, action }: EmptyStateProps) {
  return (
    <div className="state-container">
      <div className="state-icon state-icon--empty" aria-hidden="true">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path
            d="M9 17H7A5 5 0 017 7h2M15 7h2a5 5 0 010 10h-2M9 12h6"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        </svg>
      </div>
      <p className="state-title">{title}</p>
      {message && <p className="state-message">{message}</p>}
      {action}
    </div>
  );
}

// ---- ErrorState ---------------------------------------------------------

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({
  title = "Something went wrong",
  message = "An unexpected error occurred. Please try again.",
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="state-container" role="alert">
      <div className="state-icon state-icon--error" aria-hidden="true">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path
            d="M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
      <p className="state-title">{title}</p>
      <p className="state-message">{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}
