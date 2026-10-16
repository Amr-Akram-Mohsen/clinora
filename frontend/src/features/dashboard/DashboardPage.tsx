/**
 * features/dashboard/DashboardPage.tsx
 *
 * Clinic Clinical Overview Dashboard: metrics, quick actions, and recent activity.
 */

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/features/auth/AuthProvider";
import { fetchPatients } from "@/api/clinical";
import { Button } from "@/components/Button/Button";
import { LoadingState } from "@/components/States/States";
import { RegisterPatientModal } from "@/features/patients/RegisterPatientModal";
import type { PatientListItem } from "@/types/clinical";

export function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [recentPatients, setRecentPatients] = useState<PatientListItem[]>([]);
  const [totalPatients, setTotalPatients] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isRegisterModalOpen, setIsRegisterModalOpen] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  async function loadDashboardData() {
    setIsLoading(true);
    try {
      const data = await fetchPatients({ page: 1, pageSize: 5 });
      setRecentPatients(data.items);
      setTotalPatients(data.total);
    } catch {
      // Graceful fallback
    } finally {
      setIsLoading(false);
    }
  }

  const roleName = user?.roles?.[0] || "Practitioner";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--spacing-6)", maxWidth: "1200px", margin: "0 auto" }}>
      {/* Welcome Banner */}
      <div
        style={{
          background: "linear-gradient(135deg, var(--color-brand-600), var(--color-brand-800))",
          color: "#ffffff",
          padding: "var(--spacing-6)",
          borderRadius: "var(--radius-lg)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          boxShadow: "var(--shadow-md)",
        }}
      >
        <div>
          <h1 style={{ fontSize: "var(--font-size-2xl)", fontWeight: "var(--font-weight-bold)", marginBottom: "var(--spacing-2)" }}>
            Welcome back, {user?.full_name}
          </h1>
          <p style={{ opacity: 0.9, fontSize: "var(--font-size-sm)" }}>
            Clinora Clinical Management Suite · Role: {roleName}
          </p>
        </div>
        <Button
          variant="secondary"
          onClick={() => setIsRegisterModalOpen(true)}
          style={{ background: "#ffffff", color: "var(--color-brand-700)", border: "none" }}
        >
          + Register New Patient
        </Button>
      </div>

      {/* Metrics Row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "var(--spacing-4)" }}>
        <div
          style={{
            background: "var(--color-surface-raised)",
            border: "1px solid var(--color-border-subtle)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--spacing-5)",
          }}
        >
          <div style={{ fontSize: "var(--font-size-xs)", textTransform: "uppercase", color: "var(--color-text-muted)", fontWeight: "var(--font-weight-bold)" }}>
            Registered Patients
          </div>
          <div style={{ fontSize: "var(--font-size-3xl)", fontWeight: "var(--font-weight-bold)", color: "var(--color-text-primary)", marginTop: "var(--spacing-2)" }}>
            {totalPatients}
          </div>
          <div style={{ fontSize: "var(--font-size-xs)", color: "var(--color-text-secondary)", marginTop: "var(--spacing-1)" }}>
            Active charts under clinic care
          </div>
        </div>

        <div
          style={{
            background: "var(--color-surface-raised)",
            border: "1px solid var(--color-border-subtle)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--spacing-5)",
          }}
        >
          <div style={{ fontSize: "var(--font-size-xs)", textTransform: "uppercase", color: "var(--color-text-muted)", fontWeight: "var(--font-weight-bold)" }}>
            Clinical Core Status
          </div>
          <div style={{ fontSize: "var(--font-size-3xl)", fontWeight: "var(--font-weight-bold)", color: "var(--color-status-success, #16a34a)", marginTop: "var(--spacing-2)" }}>
            Active
          </div>
          <div style={{ fontSize: "var(--font-size-xs)", color: "var(--color-text-secondary)", marginTop: "var(--spacing-1)" }}>
            SOAP encounters & Vitals tracking ready
          </div>
        </div>

        <div
          style={{
            background: "var(--color-surface-raised)",
            border: "1px solid var(--color-border-subtle)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--spacing-5)",
          }}
        >
          <div style={{ fontSize: "var(--font-size-xs)", textTransform: "uppercase", color: "var(--color-text-muted)", fontWeight: "var(--font-weight-bold)" }}>
            Security & Compliance
          </div>
          <div style={{ fontSize: "var(--font-size-3xl)", fontWeight: "var(--font-weight-bold)", color: "var(--color-brand-500)", marginTop: "var(--spacing-2)" }}>
            Audited
          </div>
          <div style={{ fontSize: "var(--font-size-xs)", color: "var(--color-text-secondary)", marginTop: "var(--spacing-1)" }}>
            Immutable append-only regulatory logs
          </div>
        </div>
      </div>

      {/* Recent Patients Table */}
      <div
        style={{
          background: "var(--color-surface-raised)",
          border: "1px solid var(--color-border-subtle)",
          borderRadius: "var(--radius-lg)",
          padding: "var(--spacing-5)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "var(--spacing-4)" }}>
          <h2 style={{ fontSize: "var(--font-size-lg)", fontWeight: "var(--font-weight-semibold)", color: "var(--color-text-primary)" }}>
            Recently Registered Patients
          </h2>
          <Button variant="secondary" size="sm" onClick={() => navigate("/patients")}>
            View All Patients →
          </Button>
        </div>

        {isLoading ? (
          <LoadingState message="Loading clinic activity…" />
        ) : recentPatients.length === 0 ? (
          <p style={{ fontSize: "var(--font-size-sm)", color: "var(--color-text-secondary)" }}>
            No patient charts created yet. Click "+ Register New Patient" to begin.
          </p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--color-border-subtle)", fontSize: "var(--font-size-xs)", color: "var(--color-text-secondary)", textTransform: "uppercase" }}>
                <th style={{ padding: "var(--spacing-3)" }}>Name</th>
                <th style={{ padding: "var(--spacing-3)" }}>Sex</th>
                <th style={{ padding: "var(--spacing-3)" }}>DOB</th>
                <th style={{ padding: "var(--spacing-3)" }}>Phone</th>
                <th style={{ padding: "var(--spacing-3)" }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {recentPatients.map((p) => (
                <tr
                  key={p.id}
                  style={{ borderBottom: "1px solid var(--color-border-subtle)", cursor: "pointer" }}
                  onClick={() => navigate(`/patients/${p.id}`)}
                >
                  <td style={{ padding: "var(--spacing-3)", fontWeight: "var(--font-weight-semibold)" }}>{p.full_name}</td>
                  <td style={{ padding: "var(--spacing-3)" }}>{p.gender}</td>
                  <td style={{ padding: "var(--spacing-3)" }}>{p.date_of_birth}</td>
                  <td style={{ padding: "var(--spacing-3)" }}>{p.phone}</td>
                  <td style={{ padding: "var(--spacing-3)" }}>
                    <Button variant="ghost" size="sm">
                      Open Chart →
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <RegisterPatientModal
        isOpen={isRegisterModalOpen}
        onClose={() => setIsRegisterModalOpen(false)}
        onSuccess={loadDashboardData}
      />
    </div>
  );
}
