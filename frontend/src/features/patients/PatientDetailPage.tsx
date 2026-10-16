/**
 * features/patients/PatientDetailPage.tsx
 *
 * Longitudinal patient chart: demographics, allergies, visit history timeline,
 * recent vitals observations, and encounter initiation.
 */

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  fetchPatientDetail,
  fetchPatientObservations,
  fetchPatientPrescriptions,
  fetchPatientVisits,
  startEncounter,
} from "@/api/clinical";
import { Button } from "@/components/Button/Button";
import { Badge } from "@/components/Badge/Badge";
import { EmptyState, ErrorState, LoadingState } from "@/components/States/States";
import { AddAllergyModal } from "./AddAllergyModal";
import type { Observation, Patient, Prescription, VisitListItem } from "@/types/clinical";
import "./PatientDetailPage.css";

export function PatientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [patient, setPatient] = useState<Patient | null>(null);
  const [visits, setVisits] = useState<VisitListItem[]>([]);
  const [vitals, setVitals] = useState<Observation[]>([]);
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [isStartingEncounter, setIsStartingEncounter] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAllergyModalOpen, setIsAllergyModalOpen] = useState(false);

  useEffect(() => {
    if (id) {
      loadPatientData(id);
    }
  }, [id]);

  async function loadPatientData(patientId: string) {
    setIsLoading(true);
    setError(null);
    try {
      const [patientData, visitData, vitalsData, rxData] = await Promise.all([
        fetchPatientDetail(patientId),
        fetchPatientVisits(patientId, 1, 20),
        fetchPatientObservations(patientId, 10),
        fetchPatientPrescriptions(patientId, true),
      ]);
      setPatient(patientData);
      setVisits(visitData.items);
      setVitals(vitalsData);
      setPrescriptions(rxData);
    } catch (err: any) {
      setError(err?.message || "Failed to load patient chart.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleStartEncounter() {
    if (!patient) return;
    setIsStartingEncounter(true);
    try {
      const visit = await startEncounter({
        patient_id: patient.id,
        chief_complaint: "Routine Follow-up / Consultation",
      });
      navigate(`/encounters/${visit.id}`);
    } catch (err: any) {
      alert(err?.message || "Failed to start encounter.");
    } finally {
      setIsStartingEncounter(false);
    }
  }

  if (isLoading) {
    return <LoadingState message="Loading patient chart and longitudinal history…" />;
  }

  if (error || !patient) {
    return <ErrorState message={error || "Patient not found."} onRetry={() => id && loadPatientData(id)} />;
  }

  const birthYear = new Date(patient.date_of_birth).getFullYear();
  const currentYear = new Date().getFullYear();
  const calculatedAge = currentYear - birthYear;

  return (
    <div className="patient-detail">
      {/* Patient Bio Header */}
      <div className="patient-detail__header">
        <div className="patient-detail__bio">
          <h1>{patient.full_name}</h1>
          <div className="patient-detail__badges">
            <Badge variant="info">{patient.gender}</Badge>
            <Badge variant="neutral">{calculatedAge} years old ({patient.date_of_birth})</Badge>
            {patient.blood_type && <Badge variant="info">Blood: {patient.blood_type}</Badge>}
            <Badge variant="success">Active Patient</Badge>
          </div>

          <div className="patient-detail__grid">
            <div className="patient-detail__grid-item">
              <strong>Phone</strong>
              <span>{patient.phone}</span>
            </div>
            <div className="patient-detail__grid-item">
              <strong>National ID</strong>
              <span>{patient.national_id || "Not documented"}</span>
            </div>
            <div className="patient-detail__grid-item">
              <strong>Email</strong>
              <span>{patient.email || "None"}</span>
            </div>
            <div className="patient-detail__grid-item">
              <strong>Emergency Contact</strong>
              <span>
                {patient.emergency_contact_name
                  ? `${patient.emergency_contact_name} (${patient.emergency_contact_phone || ""})`
                  : "None recorded"}
              </span>
            </div>
          </div>
        </div>

        <div>
          <Button
            variant="primary"
            onClick={handleStartEncounter}
            isLoading={isStartingEncounter}
          >
            + Start Consultation Encounter
          </Button>
        </div>
      </div>

      {/* Allergies Alert Banner */}
      <div className="patient-detail__allergy-card">
        <div>
          <h2 style={{ fontSize: "var(--font-size-base)", fontWeight: "var(--font-weight-bold)", color: "var(--color-status-error, #b91c1c)" }}>
            DOCUMENTED ALLERGIES & ADVERSE REACTIONS
          </h2>
          {patient.allergies.length === 0 ? (
            <p style={{ fontSize: "var(--font-size-sm)", color: "var(--color-text-secondary)", marginTop: "4px" }}>
              No documented allergies. Always verify with patient before prescribing.
            </p>
          ) : (
            <div className="patient-detail__allergy-list">
              {patient.allergies.map((allergy) => (
                <Badge key={allergy.id} variant="error">
                  {allergy.allergen} ({allergy.severity}) {allergy.reaction ? `— ${allergy.reaction}` : ""}
                </Badge>
              ))}
            </div>
          )}
        </div>
        <Button variant="secondary" size="sm" onClick={() => setIsAllergyModalOpen(true)}>
          + Record Allergy
        </Button>
      </div>

      {/* Content Columns: Left (Visits) / Right (Vitals & Rx) */}
      <div className="patient-detail__columns">
        {/* Left: Visits Timeline */}
        <section className="patient-detail__section">
          <div className="patient-detail__section-header">
            <h2>Clinical Encounters (Longitudinal History)</h2>
            <span style={{ fontSize: "var(--font-size-sm)", color: "var(--color-text-muted)" }}>
              {visits.length} recorded
            </span>
          </div>

          {visits.length === 0 ? (
            <EmptyState
              title="No clinical visits yet"
              message="Click 'Start Consultation Encounter' above to begin documenting patient care."
            />
          ) : (
            <div className="patient-detail__timeline">
              {visits.map((v) => (
                <div
                  key={v.id}
                  className="patient-detail__visit-item"
                  onClick={() => navigate(`/encounters/${v.id}`)}
                >
                  <div>
                    <div className="patient-detail__visit-date">
                      {new Date(v.visit_date).toLocaleDateString(undefined, {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </div>
                    <div className="patient-detail__visit-complaint">{v.chief_complaint}</div>
                  </div>
                  <div>
                    <Badge variant={v.status === "SIGNED" ? "success" : "warning"}>
                      {v.status === "SIGNED" ? "Signed & Locked" : "Draft (In Progress)"}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Right: Vitals & Prescriptions */}
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--spacing-6)" }}>
          {/* Active Prescriptions */}
          <section className="patient-detail__section">
            <div className="patient-detail__section-header">
              <h2>Active Prescriptions</h2>
            </div>
            {prescriptions.length === 0 ? (
              <p style={{ fontSize: "var(--font-size-sm)", color: "var(--color-text-muted)" }}>
                No active medications prescribed.
              </p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "var(--spacing-2)" }}>
                {prescriptions.map((rx) => (
                  <div
                    key={rx.id}
                    style={{
                      padding: "var(--spacing-3)",
                      background: "var(--color-surface-sunken)",
                      borderRadius: "var(--radius-md)",
                      border: "1px solid var(--color-border-subtle)",
                    }}
                  >
                    <div style={{ fontWeight: "var(--font-weight-semibold)", fontSize: "var(--font-size-sm)" }}>
                      {rx.medication_name} — {rx.dosage}
                    </div>
                    <div style={{ fontSize: "var(--font-size-xs)", color: "var(--color-text-secondary)" }}>
                      {rx.frequency} ({rx.route}) · {rx.duration}
                    </div>
                    {rx.instructions && (
                      <div style={{ fontSize: "var(--font-size-xs)", color: "var(--color-text-muted)", marginTop: "2px" }}>
                        {rx.instructions}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Recent Vitals */}
          <section className="patient-detail__section">
            <div className="patient-detail__section-header">
              <h2>Recent Vitals</h2>
            </div>
            {vitals.length === 0 ? (
              <p style={{ fontSize: "var(--font-size-sm)", color: "var(--color-text-muted)" }}>
                No vital signs logged yet.
              </p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "var(--spacing-2)" }}>
                {vitals.map((obs) => (
                  <div
                    key={obs.id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "var(--spacing-2) var(--spacing-3)",
                      background: "var(--color-surface-sunken)",
                      borderRadius: "var(--radius-sm)",
                    }}
                  >
                    <span style={{ fontSize: "var(--font-size-sm)", color: "var(--color-text-secondary)" }}>
                      {obs.type.replace(/_/g, " ")}
                    </span>
                    <div style={{ display: "flex", alignItems: "center", gap: "var(--spacing-2)" }}>
                      <span style={{ fontWeight: "var(--font-weight-semibold)", fontSize: "var(--font-size-sm)" }}>
                        {obs.value} {obs.unit}
                      </span>
                      {obs.is_abnormal && <Badge variant="error">Abnormal</Badge>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      </div>

      <AddAllergyModal
        patientId={patient.id}
        isOpen={isAllergyModalOpen}
        onClose={() => setIsAllergyModalOpen(false)}
        onSuccess={() => loadPatientData(patient.id)}
      />
    </div>
  );
}
