# Clinora

> AI-Assisted Clinical Management, Longitudinal Patient Record & Clinical Insights Platform

## Overview

Clinora is a modular clinical information platform designed for physicians operating private or specialized clinics. It manages patient records, appointments, clinical visits, observations, medications, prescriptions, treatments, documents, and longitudinal patient history. AI capabilities assist with clinical information retrieval and summarization; the physician remains the clinical decision-maker at all times.

## Architecture

```
clinora/
├── backend/        # FastAPI application (Python)
├── frontend/       # React + TypeScript + Vite
├── migrations/     # Alembic database migrations
├── docs/           # Architecture and developer documentation
└── docker-compose.yml
```

See [`docs/architecture/`](docs/architecture/) and the formal [System Requirements & Database Specification](docs/system_specification.md) for detailed engineering specifications.

## Development Setup

### Prerequisites

- Docker & Docker Compose
- Python 3.12+
- Node.js 20+

### Quick start

```bash
# 1. Copy environment file
cp .env.example .env
# Edit .env with your local values

# 2. Start infrastructure
docker-compose up -d

# 3. Backend
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
python scripts/seed.py             # Creates default org + admin user
uvicorn api.main:app --reload

# 4. Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Backend: http://localhost:8000  
Frontend: http://localhost:5173  
API docs: http://localhost:8000/docs

## Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Foundation (auth, users, org, audit) | 🟡 In Progress |
| 2 | Clinical Management (patients, visits, observations) | ⬜ Planned |
| 3 | Admin Panel | ⬜ Planned |
| 4 | AI Subsystem | ⬜ Planned |
| 5 | Analytics Engine | ⬜ Planned |
| 6 | Research Workspace | ⬜ Planned |
| 7 | Hardening & Observability | ⬜ Planned |

## Medical Safety Boundary

This platform assists physicians. It does not diagnose, prescribe, or make autonomous clinical decisions. All AI outputs are clearly labeled as AI-generated and distinct from physician-authored clinical records. The physician remains the decision-maker.
