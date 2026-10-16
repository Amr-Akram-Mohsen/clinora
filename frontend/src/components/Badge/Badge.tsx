/**
 * Badge.tsx
 *
 * Status badge component.
 * Variants: success, warning, error, info, neutral, ai.
 * The "ai" variant visually distinguishes AI-generated content
 * from physician-authored clinical data (Medical Safety Boundary requirement).
 */

import { type ReactNode } from "react";
import "./Badge.css";

type BadgeVariant = "success" | "warning" | "error" | "info" | "neutral" | "ai";

interface BadgeProps {
  variant?: BadgeVariant;
  showDot?: boolean;
  children: ReactNode;
  className?: string;
}

export function Badge({
  variant = "neutral",
  showDot = false,
  children,
  className = "",
}: BadgeProps) {
  return (
    <span
      className={`badge badge--${variant} ${className}`.trim()}
      aria-label={variant === "ai" ? `AI-generated: ${typeof children === "string" ? children : ""}` : undefined}
    >
      {showDot && <span className="badge__dot" aria-hidden="true" />}
      {children}
    </span>
  );
}
