# Clinora — Revised Implementation Roadmap

---

## Phase 1 — Foundation (Completed Baseline)
- **Purpose**: Core identity, multi-tenancy, authentication, authorization, and audit logging.
- **Domain Entities**: `Organization`, `User`, `Role`, `UserRole`, `RefreshToken`, `AuditLog`.
- **Backend**: FastAPI app, async SQLAlchemy engine, Pydantic settings, correlation middleware, JWT + refresh token rotation, RBAC guards.
- **Frontend**: React + Vite SPA, design tokens (CSS variables), light/dark themes, `LoginPage`, `AuthProvider`, Axios client with refresh interceptor, `ProtectedRoute`.
- **Infrastructure**: PostgreSQL 16 (AsyncPG), Alembic migrations, database seeder.

---

## Phase 2 — Clinical Core (Next Phase)
> See detailed execution plan: [`docs/phase_2_implementation_plan.md`](./phase_2_implementation_plan.md)
- **Purpose**: Longitudinal patient record management, appointments, clinical visits, observations, medications, and prescriptions.
- **Domain Entities**: `Patient`, `Appointment`, `Visit`, `Observation`, `Prescription`, `Treatment`.
- **Backend Changes**:
  - Patient repository & services (CRUD, search, medical history timeline).
  - Visit workflows (SOAP notes, vital signs, clinical encounters).
  - Prescription & medication management (active prescriptions, dosage, frequency).
- **Database Changes**:
  - `patients`, `appointments`, `visits`, `observations`, `prescriptions`, `treatments` tables.
  - Multi-tenant organization scoping and soft-delete/audit trails.
- **Frontend Pages/Components**:
  - Patient Directory & Search.
  - Patient Summary / Longitudinal Timeline view.
  - Visit Recording & Encounter Form.
  - Prescription & Medication Panel.
- **Completion Criteria**: Physician can register patients, record visits, log observations/vitals, and prescribe medications with full organization isolation.

---

## Phase 3 — Administration & Clinic Operations
- **Purpose**: Staff management, role assignments, clinic settings, and operational audit trail review.
- **Domain Entities**: Clinic configuration, staff invites, role permissions.
- **Features**:
  - Staff management panel (invite doctor/nurse/receptionist, deactivate accounts).
  - Clinic metadata & working hours settings.
  - Audit log viewer with search, filtering by actor/action/time.
- **Completion Criteria**: Clinic admin can invite users, assign RBAC roles, and review audit logs from the web UI.

---

## Phase 4 — AI-Assisted Clinical Intelligence
- **Purpose**: AI-powered clinical summarization, visit pre-briefing, and context retrieval (Physician remains sole decision-maker).
- **Safety Boundary**: Non-diagnostic, physician-in-the-loop, explicitly labeled AI outputs.
- **Features**:
  - Patient longitudinal history summarizer.
  - Pre-visit clinical brief generator.
  - Clinical information retrieval assistant.
- **Infrastructure**: Provider abstraction (`Anthropic`, `OpenAI`, `Local/Ollama`), prompt templates, structured output validation.
- **Completion Criteria**: Physician can request an AI summary of past visits and see clear AI-generated tags before signing off.

---

## Phase 5 — Analytics & Longitudinal Trends
- **Purpose**: Patient vitals trend analysis, clinic workload statistics, population health metrics.
- **Features**:
  - Patient vital trend charts (blood pressure, glucose, BMI over time).
  - Clinic visit volume & appointment adherence analytics.
- **Completion Criteria**: Visual chart components and aggregated metrics dashboards for clinicians.

---

## Phase 6 — Research Workspace & Data Export
- **Purpose**: Anonymized cohort querying, research dataset extraction, structured CSV/FHIR exports.
- **Features**:
  - De-identification pipeline for PHI data.
  - Cohort query builder.
  - Export auditing and authorization checks.
- **Completion Criteria**: Authorized researchers/admins can export de-identified clinical datasets.

---

## Phase 7 — Production Hardening & Observability
- **Purpose**: Production deployment readiness, rate limiting, structured telemetry, Prometheus metrics, distributed tracing.
- **Features**:
  - Redis cache & rate limiting integration.
  - Prometheus metrics exporter & Sentry exception tracking.
  - Automated backups, database connection pooling tuning.
  - Comprehensive end-to-end load tests.
- **Completion Criteria**: Zero-downtime deployment scripts, health probes, automated monitoring, and stress-tested throughput.
