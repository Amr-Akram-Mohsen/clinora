/**
 * Input.tsx
 *
 * Reusable input field with FormField wrapper.
 *
 * FormField: label + hint + error message with proper aria linkage.
 * Input: controlled text input with error styling and accessible description.
 *
 * Accessibility:
 * - <label> associated via htmlFor
 * - Error message linked via aria-describedby
 * - Hint text linked via aria-describedby (combined with error ID)
 * - aria-invalid on error state
 */

import {
  type InputHTMLAttributes,
  type ReactNode,
  useId,
} from "react";
import "./Input.css";

// ---- FormField --------------------------------------------------------

interface FormFieldProps {
  label: string;
  required?: boolean;
  hint?: string;
  error?: string;
  htmlFor?: string;
  children: ReactNode;
}

export function FormField({
  label,
  required,
  hint,
  error,
  htmlFor,
  children,
}: FormFieldProps) {
  return (
    <div className="form-field">
      <label
        className={`form-field__label ${required ? "form-field__label--required" : ""}`}
        htmlFor={htmlFor}
      >
        {label}
      </label>
      {children}
      {hint && !error && (
        <span className="form-field__hint" id={htmlFor ? `${htmlFor}-hint` : undefined}>
          {hint}
        </span>
      )}
      {error && (
        <span
          className="form-field__error"
          id={htmlFor ? `${htmlFor}-error` : undefined}
          role="alert"
          aria-live="polite"
        >
          {error}
        </span>
      )}
    </div>
  );
}

// ---- Input ------------------------------------------------------------

type InputSize = "sm" | "md" | "lg";

interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "size"> {
  size?: InputSize;
  error?: string;
  hint?: string;
  label?: string;
}

export function Input({
  size = "md",
  error,
  hint,
  label,
  id: externalId,
  className = "",
  ...rest
}: InputProps) {
  const generatedId = useId();
  const inputId = externalId ?? generatedId;

  const ariaDescribedBy = [
    error ? `${inputId}-error` : null,
    hint && !error ? `${inputId}-hint` : null,
  ]
    .filter(Boolean)
    .join(" ") || undefined;

  const classes = [
    "input",
    size !== "md" ? `input--${size}` : "",
    error ? "input--error" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const inputEl = (
    <input
      id={inputId}
      className={classes}
      aria-invalid={!!error}
      aria-describedby={ariaDescribedBy}
      {...rest}
    />
  );

  if (label) {
    return (
      <FormField
        label={label}
        required={rest.required}
        hint={hint}
        error={error}
        htmlFor={inputId}
      >
        {inputEl}
      </FormField>
    );
  }

  return inputEl;
}
