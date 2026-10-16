# Clinora — Local Development Setup Guide

This guide describes how to run and test Clinora locally from a fresh environment.

---

## Prerequisites

- **Python**: 3.12+ (tested with 3.12.4)
- **Node.js**: 20+ (tested with v20.18.0 LTS) and npm 10+
- **PostgreSQL**: 16+ (running locally on port 5432 or via Docker)

---

## 1. Environment Configuration

Copy `.env.example` to `.env` in the root workspace and backend directories:

```bash
cp .env.example .env
cp .env.example backend/.env
```

### Essential `.env` Settings

```env
# Application
APP_ENV=development
SECRET_KEY=dev-secret-key-CHANGE-ME-in-production-must-be-at-least-32-chars
DEBUG=true

# Database (PostgreSQL + AsyncPG)
DATABASE_URL=postgresql+asyncpg://clinora:clinora@localhost:5432/clinora
DATABASE_ECHO=false

# JWT Configuration
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# CORS
ALLOWED_ORIGINS=http://localhost:5173

# Storage
STORAGE_BACKEND=local
STORAGE_LOCAL_ROOT=./storage/uploads

# Default Seed Administrator
SEED_ADMIN_EMAIL=admin@clinora.com
SEED_ADMIN_PASSWORD=ChangeMe123!
SEED_ORG_NAME=Clinora Clinic
SEED_ORG_SLUG=clinora
```

---

## 2. Database Setup & Migration

Ensure PostgreSQL is running on `localhost:5432` with user `clinora` (password `clinora`) and database `clinora`.

### Running Migrations
From the `backend` directory:

```bash
cd backend
.\.venv\Scripts\activate          # On Linux/macOS: source .venv/bin/activate
alembic upgrade head
```

### Seeding Admin User
Create the initial clinic organization and administrator account (`admin@clinora.com` / `ChangeMe123!`):

```bash
python scripts/seed.py
```

---

## 3. Running the Backend (FastAPI)

From the `backend` directory:

```bash
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

- Backend API: `http://127.0.0.1:8000`
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

---

## 4. Running the Frontend (React + Vite)

From the `frontend` directory:

```bash
cd frontend
npm install
npm run dev
```

- Frontend Web App: `http://localhost:5173`

---

## 5. Running Automated Tests

### Backend Test Suite (Pytest + AsyncIO + Coverage)
```bash
cd backend
pytest -v tests
```

### Frontend Test Suite (Vitest)
```bash
cd frontend
npm run test
```

---

## 6. Default Development Credentials

| Role | Email | Password | Organization |
|---|---|---|---|
| Platform Admin | `admin@clinora.com` | `ChangeMe123!` | `Clinora Clinic` (`clinora`) |
