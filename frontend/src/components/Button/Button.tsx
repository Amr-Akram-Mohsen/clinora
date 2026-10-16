/**
 * Button.tsx
 *
 * Reusable button component supporting:
 * - Variants: primary, secondary, ghost, danger
 * - Sizes: sm, md, lg
 * - Loading state with spinner
 * - Full-width option
 * - Semantic <button> with proper disabled/aria-disabled handling
 * - Keyboard: Enter and Space activate (native button behavior)
 * - Focus-visible ring via CSS
 */

import { type ButtonHTMLAttributes, type ReactNode } from "react";
import "./Button.css";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  fullWidth?: boolean;
  children: ReactNode;
}

export function Button({
  variant = "primary",
  size = "md",
  isLoading = false,
  fullWidth = false,
  disabled,
  children,
  className = "",
  ...rest
}: ButtonProps) {
  const isDisabled = disabled || isLoading;

  const classes = [
    "btn",
    `btn--${variant}`,
    `btn--${size}`,
    isLoading ? "btn--loading" : "",
    fullWidth ? "btn--full-width" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <button
      className={classes}
      disabled={isDisabled}
      aria-disabled={isDisabled}
      {...rest}
    >
      {isLoading && (
        <>
          <span className="btn__spinner" aria-hidden="true" />
          <span className="sr-only">Loading…</span>
        </>
      )}
      {children}
    </button>
  );
}
