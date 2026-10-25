/**
 * features/auth/GoogleSignInButton.tsx
 *
 * Google OAuth 2.0 Identity Button.
 * Uses Google Identity Services (GSI) with direct credential callback,
 * with graceful fallback to standard OAuth redirect.
 */
/// <reference types="vite/client" />
import { useEffect, useRef, useState } from "react";
import { useAuth } from "./AuthProvider";
import "./GoogleSignInButton.css";

interface GoogleSignInButtonProps {
  label?: string;
  onError?: (err: string) => void;
  disabled?: boolean;
}

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (res: { credential: string }) => void;
            auto_select?: boolean;
          }) => void;
          renderButton: (
            parent: HTMLElement,
            options: {
              theme?: "outline" | "filled_blue" | "filled_black";
              size?: "large" | "medium" | "small";
              width?: number | string;
              text?: "signin_with" | "signup_with" | "continue_with";
              shape?: "rectangular" | "pill";
            }
          ) => void;
          prompt: () => void;
        };
      };
    };
  }
}

const GOOGLE_CLIENT_ID =
  (import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined) ||
  "1052842098229-cinjl2d6rhkch568u8hjmse275l2b3e5.apps.googleusercontent.com";

export function GoogleSignInButton({
  label = "Continue with Google",
  onError,
  disabled = false,
}: GoogleSignInButtonProps) {
  const { googleLogin } = useAuth();
  const [loading, setLoading] = useState(false);
  const [gsiRendered, setGsiRendered] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let timer: ReturnType<typeof setInterval> | null = null;

    function renderGsiButton() {
      if (window.google?.accounts?.id && containerRef.current) {
        try {
          window.google.accounts.id.initialize({
            client_id: GOOGLE_CLIENT_ID,
            callback: async (response) => {
              if (response.credential) {
                setLoading(true);
                try {
                  await googleLogin(response.credential);
                } catch (err: unknown) {
                  const message = err instanceof Error ? err.message : "Google authentication failed";
                  onError?.(message);
                } finally {
                  setLoading(false);
                }
              }
            },
          });

          containerRef.current.innerHTML = "";
          window.google.accounts.id.renderButton(containerRef.current, {
            theme: "outline",
            size: "large",
            width: 360,
            text: label.toLowerCase().includes("sign up") ? "signup_with" : "continue_with",
            shape: "rectangular",
          });
          setGsiRendered(true);
        } catch (err) {
          console.warn("Failed to render Google button:", err);
        }
      }
    }

    if (!document.getElementById("gsi-client-script")) {
      const script = document.createElement("script");
      script.id = "gsi-client-script";
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.defer = true;
      script.onload = () => renderGsiButton();
      document.body.appendChild(script);
    } else {
      renderGsiButton();
    }

    timer = setInterval(() => {
      if (window.google?.accounts?.id && containerRef.current && !containerRef.current.hasChildNodes()) {
        renderGsiButton();
      }
    }, 600);

    return () => {
      if (timer) clearInterval(timer);
    };
  }, [googleLogin, label, onError]);

  function handleFallbackRedirect() {
    window.location.href = "/api/v1/auth/google/login";
  }

  return (
    <div className="google-signin-container" style={{ width: "100%", display: "flex", flexDirection: "column", alignItems: "center" }}>
      {/* Container where Google's official popup button renders */}
      <div
        ref={containerRef}
        style={{
          width: "100%",
          display: gsiRendered ? "flex" : "none",
          justifyContent: "center",
          minHeight: "44px",
        }}
      />

      {/* Styled Clinora button if Google GSI iframe has not rendered */}
      {!gsiRendered && (
        <button
          type="button"
          className="google-signin-btn"
          onClick={handleFallbackRedirect}
          disabled={disabled || loading}
          aria-label={label}
        >
          <svg className="google-signin-btn__icon" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
            />
          </svg>
          <span className="google-signin-btn__text">
            {loading ? "Connecting to Google…" : label}
          </span>
        </button>
      )}
    </div>
  );
}
