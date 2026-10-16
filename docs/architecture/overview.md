# Clinora — Architecture Overview

## Phase 1 Architecture Baseline

```
Browser (React SPA on Vite — http://localhost:5173)
  │
  ├── [HTTP Request via Axios]
  ▼
FastAPI Application (http://127.0.0.1:8000)
  │
  ├── [CorrelationMiddleware] → injects X-Request-ID, captures latency
  │
  ├── [API Routers] (`/api/v1/auth`, `/health`)
  │     ├── `POST /api/v1/auth/login`
  │     ├── `POST /api/v1/auth/refresh`
  │     ├── `POST /api/v1/auth/logout`
  │     └── `GET  /api/v1/auth/me`
  │
  ├── [Dependencies] (`api/deps.py`)
  │     ├── `get_current_user` (Bearer JWT validation)
  │     ├── `require_active_user`
  │     ├── `require_roles` (RBAC)
  │     └── `get_db_session` (SQLAlchemy AsyncSession)
  │
  ├── [Application Layer] (`application/auth/auth_service.py`)
  │     └── `AuthService`: Orchestrates credential validation, token rotation family management, and audit logging
  │
  ├── [Infrastructure Layer]
  │     ├── Repositories: `UserRepository`, `TokenRepository`, `AuditRepository`
  │     ├── ORM Models: `Organization`, `User`, `Role`, `UserRole`, `RefreshToken`, `AuditLog`
  │     └── Database Engine: SQLAlchemy 2.0 Async Engine with `asyncpg`
  ▼
PostgreSQL 16 Database (`localhost:5432/clinora`)
```

---

## Security & Auth Strategy

1. **Short-Lived Access Tokens**:
   - Format: Signed JWT (HS256)
   - Expiration: 15 minutes
   - Payload: Subject (`user.id`), `org_id`, `roles`, `exp`, `iat`

2. **Long-Lived Refresh Tokens**:
   - Transport: HTTP-Only cookie (`clinora_refresh`)
   - Expiration: 30 days
   - Stored in DB: SHA-256 hash
   - Rotation: Rotated on every refresh call.
   - Theft Detection: If an already-rotated token is reused, its entire token family is immediately revoked and audited.

3. **Audit Logging**:
   - Immutability: Write-only `AuditLog` records.
   - Traceability: Correlated via `request_id`, client IP, user agent, actor email snapshot.
