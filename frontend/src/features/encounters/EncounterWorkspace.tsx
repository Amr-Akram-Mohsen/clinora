/**
 * features/encounters/EncounterWorkspace.tsx
 *
 * The Physician's Consultation Desk:
 * - Structured SOAP Documentation (Subjective, Objective, Assessment, Plan)
 * - Vitals intake with physiological abnormality detection
 * - Medication prescribing
 * - Digital sign-off locking the medical record
 */

import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  fetchEncounter,
  fetchPatientDetail,
  issueVisitPrescriptions,
  recordVisitObservations,
  signEncounter,
  updateEncounterDraft,
} from "@/api/clinical";
import { Button } from "@/components/Button/Button";
import { Input } from "@/components/Input/Input";
import { Badge } from "@/components/Badge/Badge";
import { ErrorState, LoadingState } from "@/components/States/States";
import type { Patient, Visit } from "@/types/clinical";
import "./EncounterWorkspace.css";

export function EncounterWorkspace() {
  const { id } = useParams<{ id: string }>();

  const [visit, setVisit] = useState<Visit | null>(null);
  const [patient, setPatient] = useState<Patient | null>(null);

  // Form states
  const [chiefComplaint, setChiefComplaint] = useState("");
  const [subjective, setSubjective] = useState("");
  const [objective, setObjective] = useState("");
  const [assessment, setAssessment] = useState("");
  const [plan, setPlan] = useState("");

  // Vitals inputs
  const [bpSys, setBpSys] = useState("");
  const [bpDia, setBpDia] = useState("");
  const [pulse, setPulse] = useState("");
  const [temp, setTemp] = useState("");
  const [respRate, setRespRate] = useState("");
  const [o2Sat, setO2Sat] = useState("");
  const [weightKg, setWeightKg] = useState("");
  const [heightCm, setHeightCm] = useState("");

  // Prescriptions inputs
  const [medName, setMedName] = useState("");
  const [dosage, setDosage] = useState("");
  const [frequency, setFrequency] = useState("Once daily");
  const [duration, setDuration] = useState("7 days");
  const [instructions, setInstructions] = useState("");

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isSigning, setIsSigning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadEncounter(id);
    }
  }, [id]);

  async function loadEncounter(visitId: string) {
    setIsLoading(true);
    setError(null);
    try {
      const visitData = await fetchEncounter(visitId);
      setVisit(visitData);

      // Hydrate forms
      setChiefComplaint(visitData.chief_complaint);
      setSubjective(visitData.subjective_notes || "");
      setObjective(visitData.objective_notes || "");
      setAssessment(visitData.assessment_notes || "");
      setPlan(visitData.plan_notes || "");

      // Load patient for context
      const patientData = await fetchPatientDetail(visitData.patient_id);
      setPatient(patientData);
    } catch (err: any) {
      setError(err?.message || "Failed to load encounter.");
    } finally {
      setIsLoading(false);
    }
  }

  const isLocked = visit?.status === "SIGNED";

  async function handleSaveDraft() {
    if (!id || isLocked) return;
    setIsSaving(true);
    setSuccessBanner(null);
    try {
      const updated = await updateEncounterDraft(id, {
        chief_complaint: chiefComplaint,
        subjective_notes: subjective,
        objective_notes: objective,
        assessment_notes: assessment,
        plan_notes: plan,
      });
      setVisit(updated);
      setSuccessBanner("Draft notes successfully saved.");
    } catch (err: any) {
      alert(err?.message || "Failed to save draft.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleSignEncounter() {
    if (!id || isLocked) return;
    const confirmed = window.confirm(
      "Are you sure you want to sign this encounter? Once signed, clinical notes are locked per medical compliance standards."
    );
    if (!confirmed) return;

    setIsSigning(true);
    try {
      // First save draft
      await updateEncounterDraft(id, {
        chief_complaint: chiefComplaint,
        subjective_notes: subjective,
        objective_notes: objective,
        assessment_notes: assessment,
        plan_notes: plan,
      });

      // Sign encounter
      const signed = await signEncounter(id);
      setVisit(signed);
      setSuccessBanner("Encounter permanently signed and locked.");
    } catch (err: any) {
      alert(err?.message || "Failed to sign encounter.");
    } finally {
      setIsSigning(false);
    }
  }

  async function handleRecordVitals(e: React.FormEvent) {
    e.preventDefault();
    if (!id || isLocked) return;

    const items = [];
    if (bpSys) items.push({ type: "BLOOD_PRESSURE_SYS", value: parseFloat(bpSys), unit: "mmHg" });
    if (bpDia) items.push({ type: "BLOOD_PRESSURE_DIA", value: parseFloat(bpDia), unit: "mmHg" });
    if (pulse) items.push({ type: "HEART_RATE", value: parseFloat(pulse), unit: "bpm" });
    if (temp) items.push({ type: "BODY_TEMPERATURE", value: parseFloat(temp), unit: "celsius" });
    if (respRate) items.push({ type: "RESPIRATORY_RATE", value: parseFloat(respRate), unit: "breaths/min" });
    if (o2Sat) items.push({ type: "OXYGEN_SATURATION", value: parseFloat(o2Sat), unit: "%" });
    if (weightKg) items.push({ type: "WEIGHT", value: parseFloat(weightKg), unit: "kg" });
    if (heightCm) items.push({ type: "HEIGHT", value: parseFloat(heightCm), unit: "cm" });

    if (items.length === 0) return;

    try {
      const recorded = await recordVisitObservations(id, items);
      setVisit((prev) => (prev ? { ...prev, observations: [...prev.observations, ...recorded] } : null));
      // Clear inputs
      setBpSys("");
      setBpDia("");
      setPulse("");
      setTemp("");
      setRespRate("");
      setO2Sat("");
      setWeightKg("");
      setHeightCm("");
      setSuccessBanner("Vitals recorded successfully.");
    } catch (err: any) {
      alert(err?.message || "Failed to record vitals.");
    }
  }

  async function handleAddPrescription(e: React.FormEvent) {
    e.preventDefault();
    if (!id || isLocked || !medName.trim() || !dosage.trim()) return;

    try {
      const issued = await issueVisitPrescriptions(id, [
        {
          medication_name: medName.trim(),
          dosage: dosage.trim(),
          frequency: frequency.trim(),
          duration: duration.trim(),
          instructions: instructions.trim() || undefined,
        },
      ]);

      setVisit((prev) => (prev ? { ...prev, prescriptions: [...prev.prescriptions, ...issued] } : null));
      setMedName("");
      setDosage("");
      setInstructions("");
      setSuccessBanner("Medication prescription added.");
    } catch (err: any) {
      alert(err?.message || "Failed to add prescription.");
    }
  }

  if (isLoading) {
    return <LoadingState message="Opening consultation desk…" />;
  }

  if (error || !visit) {
    return <ErrorState message={error || "Encounter not found."} onRetry={() => id && loadEncounter(id)} />;
  }

  return (
    <div className="encounter-workspace">
      {/* Header */}
      <div className="encounter-workspace__header">
        <div className="encounter-workspace__patient-info">
          <h1>Clinical Consultation Encounter</h1>
          <div className="encounter-workspace__patient-meta">
            <span>
              Patient:{" "}
              <Link to={`/patients/${visit.patient_id}`} style={{ fontWeight: "var(--font-weight-bold)", color: "var(--color-brand-600)" }}>
                {patient?.full_name}
              </Link>
            </span>
            <span>·</span>
            <span>Date: {new Date(visit.visit_date).toLocaleDateString()}</span>
            <span>·</span>
            <Badge variant={isLocked ? "success" : "warning"}>
              {isLocked ? "Signed & Locked" : "Draft (In Progress)"}
            </Badge>
          </div>
        </div>

        <div className="encounter-workspace__actions">
          {!isLocked ? (
            <>
              <Button variant="secondary" onClick={handleSaveDraft} isLoading={isSaving}>
                Save Draft
              </Button>
              <Button variant="primary" onClick={handleSignEncounter} isLoading={isSigning}>
                Sign & Finalize Consultation
              </Button>
            </>
          ) : (
            <Button variant="secondary" onClick={() => window.print()}>
              Print Encounter Record
            </Button>
          )}
        </div>
      </div>

      {successBanner && (
        <div
          style={{
            padding: "var(--spacing-3)",
            background: "var(--color-surface-selected)",
            color: "var(--color-brand-700)",
            borderRadius: "var(--radius-md)",
            fontSize: "var(--font-size-sm)",
          }}
        >
          {successBanner}
        </div>
      )}

      {isLocked && (
        <div className="encounter-workspace__locked-banner">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
          <span>
            This clinical encounter was finalized and signed on {visit.signed_at ? new Date(visit.signed_at).toLocaleString() : ""}. Notes are locked from modification per clinical compliance invariants.
          </span>
        </div>
      )}

      {/* Chief Complaint */}
      <div style={{ background: "var(--color-surface-raised)", padding: "var(--spacing-5)", borderRadius: "var(--radius-lg)", border: "1px solid var(--color-border-subtle)" }}>
        <Input
          label="Chief Complaint *"
          value={chiefComplaint}
          onChange={(e) => setChiefComplaint(e.target.value)}
          disabled={isLocked}
          placeholder="e.g. Patient reports acute chest tightness and shortness of breath for 2 days"
          required
        />
      </div>

      {/* Vitals & Observations Strip */}
      <div className="encounter-workspace__vitals-card">
        <h2 style={{ fontSize: "var(--font-size-base)", fontWeight: "var(--font-weight-semibold)", color: "var(--color-text-primary)" }}>
          Vital Signs & Clinical Observations
        </h2>

        {/* Recorded Vitals List */}
        {visit.observations.length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--spacing-3)", marginBottom: "var(--spacing-3)" }}>
            {visit.observations.map((obs) => (
              <div
                key={obs.id}
                style={{
                  padding: "var(--spacing-2) var(--spacing-3)",
                  background: obs.is_abnormal ? "var(--color-status-error-subtle, #fee2e2)" : "var(--color-surface-sunken)",
                  border: `1px solid ${obs.is_abnormal ? "var(--color-status-error, #b91c1c)" : "var(--color-border-subtle)"}`,
                  borderRadius: "var(--radius-md)",
                  display: "flex",
                  alignItems: "center",
                  gap: "var(--spacing-2)",
                }}
              >
                <span style={{ fontSize: "var(--font-size-xs)", color: "var(--color-text-secondary)" }}>
                  {obs.type.replace(/_/g, " ")}:
                </span>
                <span style={{ fontSize: "var(--font-size-sm)", fontWeight: "var(--font-weight-bold)" }}>
                  {obs.value} {obs.unit}
                </span>
                {obs.is_abnormal && <Badge variant="error">Abnormal</Badge>}
              </div>
            ))}
          </div>
        )}

        {/* Vitals Entry Form */}
        {!isLocked && (
          <form onSubmit={handleRecordVitals} style={{ display: "flex", flexDirection: "column", gap: "var(--spacing-3)" }}>
            <div className="encounter-workspace__vitals-grid">
              <Input label="BP Systolic" type="number" placeholder="120" value={bpSys} onChange={(e) => setBpSys(e.target.value)} />
              <Input label="BP Diastolic" type="number" placeholder="80" value={bpDia} onChange={(e) => setBpDia(e.target.value)} />
              <Input label="Heart Rate (bpm)" type="number" placeholder="72" value={pulse} onChange={(e) => setPulse(e.target.value)} />
              <Input label="Temp (°C)" type="number" step="0.1" placeholder="37.0" value={temp} onChange={(e) => setTemp(e.target.value)} />
              <Input label="Resp Rate" type="number" placeholder="16" value={respRate} onChange={(e) => setRespRate(e.target.value)} />
              <Input label="O2 Sat (%)" type="number" placeholder="98" value={o2Sat} onChange={(e) => setO2Sat(e.target.value)} />
              <Input label="Weight (kg)" type="number" step="0.5" placeholder="70" value={weightKg} onChange={(e) => setWeightKg(e.target.value)} />
              <Input label="Height (cm)" type="number" placeholder="175" value={heightCm} onChange={(e) => setHeightCm(e.target.value)} />
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <Button variant="secondary" size="sm" type="submit">
                + Log Vitals
              </Button>
            </div>
          </form>
        )}
      </div>

      {/* Structured SOAP Notes */}
      <div className="encounter-workspace__soap-grid">
        {/* Subjective */}
        <div className="encounter-workspace__soap-box">
          <div className="encounter-workspace__soap-title">
            <span className="encounter-workspace__soap-badge">S</span>
            <span>Subjective (Patient Narrative & HPI)</span>
          </div>
          <textarea
            className="encounter-workspace__textarea"
            placeholder="Document patient reported symptoms, history of present illness, symptom onset, pain scale…"
            value={subjective}
            onChange={(e) => setSubjective(e.target.value)}
            disabled={isLocked}
          />
        </div>

        {/* Objective */}
        <div className="encounter-workspace__soap-box">
          <div className="encounter-workspace__soap-title">
            <span className="encounter-workspace__soap-badge">O</span>
            <span>Objective (Physical Exam & Findings)</span>
          </div>
          <textarea
            className="encounter-workspace__textarea"
            placeholder="Document physical examination observations, auscultation, palpation, neurological exam…"
            value={objective}
            onChange={(e) => setObjective(e.target.value)}
            disabled={isLocked}
          />
        </div>

        {/* Assessment */}
        <div className="encounter-workspace__soap-box">
          <div className="encounter-workspace__soap-title">
            <span className="encounter-workspace__soap-badge">A</span>
            <span>Assessment (Clinical Diagnoses & ICD-10)</span>
          </div>
          <textarea
            className="encounter-workspace__textarea"
            placeholder="Working diagnosis, differential diagnoses, clinical status (stable, deteriorating, resolved)…"
            value={assessment}
            onChange={(e) => setAssessment(e.target.value)}
            disabled={isLocked}
          />
        </div>

        {/* Plan */}
        <div className="encounter-workspace__soap-box">
          <div className="encounter-workspace__soap-title">
            <span className="encounter-workspace__soap-badge">P</span>
            <span>Plan (Therapy, Orders & Follow-Up)</span>
          </div>
          <textarea
            className="encounter-workspace__textarea"
            placeholder="Prescribed therapies, lab/imaging orders, patient education, follow-up timeline…"
            value={plan}
            onChange={(e) => setPlan(e.target.value)}
            disabled={isLocked}
          />
        </div>
      </div>

      {/* Prescriptions Panel */}
      <div className="encounter-workspace__rx-card">
        <h2 style={{ fontSize: "var(--font-size-base)", fontWeight: "var(--font-weight-semibold)", color: "var(--color-text-primary)" }}>
          Prescribed Medications & Pharmacotherapy
        </h2>

        {visit.prescriptions.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--spacing-2)" }}>
            {visit.prescriptions.map((rx) => (
              <div
                key={rx.id}
                style={{
                  padding: "var(--spacing-3)",
                  background: "var(--color-surface-sunken)",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid var(--color-border-subtle)",
                }}
              >
                <div style={{ fontWeight: "var(--font-weight-bold)", fontSize: "var(--font-size-sm)" }}>
                  {rx.medication_name} — {rx.dosage} ({rx.route})
                </div>
                <div style={{ fontSize: "var(--font-size-xs)", color: "var(--color-text-secondary)" }}>
                  {rx.frequency} for {rx.duration}
                </div>
                {rx.instructions && (
                  <div style={{ fontSize: "var(--font-size-xs)", color: "var(--color-text-muted)", marginTop: "2px" }}>
                    Directions: {rx.instructions}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {!isLocked && (
          <form onSubmit={handleAddPrescription} className="encounter-workspace__rx-form">
            <Input label="Medication *" placeholder="e.g. Amoxicillin" value={medName} onChange={(e) => setMedName(e.target.value)} required />
            <Input label="Dosage *" placeholder="e.g. 500 mg" value={dosage} onChange={(e) => setDosage(e.target.value)} required />
            <Input label="Frequency *" placeholder="e.g. Every 8 hours" value={frequency} onChange={(e) => setFrequency(e.target.value)} required />
            <Input label="Duration *" placeholder="e.g. 7 days" value={duration} onChange={(e) => setDuration(e.target.value)} required />
            <Button variant="primary" size="md" type="submit">
              + Add Rx
            </Button>
          </form>
        )}
      </div>
    </div>
  );
}
