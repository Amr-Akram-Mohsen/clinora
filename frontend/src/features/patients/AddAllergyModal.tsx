/**
 * features/patients/AddAllergyModal.tsx
 *
 * Modal to document a verified allergy on the patient chart.
 */

import { useState } from "react";
import { Modal } from "@/components/Modal/Modal";
import { Input } from "@/components/Input/Input";
import { Button } from "@/components/Button/Button";
import { recordAllergy } from "@/api/clinical";

interface AddAllergyModalProps {
  patientId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function AddAllergyModal({
  patientId,
  isOpen,
  onClose,
  onSuccess,
}: AddAllergyModalProps) {
  const [allergen, setAllergen] = useState("");
  const [severity, setSeverity] = useState("MODERATE");
  const [reaction, setReaction] = useState("");

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!allergen.trim()) {
      setError("Please specify the allergen substance or drug.");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      await recordAllergy(patientId, {
        allergen: allergen.trim(),
        severity,
        reaction: reaction.trim() || undefined,
      });
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err?.message || "Failed to record allergy.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Record Patient Allergy"
    >
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "var(--spacing-4)" }}>
        {error && (
          <div
            role="alert"
            style={{
              padding: "var(--spacing-3)",
              background: "var(--color-status-error-subtle, #fee2e2)",
              color: "var(--color-status-error, #b91c1c)",
              borderRadius: "var(--radius-md)",
              fontSize: "var(--font-size-sm)",
            }}
          >
            {error}
          </div>
        )}

        <Input
          label="Allergen Substance or Medication *"
          value={allergen}
          onChange={(e) => setAllergen(e.target.value)}
          placeholder="e.g. Penicillin, Peanuts, Sulfa"
          required
        />

        <div style={{ display: "flex", flexDirection: "column", gap: "var(--spacing-1)" }}>
          <label style={{ fontSize: "var(--font-size-sm)", fontWeight: "var(--font-weight-medium)", color: "var(--color-text-secondary)" }}>
            Severity Level *
          </label>
          <select
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
            style={{
              height: "38px",
              padding: "0 var(--spacing-3)",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--color-border-default)",
              backgroundColor: "var(--color-surface-sunken)",
              color: "var(--color-text-primary)",
              fontSize: "var(--font-size-sm)",
            }}
          >
            <option value="MILD">Mild (Rash, itching)</option>
            <option value="MODERATE">Moderate (Urticaria, gastrointestinal)</option>
            <option value="SEVERE">Severe (Bronchospasm, facial edema)</option>
            <option value="LIFE_THREATENING">Life-Threatening (Anaphylaxis)</option>
          </select>
        </div>

        <Input
          label="Observed Reaction Notes"
          value={reaction}
          onChange={(e) => setReaction(e.target.value)}
          placeholder="e.g. Developed acute hives within 15 minutes of intake"
        />

        <div style={{ display: "flex", justifyContent: "flex-end", gap: "var(--spacing-3)", marginTop: "var(--spacing-4)" }}>
          <Button variant="secondary" type="button" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button variant="danger" type="submit" isLoading={isLoading}>
            Save Allergy Alert
          </Button>
        </div>
      </form>
    </Modal>
  );
}
