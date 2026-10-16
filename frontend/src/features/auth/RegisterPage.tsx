/**
 * features/auth/RegisterPage.tsx
 *
 * Registration / Sign-up page for clinicians and clinic administrators.
 *
 * Layout: Two-column (brand panel | form panel) on ≥1024px, single-column mobile.
 *
 * Accessibility:
 * - <main> landmark
 * - <form> with semantic inputs and labels
 * - Password matching & length client validation with aria-live error announcements
 * - Focus-visible management on interactive elements
 * - Theme toggle with accessible aria labels
 */

import { type FormEvent, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "./AuthProvider";
import { Button } from "@/components/Button/Button";
import { FormField, Input } from "@/components/Input/Input";
import type { ApiError } from "@/types/api";
import "./RegisterPage.css";

const REGISTER_BENEFITS = [
  "Instant clinical workspace setup",
  "Role-based access (Physician, Nurse, Admin)",
  "Tenancy isolation for your clinic",
  "HIPAA-conscious immutable audit logging",
];

const ROLES = [
  { value: "DOCTOR", label: "Physician / Doctor" },
  { value: "ADMIN", label: "Clinic Administrator" },
  { value: "NURSE", label: "Clinical Nurse" },
  { value: "RECEPTIONIST", label: "Front Desk / Reception" },
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
      className="register-page__theme-toggle"
      onClick={toggle}
      aria-label={`Switch to ${isDark ? "light" : "dark"} mode`}
      title={`Switch to ${isDark ? "light" : "dark"} mode`}
    >
      {isDark ? (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="12" cy="12" r="5" stroke="currentColor" strokeWidth="1.5" />
          <path
            d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
          />
        </svg>
      ) : (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M21 12.79A9 9 0 1111.21 3a7 7 0 009.79 9.79z"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      )}
    </button>
  );
}

export function RegisterPage() {
  const { register, isAuthenticated, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [clinicName, setClinicName] = useState("");
  const [role, setRole] = useState("DOCTOR");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const errorRef = useRef<HTMLDivElement>(null);

  // Redirect if already authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      navigate("/", { replace: true });
    }
  }, [isAuthenticated, authLoading, navigate]);

  // Focus error banner for screen readers
  useEffect(() => {
    if (error) {
      errorRef.current?.focus();
    }
  }, [error]);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match. Please verify your password.");
      return;
    }

    setIsSubmitting(true);

    try {
      await register({
        full_name: fullName.trim(),
        organization_name: clinicName.trim() || undefined,
        role,
        email: email.toLowerCase().trim(),
        password,
      });
      navigate("/", { replace: true });
    } catch (err) {
      const apiErr = err as ApiError;
      setError(apiErr.message ?? "Registration failed. Please check the details entered.");
    } finally {
      setIsSubmitting(false);
    }
  }

  const isFormValid =
    fullName.trim() &&
    email.trim() &&
    password.length >= 8 &&
    confirmPassword &&
    password === confirmPassword;

  return (
    <main className="register-page">
      <ThemeToggle />

      {/* Brand panel */}
      <aside className="register-page__brand" aria-hidden="true">
        <div className="register-page__brand-logo">
          <div className="register-page__brand-logo-mark">C</div>
          <span className="register-page__brand-name">Clinora</span>
        </div>

        <div className="register-page__brand-content">
          <h1 className="register-page__brand-heading">
            Join the new standard<br />in clinical intelligence.
          </h1>
          <p className="register-page__brand-subheading">
            Equip your practice with longitudinal clinical records, automated
            traceability, and doctor-in-the-loop insights.
          </p>
          <ul className="register-page__brand-features">
            {REGISTER_BENEFITS.map((b) => (
              <li key={b} className="register-page__brand-feature">
                <span className="register-page__brand-feature-dot" />
                {b}
              </li>
            ))}
          </ul>
        </div>

        <p className="register-page__brand-tagline">
          Zero vendor lock-in. Full clinical audit transparency.
        </p>
      </aside>

      {/* Form panel */}
      <section className="register-page__form-panel">
        <div className="register-page__form-container">
          {/* Mobile logo */}
          <div className="register-page__mobile-logo" aria-hidden="true">
            <div className="register-page__mobile-logo-mark">C</div>
            <span className="register-page__mobile-logo-name">Clinora</span>
          </div>

          <h2 className="register-page__heading">Create an account</h2>
          <p className="register-page__subheading">
            Set up your clinical credentials to begin
          </p>

          {error && (
            <div
              ref={errorRef}
              className="register-page__form-error"
              role="alert"
              aria-live="assertive"
              tabIndex={-1}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true" style={{ flexShrink: 0 }}>
                <path
                  d="M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              {error}
            </div>
          )}

          <form
            className="register-page__form"
            onSubmit={handleSubmit}
            noValidate
            aria-label="Create clinical account form"
          >
            <Input
              id="register-fullname"
              type="text"
              label="Full Name"
              placeholder="Dr. Alex Morgan"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
              autoFocus
              disabled={isSubmitting}
            />

            <div className="register-page__form-grid">
              <Input
                id="register-clinic"
                type="text"
                label="Clinic / Practice Name"
                placeholder="Clinora Health (or leave empty)"
                value={clinicName}
                onChange={(e) => setClinicName(e.target.value)}
                disabled={isSubmitting}
                hint="Optional: creates a dedicated clinic tenant"
              />

              <FormField label="Clinical Role" htmlFor="register-role" required>
                <select
                  id="register-role"
                  className="register-page__select"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  disabled={isSubmitting}
                >
                  {ROLES.map((r) => (
                    <option key={r.value} value={r.value}>
                      {r.label}
                    </option>
                  ))}
                </select>
              </FormField>
            </div>

            <Input
              id="register-email"
              type="email"
              label="Email address"
              placeholder="alex.morgan@clinic.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              disabled={isSubmitting}
            />

            <div className="register-page__form-grid">
              <Input
                id="register-password"
                type="password"
                label="Password"
                placeholder="At least 8 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="new-password"
                disabled={isSubmitting}
                hint={password && password.length < 8 ? "Must be ≥ 8 chars" : undefined}
              />

              <Input
                id="register-confirm-password"
                type="password"
                label="Confirm Password"
                placeholder="Re-enter password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                autoComplete="new-password"
                disabled={isSubmitting}
                error={
                  confirmPassword && password !== confirmPassword
                    ? "Passwords do not match"
                    : undefined
                }
              />
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              fullWidth
              isLoading={isSubmitting}
              disabled={!isFormValid}
            >
              Create Account & Enter Workspace
            </Button>

            <div className="register-page__footer-prompt">
              Already have an account?{" "}
              <Link to="/login" className="register-page__link">
                Sign in here
              </Link>
            </div>
          </form>
        </div>
      </section>
    </main>
  );
}
