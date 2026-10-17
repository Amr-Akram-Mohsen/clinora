/**
 * features/auth/ResetPasswordPage.tsx
 *
 * Password reset execution page.
 * Validates the reset token from URL parameters and sets a new password.
 */

import { type FormEvent, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import * as authApi from "@/api/auth";
import { Button } from "@/components/Button/Button";
import { Input } from "@/components/Input/Input";
import { PasswordStrengthMeter, scorePassword } from "./PasswordStrengthMeter";
import type { ApiError } from "@/types/api";
import "./AuthPages.css";

export function ResetPasswordPage() {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();

  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { isStrongEnough } = scorePassword(newPassword);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!token) {
      setError("Reset link is missing a valid security token.");
      return;
    }

    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setError(null);
    setIsSubmitting(true);

    try {
      await authApi.resetPassword({
        token,
        new_password: newPassword,
      });
      setIsSuccess(true);
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.message ?? "Password reset link is invalid or has expired.");
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

          <div className={`auth-recovery-icon-badge ${isSuccess ? "auth-recovery-icon-badge--success" : ""}`}>
            {isSuccess ? (
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            ) : (
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M21 2l-2 2m-6 6l-3 3-4-4-3 3 7 7 3-3 4 4 2-2" />
                <circle cx="15.5" cy="8.5" r="3.5" />
              </svg>
            )}
          </div>

          <h1 className="auth-recovery-title">
            {isSuccess ? "Password updated!" : "Create new password"}
          </h1>
          <p className="auth-recovery-subtitle">
            {isSuccess
              ? "Your password has been changed securely. Existing active sessions were revoked."
              : "Please choose a strong password for your clinical workspace account."}
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

        {isSuccess ? (
          <div className="auth-recovery-form">
            <div className="auth-recovery-alert auth-recovery-alert--success">
              You may now sign in using your new password.
            </div>
            <Button
              type="button"
              variant="primary"
              size="lg"
              fullWidth
              onClick={() => navigate("/login")}
            >
              Sign in with new password
            </Button>
          </div>
        ) : (
          <form className="auth-recovery-form" onSubmit={handleSubmit} noValidate>
            <div>
              <Input
                id="new-password"
                type="password"
                label="New password"
                placeholder="At least 8 characters"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                autoFocus
                disabled={isSubmitting}
              />
              <PasswordStrengthMeter password={newPassword} />
            </div>

            <Input
              id="confirm-new-password"
              type="password"
              label="Confirm new password"
              placeholder="Re-enter your password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              disabled={isSubmitting}
            />

            <Button
              type="submit"
              variant="primary"
              size="lg"
              fullWidth
              isLoading={isSubmitting}
              disabled={!newPassword || !confirmPassword || !isStrongEnough}
            >
              Update password
            </Button>
          </form>
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
