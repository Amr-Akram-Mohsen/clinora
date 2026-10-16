/**
 * features/patients/RegisterPatientModal.tsx
 *
 * Accessible modal dialog to register a new patient into the clinic organization.
 */

import { useState } from "react";
import { Modal } from "@/components/Modal/Modal";
import { Input } from "@/components/Input/Input";
import { Button } from "@/components/Button/Button";
import { createPatient } from "@/api/clinical";
import type { PatientCreatePayload } from "@/types/clinical";

interface RegisterPatientModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function RegisterPatientModal({
  isOpen,
  onClose,
  onSuccess,
}: RegisterPatientModalProps) {
  const [fullName, setFullName] = useState("");
  const [dob, setDob] = useState("");
  const [gender, setGender] = useState("MALE");
  const [phone, setPhone] = useState("");
  const [nationalId, setNationalId] = useState("");
  const [bloodType, setBloodType] = useState("");
  const [email, setEmail] = useState("");
  const [address, setAddress] = useState("");
  const [emergencyName, setEmergencyName] = useState("");
  const [emergencyPhone, setEmergencyPhone] = useState("");

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!fullName.trim() || !dob || !phone.trim()) {
      setError("Please fill in all required fields (Name, Date of Birth, Phone).");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const payload: PatientCreatePayload = {
        full_name: fullName.trim(),
        date_of_birth: dob,
        gender,
        phone: phone.trim(),
        national_id: nationalId.trim() || undefined,
        blood_type: bloodType || undefined,
        email: email.trim() || undefined,
        address: address.trim() || undefined,
        emergency_contact_name: emergencyName.trim() || undefined,
        emergency_contact_phone: emergencyPhone.trim() || undefined,
      };

      await createPatient(payload);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err?.message || "Failed to register patient.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Register New Patient"
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
          label="Full Legal Name *"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          placeholder="e.g. Jane Doe"
          required
        />

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--spacing-4)" }}>
          <Input
            label="Date of Birth *"
            type="date"
            value={dob}
            onChange={(e) => setDob(e.target.value)}
            required
          />

          <div style={{ display: "flex", flexDirection: "column", gap: "var(--spacing-1)" }}>
            <label style={{ fontSize: "var(--font-size-sm)", fontWeight: "var(--font-weight-medium)", color: "var(--color-text-secondary)" }}>
              Biological Sex *
            </label>
            <select
              value={gender}
              onChange={(e) => setGender(e.target.value)}
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
              <option value="MALE">Male</option>
              <option value="FEMALE">Female</option>
              <option value="OTHER">Other</option>
            </select>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--spacing-4)" }}>
          <Input
            label="Phone Number *"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+1 555-0100"
            required
          />

          <Input
            label="National ID / SSN"
            value={nationalId}
            onChange={(e) => setNationalId(e.target.value)}
            placeholder="ID number"
          />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--spacing-4)" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--spacing-1)" }}>
            <label style={{ fontSize: "var(--font-size-sm)", fontWeight: "var(--font-weight-medium)", color: "var(--color-text-secondary)" }}>
              Blood Type
            </label>
            <select
              value={bloodType}
              onChange={(e) => setBloodType(e.target.value)}
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
              <option value="">Unknown</option>
              <option value="A+">A+</option>
              <option value="A-">A-</option>
              <option value="B+">B+</option>
              <option value="B-">B-</option>
              <option value="AB+">AB+</option>
              <option value="AB-">AB-</option>
              <option value="O+">O+</option>
              <option value="O-">O-</option>
            </select>
          </div>

          <Input
            label="Email Address"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="patient@example.com"
          />
        </div>

        <Input
          label="Residential Address"
          value={address}
          onChange={(e) => setAddress(e.target.value)}
          placeholder="Street address, city"
        />

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--spacing-4)" }}>
          <Input
            label="Emergency Contact Name"
            value={emergencyName}
            onChange={(e) => setEmergencyName(e.target.value)}
            placeholder="e.g. John Doe (Spouse)"
          />
          <Input
            label="Emergency Contact Phone"
            value={emergencyPhone}
            onChange={(e) => setEmergencyPhone(e.target.value)}
            placeholder="+1 555-0199"
          />
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: "var(--spacing-3)", marginTop: "var(--spacing-4)" }}>
          <Button variant="secondary" type="button" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button variant="primary" type="submit" isLoading={isLoading}>
            Register Patient
          </Button>
        </div>
      </form>
    </Modal>
  );
}
