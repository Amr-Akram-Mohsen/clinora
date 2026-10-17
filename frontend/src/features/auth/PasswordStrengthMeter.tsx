/**
 * features/auth/PasswordStrengthMeter.tsx
 *
 * Password strength indicator for password creation and reset.
 * Evaluates length, lowercase, uppercase, numbers, and special characters.
 */

import "./PasswordStrengthMeter.css";

interface PasswordStrengthMeterProps {
  password: string;
}

export function scorePassword(password: string): {
  score: number;
  label: string;
  isStrongEnough: boolean;
} {
  if (!password) {
    return { score: 0, label: "", isStrongEnough: false };
  }

  if (password.length < 8) {
    return { score: 0, label: "Too short (min 8 chars)", isStrongEnough: false };
  }

  let points = 0;
  if (/[a-z]/.test(password)) points++;
  if (/[A-Z]/.test(password)) points++;
  if (/\d/.test(password)) points++;
  if (/[^A-Za-z0-9]/.test(password)) points++;

  const labels = ["", "Weak", "Fair", "Good", "Strong"];
  return {
    score: points,
    label: labels[points] || "Weak",
    isStrongEnough: password.length >= 8 && points >= 2,
  };
}

export function PasswordStrengthMeter({ password }: PasswordStrengthMeterProps) {
  if (!password) return null;

  const { score, label } = scorePassword(password);

  return (
    <div className="pw-strength-meter" aria-live="polite">
      <div className="pw-strength-bars">
        {[1, 2, 3, 4].map((step) => (
          <div
            key={step}
            className={`pw-strength-segment ${step <= score ? `pw-strength-segment--active-${score}` : ""}`}
          />
        ))}
      </div>
      <div className={`pw-strength-label pw-strength-label--score-${score}`}>
        {label}
      </div>
    </div>
  );
}
