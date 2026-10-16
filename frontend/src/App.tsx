/**
 * App.tsx
 *
 * Root application component.
 * Sets up routing and wraps everything in AuthProvider.
 *
 * Phase 1 routes:
 * - /login → LoginPage (public)
 * - /      → Dashboard placeholder (protected, redirects to /login if not authenticated)
 *
 * Future phases will expand routing as features are added.
 */

import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "@/features/auth/AuthProvider";
import { LoginPage } from "@/features/auth/LoginPage";
import { RegisterPage } from "@/features/auth/RegisterPage";
import { LoadingState } from "@/components/States/States";
import { type ReactNode } from "react";

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingState message="Restoring session…" />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

function DashboardPlaceholder() {
  const { user, logout } = useAuth();
  return (
    <main style={{ padding: "2rem", fontFamily: "var(--font-family-sans)" }}>
      <h1 style={{ color: "var(--color-text-primary)", marginBottom: "0.5rem" }}>
        Dashboard
      </h1>
      <p style={{ color: "var(--color-text-secondary)", marginBottom: "1.5rem" }}>
        Welcome, {user?.full_name}. Clinical features arrive in Phase 2.
      </p>
      <button
        onClick={logout}
        style={{
          padding: "0.5rem 1rem",
          background: "var(--color-brand-500)",
          color: "white",
          border: "none",
          borderRadius: "var(--radius-md)",
          cursor: "pointer",
          fontFamily: "inherit",
        }}
      >
        Sign out
      </button>
    </main>
  );
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/signup" element={<Navigate to="/register" replace />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardPlaceholder />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}
