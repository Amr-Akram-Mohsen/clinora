/**
 * App.tsx
 *
 * Root application component.
 * Sets up routing, protected routes wrapped in AppShell, and AuthProvider.
 */

import { type ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "@/features/auth/AuthProvider";
import { LoginPage } from "@/features/auth/LoginPage";
import { RegisterPage } from "@/features/auth/RegisterPage";
import { AppShell } from "@/components/Layout/AppShell";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { PatientListPage } from "@/features/patients/PatientListPage";
import { PatientDetailPage } from "@/features/patients/PatientDetailPage";
import { EncounterWorkspace } from "@/features/encounters/EncounterWorkspace";
import { LoadingState } from "@/components/States/States";

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingState message="Restoring clinical session…" />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <AppShell>{children}</AppShell>;
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public Auth Routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/signup" element={<Navigate to="/register" replace />} />

      {/* Protected Clinical Workstation Routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/patients"
        element={
          <ProtectedRoute>
            <PatientListPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/patients/:id"
        element={
          <ProtectedRoute>
            <PatientDetailPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/encounters/:id"
        element={
          <ProtectedRoute>
            <EncounterWorkspace />
          </ProtectedRoute>
        }
      />

      {/* Fallback */}
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
