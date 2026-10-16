/**
 * api/clinical.ts
 *
 * Typed API functions for clinical endpoints (patients, encounters, vitals, prescriptions).
 * Uses central ENDPOINTS registry.
 */

import { apiClient } from "./client";
import { ENDPOINTS } from "./endpoints";
import type { PaginatedResponse } from "@/types/api";
import type {
  Allergy,
  Observation,
  ObservationCreatePayload,
  Patient,
  PatientCreatePayload,
  PatientListItem,
  Prescription,
  PrescriptionCreatePayload,
  Visit,
  VisitCreatePayload,
  VisitListItem,
  VisitUpdatePayload,
} from "@/types/clinical";

export async function fetchPatients(params?: {
  q?: string;
  page?: number;
  pageSize?: number;
}): Promise<PaginatedResponse<PatientListItem>> {
  const response = await apiClient.get<PaginatedResponse<PatientListItem>>(
    ENDPOINTS.patients.list,
    {
      params: {
        q: params?.q,
        page: params?.page ?? 1,
        page_size: params?.pageSize ?? 20,
      },
    }
  );
  return response.data;
}

export async function createPatient(data: PatientCreatePayload): Promise<Patient> {
  const response = await apiClient.post<Patient>(ENDPOINTS.patients.create, data);
  return response.data;
}

export async function fetchPatientDetail(id: string): Promise<Patient> {
  const response = await apiClient.get<Patient>(ENDPOINTS.patients.detail(id));
  return response.data;
}

export async function recordAllergy(
  patientId: string,
  data: { allergen: string; severity: string; reaction?: string }
): Promise<Allergy> {
  const response = await apiClient.post<Allergy>(
    ENDPOINTS.patients.allergies(patientId),
    data
  );
  return response.data;
}

export async function fetchPatientVisits(
  patientId: string,
  page = 1,
  pageSize = 20
): Promise<PaginatedResponse<VisitListItem>> {
  const response = await apiClient.get<PaginatedResponse<VisitListItem>>(
    ENDPOINTS.patients.visits(patientId),
    { params: { page, page_size: pageSize } }
  );
  return response.data;
}

export async function fetchPatientObservations(
  patientId: string,
  limit = 50
): Promise<Observation[]> {
  const response = await apiClient.get<Observation[]>(
    ENDPOINTS.patients.observations(patientId),
    { params: { limit } }
  );
  return response.data;
}

export async function fetchPatientPrescriptions(
  patientId: string,
  activeOnly = false
): Promise<Prescription[]> {
  const response = await apiClient.get<Prescription[]>(
    ENDPOINTS.patients.prescriptions(patientId),
    { params: { active_only: activeOnly } }
  );
  return response.data;
}

export async function startEncounter(data: VisitCreatePayload): Promise<Visit> {
  const response = await apiClient.post<Visit>(ENDPOINTS.visits.create, data);
  return response.data;
}

export async function fetchEncounter(visitId: string): Promise<Visit> {
  const response = await apiClient.get<Visit>(ENDPOINTS.visits.detail(visitId));
  return response.data;
}

export async function updateEncounterDraft(
  visitId: string,
  data: VisitUpdatePayload
): Promise<Visit> {
  const response = await apiClient.put<Visit>(ENDPOINTS.visits.update(visitId), data);
  return response.data;
}

export async function signEncounter(visitId: string): Promise<Visit> {
  const response = await apiClient.post<Visit>(ENDPOINTS.visits.sign(visitId));
  return response.data;
}

export async function recordVisitObservations(
  visitId: string,
  items: ObservationCreatePayload[]
): Promise<Observation[]> {
  const response = await apiClient.post<Observation[]>(
    ENDPOINTS.visits.observations(visitId),
    items
  );
  return response.data;
}

export async function issueVisitPrescriptions(
  visitId: string,
  items: PrescriptionCreatePayload[]
): Promise<Prescription[]> {
  const response = await apiClient.post<Prescription[]>(
    ENDPOINTS.visits.prescriptions(visitId),
    items
  );
  return response.data;
}
