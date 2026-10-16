# Clinora — Phase 2: Clinical Core Implementation Plan

**Branch Name:** `phase-2/clinical-core`  
**Target Milestone:** Clinical Management Baseline (Patients, Encounters/SOAP, Observations/Vitals, Prescriptions)  
**Parent Document:** [`docs/system_specification.md`](./system_specification.md)  
**Status:** Ready for Execution  

---

## 1. Branch Strategy & Git Commands

### 1.1 Branch Creation & Setup
Before beginning implementation, checkout the dedicated Phase 2 feature branch:

```powershell
# 1. Ensure you are on clean main
git checkout main

# 2. Create and switch to the phase 2 feature branch
git checkout -b phase-2/clinical-core
```

### 1.2 Atomic Commit & Push Schedule

Follow Conventional Commits for each atomic milestone:

| Milestone / Step | Suggested Commit Command |
| :--- | :--- |
| **Step 1: DB Schema & Models** | `git commit -m "feat(db): add patient, visit, observation, and prescription models with migration"` |
| **Step 2: Repositories & Domain** | `git commit -m "feat(domain): implement clinical repositories and physiological range validators"` |
| **Step 3: Application Services** | `git commit -m "feat(service): implement patient, encounter, and prescription workflow services"` |
| **Step 4: API Routers & Schemas** | `git commit -m "feat(api): add patient and clinical encounter REST endpoints with org-scoped RBAC"` |
| **Step 5: Frontend API & App Shell** | `git commit -m "feat(ui): implement responsive clinical app shell, sidebar navigation, and clinical api client"` |
| **Step 6: Patient Directory & Chart** | `git commit -m "feat(ui): add patient directory, registration modal, and longitudinal record timeline"` |
| **Step 7: SOAP Consultation Desk** | `git commit -m "feat(ui): implement structured SOAP encounter documentation, vitals entry, and prescribing"` |
| **Step 8: Tests & Verification** | `git commit -m "test(clinical): add test suites for patient workflows, encounter signing, and api endpoints"` |

**Pushing the branch to GitHub:**
```powershell
git push -u origin phase-2/clinical-core
```

---

## 2. Architectural Invariants & Constraints Checklist

Every piece of code written in Phase 2 must strictly satisfy these rules:

1. **Multi-Tenancy Guard (Zero Data-Leak)**:
   - Every single SQL query for `patients`, `visits`, `observations`, and `prescriptions` must explicitly include `WHERE organization_id = :current_user_org_id`.
   - Never accept `organization_id` from the HTTP request body or query params; always derive it securely from the authenticated token via `current_user.organization_id`.
2. **Clean Layering & DTO Purity**:
   - `api/routers/` handles HTTP serialization and delegates immediately to application services.
   - Route handlers return Pydantic schemas (`PatientRead`, `VisitRead`, etc.). Raw SQLAlchemy ORM models are never returned to the presentation layer.
3. **Audit Non-Repudiation**:
   - Any patient creation, encounter sign-off, or prescription generation must write an `AuditLog` entry detailing `actor_id`, `actor_email`, `action`, `resource_id`, and `request_id`.
4. **Encounter State Machine & Immutability**:
   - A clinical encounter starts in `IN_PROGRESS`.
   - Once a physician marks an encounter as `SIGNED`, it becomes **immutable**. Any subsequent corrections must be appended as signed addenda.
