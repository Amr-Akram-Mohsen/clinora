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
import { ForgotPasswordPage } from "@/features/auth/ForgotPasswordPage";
import { ResetPasswordPage } from "@/features/auth/ResetPasswordPage";
import { VerifyEmailPage } from "@/features/auth/VerifyEmailPage";
import { AppShell } from "@/components/Layout/AppShell";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { PatientListPage } from "@/features/patients/PatientListPage";
import { PatientDetailPage } from "@/features/patients/PatientDetailPage";
import { EncounterWorkspace } from "@/features/encounters/EncounterWorkspace";
import { LoadingState } from "@/components/States/States";

// Import Admin components:
import { AdminLayout } from "@/features/admin/AdminLayout";
import { StaffManagementPage } from "@/features/admin/StaffManagementPage";
import { ClinicSettingsPage } from "@/features/admin/ClinicSettingsPage";
import { AuditLogViewerPage } from "@/features/admin/AuditLogViewerPage";



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
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password/:token" element={<ResetPasswordPage />} />
      <Route path="/verify-email" element={<VerifyEmailPage />} />
      <Route path="/verify-email/:token" element={<VerifyEmailPage />} />
      <Route path="/resend-verification" element={<VerifyEmailPage />} />

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

      {/* Administration Routes */}
      <Route
        path="/admin"
        element={
          <ProtectedRoute>
            <AdminLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/admin/staff" replace />} />
        <Route path="staff" element={<StaffManagementPage />} />
        <Route path="settings" element={<ClinicSettingsPage />} />
        <Route path="audit" element={<AuditLogViewerPage />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

// function AppRoutes() {
//   return (
//     <Routes>
//       {/* Public Auth Routes */}
//       <Route path="/login" element={<LoginPage />} />
//       <Route path="/register" element={<RegisterPage />} />
//       <Route path="/signup" element={<Navigate to="/register" replace />} />
//       <Route path="/forgot-password" element={<ForgotPasswordPage />} />
//       <Route path="/reset-password/:token" element={<ResetPasswordPage />} />
//       <Route path="/verify-email" element={<VerifyEmailPage />} />
//       <Route path="/verify-email/:token" element={<VerifyEmailPage />} />
//       <Route path="/resend-verification" element={<VerifyEmailPage />} />

//       {/* Protected Clinical Workstation Routes */}
//       <Route
//         path="/"
//         element={
//           <ProtectedRoute>
//             <DashboardPage />
//           </ProtectedRoute>
//         }
//       />
//       <Route
//         path="/patients"
//         element={
//           <ProtectedRoute>
//             <PatientListPage />
//           </ProtectedRoute>
//         }
//       />
//       <Route
//         path="/patients/:id"
//         element={
//           <ProtectedRoute>
//             <PatientDetailPage />
//           </ProtectedRoute>
//         }
//       />
//       <Route
//         path="/encounters/:id"
//         element={
//           <ProtectedRoute>
//             <EncounterWorkspace />
//           </ProtectedRoute>
//         }
//       />

//       {/* Fallback */}
//       <Route path="*" element={<Navigate to="/" replace />} />
//     </Routes>

//     <Route
//       path="/admin"
//       element={
//         <ProtectedRoute>
//           <AdminLayout />
//         </ProtectedRoute>
//       }
//     >
//     <Route index element={<Navigate to="/admin/staff" replace />} />
//     <Route path="staff" element={<StaffManagementPage />} />
//     <Route path="settings" element={<ClinicSettingsPage />} />
//     <Route path="audit" element={<AuditLogViewerPage />} />
//   </Route>

//   );
// }

export function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}
