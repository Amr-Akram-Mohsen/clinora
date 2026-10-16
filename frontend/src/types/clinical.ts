/**
 * types/clinical.ts
 *
 * TypeScript types for clinical entities: Patients, Allergies, Encounters (Visits),
 * Observations (Vitals), and Prescriptions.
 */

export interface Allergy {
  id: string;
  allergen: string;
  severity: "MILD" | "MODERATE" | "SEVERE" | "LIFE_THREATENING";
  reaction?: string | null;
  recorded_at: string;
}

export interface PatientListItem {
  id: string;
  full_name: string;
  date_of_birth: string;
  gender: "MALE" | "FEMALE" | "OTHER";
  phone: string;
  national_id?: string | null;
  blood_type?: string | null;
  created_at: string;
}

export interface Patient extends PatientListItem {
  organization_id: string;
  email?: string | null;
  address?: string | null;
  emergency_contact_name?: string | null;
  emergency_contact_phone?: string | null;
  is_active: boolean;
  updated_at: string;
  allergies: Allergy[];
}

export interface PatientCreatePayload {
  full_name: string;
  date_of_birth: string;
  gender: string;
  phone: string;
  national_id?: string;
  blood_type?: string;
  email?: string;
  address?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
}

export interface Observation {
  id: string;
  patient_id: string;
  visit_id?: string | null;
  type: string;
  value: number;
  unit: string;
  is_abnormal: boolean;
  recorded_at: string;
}

export interface ObservationCreatePayload {
  type: string;
  value: number;
  unit: string;
}

export interface Prescription {
  id: string;
  patient_id: string;
  visit_id: string;
  doctor_id: string;
  medication_name: string;
  dosage: string;
  route: string;
  frequency: string;
  duration: string;
  instructions?: string | null;
  is_active: boolean;
  issued_at: string;
}

export interface PrescriptionCreatePayload {
  medication_name: string;
  dosage: string;
  route?: string;
  frequency: string;
  duration: string;
  instructions?: string;
}

export interface VisitListItem {
  id: string;
  patient_id: string;
  doctor_id: string;
  visit_date: string;
  status: "IN_PROGRESS" | "COMPLETED" | "SIGNED";
  chief_complaint: string;
  signed_at?: string | null;
}

export interface Visit extends VisitListItem {
  organization_id: string;
  appointment_id?: string | null;
  subjective_notes?: string | null;
  objective_notes?: string | null;
  assessment_notes?: string | null;
  plan_notes?: string | null;
  created_at: string;
  updated_at: string;
  observations: Observation[];
  prescriptions: Prescription[];
}

export interface VisitCreatePayload {
  patient_id: string;
  chief_complaint: string;
  appointment_id?: string | null;
  subjective_notes?: string | null;
  objective_notes?: string | null;
  assessment_notes?: string | null;
  plan_notes?: string | null;
}

export interface VisitUpdatePayload {
  chief_complaint?: string;
  subjective_notes?: string;
  objective_notes?: string;
  assessment_notes?: string;
  plan_notes?: string;
}
