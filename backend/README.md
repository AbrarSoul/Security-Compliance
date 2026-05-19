# Security Compliance API (Backend)

FastAPI backend with PostgreSQL, JWT authentication, and modular service architecture.

## Prerequisites

- Python 3.12+
- Docker & Docker Compose (for PostgreSQL)

## Quick start

```bash
# From repository root — start PostgreSQL
docker compose up -d postgres

# Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # if .env does not exist

# Run migrations
alembic upgrade head

# Start API (must use the project venv — conda/base Python won't have dependencies)
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or without activating:
# ./run.sh
```

**If you see `ModuleNotFoundError: No module named 'fastapi'`**, you are not using `.venv`. Either run `source .venv/bin/activate` first or use `./run.sh`.

API docs: http://localhost:8000/docs  
Health: http://localhost:8000/health

## Authentication module

Located in `app/auth/`:

| File | Purpose |
|------|---------|
| `router.py` | Signup, login, refresh, logout, `/me` |
| `service.py` | Auth business logic |
| `security.py` | bcrypt hashing + JWT create/decode |
| `dependencies.py` | `get_current_user`, `get_current_active_user` |
| `schemas.py` | Request/response models |

Protected route example: `GET /api/v1/protected/profile` (requires Bearer token).

## Auth endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/signup` | No | Register (password: 8+ chars, upper, lower, digit) |
| POST | `/api/v1/auth/login` | No | Login |
| POST | `/api/v1/auth/refresh` | No | Refresh tokens |
| POST | `/api/v1/auth/logout` | Bearer | Revoke refresh token |
| GET | `/api/v1/auth/me` | Bearer | Current user |
| GET | `/api/v1/protected/profile` | Bearer | Protected profile example |
| GET | `/api/v1/protected/status` | Bearer | Protected status example |

## Project structure

```
app/
├── main.py              # FastAPI application
├── core/                # Config, security, dependencies
├── db/                  # SQLAlchemy engine & session
├── models/              # ORM models
├── schemas/             # Pydantic DTOs
├── api/v1/              # HTTP routes
└── services/            # Business logic
```

## Environment variables

See `.env.example` for all settings. `JWT_SECRET_KEY` is required.

## File upload endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/files/upload` | Bearer | Upload CSV, JSON, or TXT (multipart) |
| GET | `/api/v1/files` | Bearer | List your files |
| GET | `/api/v1/files/{file_id}` | Bearer | File + metadata |
| DELETE | `/api/v1/files/{file_id}` | Bearer | Delete file |

Files are stored locally under `STORAGE_LOCAL_PATH` (default `./uploads`). Metadata (schema, row/column counts, preview) is extracted on upload.

## Compliance scan endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/scans` | Bearer | Run scan on `{ "file_id": "..." }` |
| GET | `/api/v1/scans` | Bearer | List scans |
| GET | `/api/v1/scans/{scan_id}` | Bearer | Scan results + findings |

Detects: **emails**, **phone numbers**, **passwords**, **API keys**, **names**, and **sensitive fields** (column-name heuristics). Returns risk score, compliance status, and data classification.

## Compliance scoring

Configurable via environment variables. Status bands:

| Risk score | Status |
|------------|--------|
| 0 – `SCORE_COMPLIANT_MAX` (default 30) | `compliant` |
| `SCORE_COMPLIANT_MAX` + 1 – `SCORE_RISKY_MAX` (default 60) | `risky` |
| Above `SCORE_RISKY_MAX` | `non_compliant` |

Critical findings can force `non_compliant` when `SCORE_FORCE_NON_COMPLIANT_ON_CRITICAL=true`.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/scoring/config` | View active weights and thresholds |

Scan detail responses include a `compliance_score` object with per-finding point breakdown.

## Recommendations

Generated automatically after each scan based on findings and compliance status.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/scans/{scan_id}/recommendations` | List recommendations for a scan |

Action types: `anonymize`, `mask`, `remove_column`, `rotate_secret`, `encrypt`, `restrict_access`, `review_policy`, `audit_logging`.

## Compliance reports

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/reports` | Generate JSON + PDF for `{ "scan_id": "..." }` |
| GET | `/api/v1/reports` | List reports |
| GET | `/api/v1/reports/{report_id}` | Report metadata + summary |
| GET | `/api/v1/reports/{report_id}/export?format=json` | Download JSON |
| GET | `/api/v1/reports/{report_id}/export?format=pdf` | Download PDF (ReportLab) |

## Sprint 3 — Real-time monitoring

Sprint 3 adds prompt/output monitoring, compliance guard, notifications, analytics, gap analysis, and threat detection.

See **[docs/SPRINT3_TECHNICAL.md](docs/SPRINT3_TECHNICAL.md)** for architecture, APIs, configuration, and test commands.

```bash
# Requires migrations 017–025
alembic upgrade head

# Sprint 3 integration + E2E
pytest -m sprint3 tests/test_sprint3_integration.py -v
pytest -m sprint3_e2e tests/test_sprint3_e2e_workflow.py -v
```

## Tests

```bash
pytest
```
