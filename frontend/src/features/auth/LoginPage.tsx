/**
 * features/auth/LoginPage.tsx
 *
 * Authentication login page.
 *
 * Layout: Two-column (brand panel | form panel) on ≥1024px, single-column mobile.
 *
 * Accessibility:
 * - <main> landmark
 * - <form> with submit handler
 * - Inputs have labels via the FormField/Input wrapper
 * - Error messages linked via aria-describedby
 * - Error banner has role="alert" for screen-reader announcement
 * - Keyboard: Tab navigation, Enter submits form
 * - Focus moves to error banner on failure for screen readers
 * - Theme toggle has accessible label
 */

import { type FormEvent, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "./AuthProvider";
import { Button } from "@/components/Button/Button";
import { Input } from "@/components/Input/Input";
import { GoogleSignInButton } from "./GoogleSignInButton";
import type { ApiError } from "@/types/api";
import "./LoginPage.css";

const FEATURES = [
  "Longitudinal patient records",
  "AI-assisted visit preparation",
  "Clinical analytics and insights",
  "Secure audit trail",
];

function ThemeToggle() {
  const [isDark, setIsDark] = useState(
    () => document.documentElement.getAttribute("data-theme") === "dark"
  );

  function toggle() {
    const next = isDark ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    setIsDark(!isDark);
  }

  return (
    <button
      type="button"
      className="login-page__theme-toggle"
      onClick={toggle}
      aria-label={`Switch to ${isDark ? "light" : "dark"} mode`}
      title={`Switch to ${isDark ? "light" : "dark"} mode`}
    >
      {isDark ? (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="12" cy="12" r="5" stroke="currentColor" strokeWidth="1.5" />
          <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"
            stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      ) : (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M21 12.79A9 9 0 1111.21 3a7 7 0 009.79 9.79z"
            stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      )}
    </button>
  );
}

export function LoginPage() {
  const { login, isAuthenticated, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const errorRef = useRef<HTMLDivElement>(null);

  // Redirect if already authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      navigate("/", { replace: true });
    }
  }, [isAuthenticated, authLoading, navigate]);

  // Move focus to error banner for screen-reader announcement
  useEffect(() => {
    if (error) {
      errorRef.current?.focus();
    }
  }, [error]);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await login({ email: email.toLowerCase().trim(), password });
      navigate("/", { replace: true });
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.message ?? "Login failed. Please check your credentials.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="login-page">
      <ThemeToggle />

      {/* Brand panel */}
      <aside className="login-page__brand" aria-hidden="true">
        <div className="login-page__brand-logo">
          <div className="login-page__brand-logo-mark">C</div>
          <span className="login-page__brand-name">Clinora</span>
        </div>

        <div className="login-page__brand-content">
          <h1 className="login-page__brand-heading">
            Clinical care,<br />powered by insight.
          </h1>
          <p className="login-page__brand-subheading">
            An AI-assisted clinical management platform designed for physicians who
            demand precision, traceability, and trust.
          </p>
          <ul className="login-page__brand-features">
            {FEATURES.map((f) => (
              <li key={f} className="login-page__brand-feature">
                <span className="login-page__brand-feature-dot" />
                {f}
              </li>
            ))}
          </ul>
        </div>

        <p className="login-page__brand-tagline">
          The physician remains the decision-maker.
        </p>
      </aside>

      {/* Form panel */}
      <section className="login-page__form-panel">
        <div className="login-page__form-container">
          {/* Mobile logo */}
          <div className="login-page__mobile-logo" aria-hidden="true">
            <div className="login-page__mobile-logo-mark">C</div>
            <span className="login-page__mobile-logo-name">Clinora</span>
          </div>

          <h2 className="login-page__heading">Welcome back</h2>
          <p className="login-page__subheading">
            Sign in to your clinical workspace
          </p>

          {error && (
            <div
              ref={errorRef}
              className="login-page__form-error"
              role="alert"
              aria-live="assertive"
              tabIndex={-1}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true" style={{ flexShrink: 0 }}>
                <path d="M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
                  stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              {error}
            </div>
          )}

          <form
            className="login-page__form"
            onSubmit={handleSubmit}
            noValidate
            aria-label="Sign in form"
          >
            <Input
              id="login-email"
              type="email"
              label="Email address"
              placeholder="you@clinic.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              autoFocus
              disabled={isSubmitting}
            />

            <div>
              <Input
                id="login-password"
                type="password"
                label="Password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                disabled={isSubmitting}
              />
              <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "var(--spacing-1)" }}>
                <Link to="/forgot-password" className="login-page__link" style={{ fontSize: "var(--font-size-xs)" }}>
                  Forgot password?
                </Link>
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              fullWidth
              isLoading={isSubmitting}
              disabled={!email || !password}
            >
              Sign in
            </Button>

            <div className="auth-divider" style={{ display: "flex", alignItems: "center", gap: "var(--spacing-3)", margin: "var(--spacing-3) 0" }}>
              <div style={{ flex: 1, height: "1px", backgroundColor: "var(--color-border-subtle)" }} />
              <span style={{ fontSize: "var(--font-size-xs)", color: "var(--color-text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>Or</span>
              <div style={{ flex: 1, height: "1px", backgroundColor: "var(--color-border-subtle)" }} />
            </div>

            <GoogleSignInButton onError={(err) => setError(err)} disabled={isSubmitting} />

            {error && error.toLowerCase().includes("verify") && (
              <div style={{ textAlign: "center", marginTop: "var(--spacing-2)", fontSize: "var(--font-size-xs)" }}>
                <Link to="/verify-email" className="login-page__link">
                  Resend verification link
                </Link>
              </div>
            )}

            <div className="login-page__footer-prompt">
              Don't have an account?{" "}
              <Link to="/register" className="login-page__link">
                Sign up for an account
              </Link>
            </div>

            {/* Quick Demo Credentials Box */}
            <div className="login-page__demo-card">
              <div className="login-page__demo-card-header">
                <span className="login-page__demo-badge">Demo / Dev Access</span>
                <button
                  type="button"
                  className="login-page__demo-fill-btn"
                  onClick={() => {
                    setEmail("admin@clinora.com");
                    setPassword("ChangeMe123!");
                  }}
                >
                  Quick-fill Demo
                </button>
              </div>
              <div className="login-page__demo-card-body">
                <div>
                  <span className="login-page__demo-label">User:</span> <code>admin@clinora.com</code>
                </div>
                <div>
                  <span className="login-page__demo-label">Pass:</span> <code>ChangeMe123!</code>
                </div>
              </div>
            </div>
          </form>
        </div>
      </section>
    </main>
  );
}
