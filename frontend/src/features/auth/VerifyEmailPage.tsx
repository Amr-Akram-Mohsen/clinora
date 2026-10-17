/**
 * features/auth/VerifyEmailPage.tsx
 *
 * Email verification landing page.
 * Validates the email confirmation token and activates the account.
 */

import { type FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import * as authApi from "@/api/auth";
import { Button } from "@/components/Button/Button";
import { Input } from "@/components/Input/Input";
import type { ApiError } from "@/types/api";
import "./AuthPages.css";

export function VerifyEmailPage() {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();

  const [isVerifying, setIsVerifying] = useState(Boolean(token));
  const [isSuccess, setIsSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Resend form state
  const [resendEmail, setResendEmail] = useState("");
  const [isResending, setIsResending] = useState(false);
  const [resendMessage, setResendMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;

    let cancelled = false;

    async function performVerification() {
      setIsVerifying(true);
      setErrorMessage(null);

      try {
        await authApi.verifyEmail({ token: token! });
        if (!cancelled) {
          setIsSuccess(true);
        }
      } catch (err) {
        if (!cancelled) {
          const apiErr = err as ApiError;
          setErrorMessage(apiErr.message ?? "Verification link is invalid or has expired.");
        }
      } finally {
        if (!cancelled) {
          setIsVerifying(false);
        }
      }
    }

    performVerification();
    return () => {
      cancelled = true;
    };
  }, [token]);

  async function handleResend(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!resendEmail) return;

    setIsResending(true);
    setResendMessage(null);

    try {
      const res = await authApi.resendVerification({ email: resendEmail.toLowerCase().trim() });
      setResendMessage(res.message);
    } catch (err) {
      const apiErr = err as ApiError;
      setResendMessage(apiErr.message ?? "Could not send verification email.");
    } finally {
      setIsResending(false);
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

          <div
            className={`auth-recovery-icon-badge ${
              isSuccess
                ? "auth-recovery-icon-badge--success"
                : errorMessage
                ? "auth-recovery-icon-badge--error"
                : ""
            }`}
          >
            {isSuccess ? (
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            ) : errorMessage ? (
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <circle cx="12" cy="12" r="10" />
                <line x1="15" y1="9" x2="9" y2="15" />
                <line x1="9" y1="9" x2="15" y2="15" />
              </svg>
            ) : (
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                <polyline points="22,6 12,13 2,6" />
              </svg>
            )}
          </div>

          <h1 className="auth-recovery-title">
            {isVerifying
              ? "Verifying your email…"
              : isSuccess
              ? "Email verified!"
              : errorMessage
              ? "Verification failed"
              : "Verify your email"}
          </h1>
          <p className="auth-recovery-subtitle">
            {isVerifying
              ? "Please wait while we confirm your account token with the clinical directory."
              : isSuccess
              ? "Your Clinora account has been verified. You can now access your workspace."
              : errorMessage
              ? errorMessage
              : "Need a new verification link? Enter your email address below."}
          </p>
        </div>

        {isSuccess ? (
          <div className="auth-recovery-form">
            <Button
              type="button"
              variant="primary"
              size="lg"
              fullWidth
              onClick={() => navigate("/login")}
            >
              Continue to Sign in
            </Button>
          </div>
        ) : isVerifying ? (
          <div style={{ textAlign: "center", padding: "20px 0", color: "var(--color-text-muted)" }}>
            Checking verification token…
          </div>
        ) : (
          <div className="auth-recovery-form">
            <form onSubmit={handleResend} className="auth-recovery-form" noValidate>
              <Input
                id="resend-email"
                type="email"
                label="Resend verification link"
                placeholder="you@clinic.com"
                value={resendEmail}
                onChange={(e) => setResendEmail(e.target.value)}
                required
                disabled={isResending}
              />

              <Button
                type="submit"
                variant="primary"
                size="md"
                fullWidth
                isLoading={isResending}
                disabled={!resendEmail}
              >
                Resend verification email
              </Button>
            </form>

            {resendMessage && (
              <div className="auth-recovery-alert auth-recovery-alert--success">
                {resendMessage}
              </div>
            )}
          </div>
        )}

        <div className="auth-recovery-footer">
          <Link to="/login" className="auth-recovery-link">
            Back to sign in
          </Link>
        </div>
      </div>
    </main>
  );
}