5. **DRY & Cross-Platform UI Consistency**:
   - No hardcoded hex values or inline styles. Use CSS custom properties from [tokens.css](file:///c:/Users/ammar/Desktop/my_github/clinora/frontend/src/styles/tokens.css).
   - Ensure full Light & Dark mode support via `[data-theme]`.
   - Reuse existing primitives: `Button`, `Input`, `Modal`, `Badge`, `States`.
   - Centralize all API URL paths in [api/endpoints.ts](file:///c:/Users/ammar/Desktop/my_github/clinora/frontend/src/api/endpoints.ts).

---

## 3. Step-by-Step Implementation Tasks

### Step 1: Database Infrastructure & Models
Create the core clinical entities in `backend/infrastructure/database/models/`:
- [ ] `patient.py`:
  - `Patient`: `id` (UUID), `organization_id` (FK), `national_id`, `full_name`, `date_of_birth`, `gender`, `blood_type`, `phone`, `email`, `address`, `emergency_contact_name`, `emergency_contact_phone`, `is_active`, `created_at`, `updated_at`.
  - `Allergy`: `id` (UUID), `organization_id` (FK), `patient_id` (FK), `allergen`, `severity` (`MILD`, `MODERATE`, `SEVERE`, `LIFE_THREATENING`), `reaction`, `recorded_at`.
- [ ] `clinical.py`:
  - `Visit`: `id` (UUID), `organization_id` (FK), `patient_id` (FK), `doctor_id` (FK), `appointment_id` (FK, nullable), `visit_date`, `status` (`IN_PROGRESS`, `COMPLETED`, `SIGNED`), `chief_complaint`, `subjective_notes`, `objective_notes`, `assessment_notes`, `plan_notes`, `signed_at`.
  - `Observation`: `id` (UUID), `organization_id` (FK), `patient_id` (FK), `visit_id` (FK, nullable), `recorded_by_id` (FK), `type` (BP, Heart Rate, Temperature, BMI, etc.), `value`, `unit`, `is_abnormal`, `recorded_at`.
  - `Prescription`: `id` (UUID), `organization_id` (FK), `patient_id` (FK), `visit_id` (FK), `doctor_id` (FK), `medication_name`, `dosage`, `route`, `frequency`, `duration`, `instructions`, `is_active`, `issued_at`.
- [ ] Update `backend/infrastructure/database/models/__init__.py` to export all clinical models.
- [ ] Generate Alembic Migration:
  ```powershell
  cd backend
  alembic revision --autogenerate -m "add_clinical_core_tables"
  alembic upgrade head
  ```

---

### Step 2: Repositories & Domain Validation
- [ ] `backend/domain/clinical/ranges.py`:
  - Define physiological reference boundaries for standard vitals (Systolic BP: 90–120 mmHg, Heart Rate: 60–100 bpm, Temperature: 36.5–37.5 °C, etc.) to automatically calculate `is_abnormal`.
- [ ] `backend/infrastructure/repositories/patient_repository.py`:
  - `create_patient`, `get_by_id_scoped`, `search_patients` (search query against name, phone, national ID), `list_patients_paginated`, `add_allergy`, `get_allergies`.
- [ ] `backend/infrastructure/repositories/clinical_repository.py`:
  - `create_visit`, `get_visit_by_id_scoped`, `list_patient_visits`, `sign_visit`.
  - `record_observations`, `get_patient_observations_by_type`.
  - `create_prescriptions`, `list_active_prescriptions_for_patient`.

---

### Step 3: Application Services (Workflow Orchestration)
- [ ] `backend/application/clinical/patient_service.py`:
  - Handles patient registration, validation of demographics, updating contacts, and writing `patient.created` audit log.
- [ ] `backend/application/clinical/encounter_service.py`:
  - `start_encounter`: Initializes `Visit` linked to doctor and patient.
  - `record_vitals`: Ingests numerical vitals, runs abnormal range checks, and persists observations.
  - `finalize_and_sign_encounter`: Locks the SOAP notes, records `signed_at`, and writes `visit.signed` audit log.
- [ ] `backend/application/clinical/prescription_service.py`:
  - `issue_prescription`: Verifies patient allergy conflicts against prescribed drugs and writes `prescription.issued` audit event.

---

### Step 4: API Presentation Layer
- [ ] Pydantic Schemas:
  - `backend/api/schemas/patient.py`: `PatientCreate`, `PatientUpdate`, `PatientRead`, `AllergyCreate`, `AllergyRead`.
  - `backend/api/schemas/clinical.py`: `VisitCreate`, `VisitUpdate`, `VisitRead`, `ObservationCreate`, `ObservationRead`, `PrescriptionCreate`, `PrescriptionRead`.
- [ ] Routers:
  - `backend/api/routers/patients.py`:
    - `POST /api/v1/patients` — Register patient (`DOCTOR`, `NURSE`, `RECEPTIONIST`)
    - `GET  /api/v1/patients` — Search and list patients with pagination
    - `GET  /api/v1/patients/{id}` — Full patient profile with allergies & recent vitals
    - `POST /api/v1/patients/{id}/allergies` — Add allergy
  - `backend/api/routers/clinical.py`:
    - `POST /api/v1/patients/{id}/visits` — Start new consultation visit
    - `GET  /api/v1/visits/{id}` — Get encounter details and SOAP notes
    - `PUT  /api/v1/visits/{id}` — Update SOAP draft
    - `POST /api/v1/visits/{id}/sign` — Lock and sign consultation (`DOCTOR` only)
    - `POST /api/v1/visits/{id}/observations` — Record vitals
    - `POST /api/v1/visits/{id}/prescriptions` — Issue prescriptions (`DOCTOR` only)
- [ ] Register new routers in `backend/api/main.py`.

---

### Step 5: Frontend API & Types Layer
- [ ] `frontend/src/types/clinical.ts`:
  - TypeScript interfaces for `Patient`, `Allergy`, `Visit`, `Observation`, `Prescription`, and query filter parameters.
- [ ] `frontend/src/api/endpoints.ts`:
  - Add routes: `patients.list`, `patients.create`, `patients.detail`, `visits.create`, `visits.detail`, `visits.sign`, `visits.observations`, `prescriptions.create`.
- [ ] `frontend/src/api/clinical.ts`:
  - Typed Axios functions calling the clinical endpoints.

---

### Step 6: Frontend Clinical App Shell & Navigation
Replace the current placeholder dashboard in `frontend/src/App.tsx`:
- [ ] `frontend/src/components/Layout/AppShell.tsx`:
  - **Sidebar**:
    - Clinic branding header (displays `organization.name`).
    - Navigation items: **Dashboard**, **Patients**, **Encounters**, **Prescriptions**, **Settings**.
    - Active link indicators and clean iconography.
  - **Topbar**:
    - Global patient quick-search input.
    - Active user badge (`Dr. John Doe · Doctor`).
    - Dark / Light mode toggle switch.
    - Sign out action.
  - **Main Content Area**:
    - Breadcrumbs and responsive layout container.

---

### Step 7: Patient Management Views
- [ ] `frontend/src/features/patients/PatientListPage.tsx`:
  - Header with patient count and `+ Register New Patient` primary button.
  - Search bar (by name, phone, national ID).
  - Clean table displaying Name, Age/DOB, Gender, Phone, Blood Type, and Last Visit date.
  - Pagination controls.
- [ ] `frontend/src/features/patients/RegisterPatientModal.tsx`:
  - Modal form utilizing existing `Input`, `Button`, and validation hooks.
  - Fields: Full Name, National ID, DOB, Gender, Phone, Blood Type, Emergency Contact.
- [ ] `frontend/src/features/patients/PatientDetailPage.tsx`:
  - Header: Demographics summary, age, blood type badge, quick action buttons (`Start Visit`, `New Prescription`).
  - Allergies banner (highlighted in alert red/amber).
  - Longitudinal Timeline: List of past visits with diagnosis highlights and dates.
  - Vital Signs History: Recent blood pressure, pulse, temperature cards with abnormal badges.

---

### Step 8: Clinical Consultation & SOAP Encounter Desk
- [ ] `frontend/src/features/encounters/EncounterWorkspace.tsx`:
  - Split-screen layout:
    - **Left Column**: Patient longitudinal context (allergies, previous diagnoses, chronic conditions).
    - **Right Column (Consultation Workspace)**:
      - **Chief Complaint** input.
      - **Vitals Strip**: Quick-entry cards for BP, Heart Rate, Temp, Glucose with instant physiological warning badges if abnormal.
      - **SOAP Tabs / Sections**:
        - `Subjective`: Patient symptoms and history of present illness.
        - `Objective`: Physical examination notes.
        - `Assessment`: Clinical impressions & ICD-10 notes.
        - `Plan`: Management directives & follow-up instructions.
      - **Prescription Builder**: Add medication rows (drug name, dose, frequency, duration, instructions).
      - **Actions**: `Save Draft` or `Sign & Finalize Encounter` button.
- [ ] `frontend/src/features/prescriptions/PrescriptionPrintModal.tsx`:
  - Clean printable prescription slip with clinic name, doctor credentials, patient details, and Rx list.

---

### Step 9: Verification & Automated Testing
- [ ] Backend Tests:
  - `tests/test_patient_service.py`: Verify patient creation, duplicate checks, and org isolation.
  - `tests/test_encounter_service.py`: Verify SOAP recording, vitals abnormal calculation, and signature immutability.
  - `tests/test_clinical_api.py`: Verify endpoints, permissions (`NURSE` cannot sign encounter, `RECEPTIONIST` cannot prescribe), and 401/403 responses.
- [ ] Frontend Tests & Build:
  - Verify TypeScript compilation: `npm run build` / `tsc --noEmit`.
  - Component tests for `PatientListPage` and `EncounterWorkspace`.

---

## 4. Verification Gate for Phase 2 Completion

Phase 2 will be declared complete when:
1. A receptionist can register a new patient via the web UI.
2. A doctor can search for the patient, open their chart, and start a visit encounter.
3. The doctor can record vitals (which flag if out of range), write SOAP notes, add a prescription, and sign the visit.
4. The patient's longitudinal timeline immediately displays the newly signed encounter.
5. All actions have generated associated `AuditLog` records with user, IP, and correlation IDs.
6. The entire flow runs cleanly in both **Light** and **Dark** themes.
