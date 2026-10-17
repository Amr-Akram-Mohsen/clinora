/**
 * features/auth/ForgotPasswordPage.tsx
 *
 * Password reset request page.
 * Sends a password recovery link to the user's registered email address.
 */

import { type FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import * as authApi from "@/api/auth";
import { Button } from "@/components/Button/Button";
import { Input } from "@/components/Input/Input";
import type { ApiError } from "@/types/api";
import "./AuthPages.css";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!email) return;

    setError(null);
    setIsSubmitting(true);

    try {
      await authApi.forgotPassword({ email: email.toLowerCase().trim() });
      setIsSubmitted(true);
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.message ?? "An error occurred while requesting password reset.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="auth-recovery-page">
      <div className="auth-recovery-card">
        <div className="auth-recovery-header">
          <Link to="/login" className="auth-recovery-logo">
            <span className="auth-recovery-logo-mark">C</span>
            <span className="auth-recovery-logo-name">Clinora</span>
          </Link>

          <div className="auth-recovery-icon-badge">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
          </div>

          <h1 className="auth-recovery-title">Reset your password</h1>
          <p className="auth-recovery-subtitle">
            {isSubmitted
              ? `We have dispatched recovery instructions to ${email}.`
              : "Enter your registered email and we'll send you a recovery link valid for 1 hour."}
          </p>
        </div>

        {error && (
          <div className="auth-recovery-alert auth-recovery-alert--error" role="alert">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span>{error}</span>
          </div>
        )}

        {isSubmitted ? (
          <div className="auth-recovery-alert auth-recovery-alert--success">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
            <span>
              If an account with that email exists, check your inbox or spam folder. Click the link in the message to set a new password.
            </span>
          </div>
        ) : (
          <form className="auth-recovery-form" onSubmit={handleSubmit} noValidate>
            <Input
              id="reset-email"
              type="email"
              label="Email address"
              placeholder="doctor@clinic.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
              disabled={isSubmitting}
            />

            <Button
              type="submit"
              variant="primary"
              size="lg"
              fullWidth
              isLoading={isSubmitting}
              disabled={!email}
            >
              Send reset instructions
            </Button>
          </form>
        )}

        <div className="auth-recovery-footer">
          Remembered your password?{" "}
          <Link to="/login" className="auth-recovery-link">
            Back to sign in
          </Link>
        </div>
      </div>
    </main>
  );
}
