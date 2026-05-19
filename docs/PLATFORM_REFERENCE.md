# Security Compliance Platform — Architecture & Reference

**Purpose:** Single reference for **Sprint 1 (implemented)** and **Sprint 2 (planned)** — architecture, database, APIs, modules, frontend, operations, and security notes.

**Stack:** FastAPI · async SQLAlchemy + asyncpg · Alembic · PostgreSQL · JWT · Next.js 14 (App Router) · TypeScript · Tailwind CSS

**API base path:** `/api/v1` (configurable via `API_V1_PREFIX`)

---

## Table of contents

1. [Executive summary](#1-executive-summary)
2. [Repository layout](#2-repository-layout)
3. [Sprint 1 — implemented architecture](#3-sprint-1--implemented-architecture)
4. [Sprint 1 — database schema](#4-sprint-1--database-schema)
5. [Sprint 1 — API reference](#5-sprint-1--api-reference)
6. [Sprint 1 — domain flows](#6-sprint-1--domain-flows)
7. [Sprint 1 — configuration & environment](#7-sprint-1--configuration--environment)
8. [Sprint 1 — frontend](#8-sprint-1--frontend)
9. [Sprint 1 — security & operations](#9-sprint-1--security--operations)
10. [Sprint 2 — planned extension (policy-driven execution security)](#10-sprint-2--planned-extension-policy-driven-execution-security)
11. [Sprint 2 — planned database additions](#11-sprint-2--planned-database-additions)
12. [Sprint 2 — planned APIs & modules](#12-sprint-2--planned-apis--modules)
13. [Sprint 2 — execution validation workflow](#13-sprint-2--execution-validation-workflow)
14. [Sprint 2 — RBAC, audit, rule/policy samples](#14-sprint-2--rbac-audit-rulepolicy-samples)
15. [Sprint 3 — scalability hooks (forward-looking)](#15-sprint-3--scalability-hooks-forward-looking)
16. [Appendix — migrations index](#appendix--migrations-index)

---

## 1. Executive summary

| Sprint | Status | Focus |
|--------|--------|--------|
| **Sprint 1** | **Implemented** | Auth, file upload, dataset scanning, scoring, recommendations, JSON/PDF reports, dashboard UI |
| **Sprint 2** | **Planned** | Policy-driven **execution security**: model compliance checks, pre-execution validation, allow/warn/block engine, configurable rules/policies, RBAC (Admin/User/Auditor), audit logging, extended dashboard |

Sprint 2 **extends** Sprint 1 modules; it does **not** replace the existing layout (`models/`, `repositories/`, `services/`, `api/v1/`, `auth/`).

---

## 2. Repository layout

```
Security Comp (Sandbox)/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, CORS, /health, mounts api_router
│   │   ├── api/v1/                 # HTTP routers
│   │   ├── auth/                   # JWT auth router, service, dependencies, security
│   │   ├── core/                   # Settings (pydantic-settings), shared config
│   │   ├── db/                     # Async session, Base
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   ├── repositories/         # Data access
│   │   ├── schemas/                # Pydantic request/response models
│   │   ├── services/               # Business logic (files, scanner, scoring, reports, scan)
│   │   └── storage/                # Local (and future) storage backends
│   ├── alembic/versions/           # Migrations 001–006
│   ├── tests/
│   ├── run.sh                      # Helper: uvicorn with project venv
│   └── .env                        # Local secrets (not committed)
├── frontend/
│   └── src/
│       ├── app/                    # Next.js App Router routes
│       ├── components/             # UI + layout
│       └── lib/                    # api.ts, auth, types
├── docker-compose.yml              # postgres (+ optional minio)
└── docs/
    └── PLATFORM_REFERENCE.md       # This file
```

---

## 3. Sprint 1 — implemented architecture

### 3.1 Layering

| Layer | Responsibility |
|-------|------------------|
| **API (`app/api/v1/`)** | HTTP, query params, dependency injection, maps ORM → response schemas |
| **Auth (`app/auth/`)** | Signup/login/refresh/logout/me; `ActiveUser` dependency |
| **Services** | Orchestration: upload → metadata → scan → score → recommendations → reports |
| **Repositories** | CRUD and queries per aggregate |
| **Models** | Tables and relationships |
| **Storage** | `LocalStorageBackend`: user-scoped paths for uploads and report artifacts |

### 3.2 High-level request flow (scan)

```
Client → POST /scans { file_id }
  → ScanService.create_and_run_scan
    → load file + stream from storage
    → ComplianceScanner (detectors)
    → ComplianceScoringEngine
    → RecommendationEngine
    → persist Scan, ScanFinding, ScanRecommendation
  → ScanDetailResponse
```

### 3.3 Scanner (Sprint 1)

- **Location:** `app/services/scanner/`
- **Detectors (examples):** email, phone, password, API key, sensitive field/name patterns
- **Loader:** CSV / JSON / TXT sampling (`scan_max_sample_rows`, `scan_match_threshold` from settings)

### 3.4 Scoring & recommendations

- **Scoring:** `app/services/scoring/` — weights/thresholds from env (`SCORE_*`), outputs `risk_score`, `compliance_status`, `classification`, `score_breakdown_json` on `scans`
- **Recommendations:** `app/services/recommendations/` — templates tied to findings/status

### 3.5 Reports

- **JSON builder:** `app/services/reports/json_builder.py`
- **PDF:** ReportLab — `app/services/reports/pdf_builder.py`
- **Persistence:** `reports` row + files under local storage keys (`json_storage_key`, `pdf_storage_key`)

### 3.6 Auth

- **Password hashing:** bcrypt (direct), not passlib on Python 3.13
- **Tokens:** access (JWT) + refresh (stored hashed in `refresh_tokens`)

---

## 4. Sprint 1 — database schema

Migrations **001 → 006** (PostgreSQL). Types below reflect implemented columns.

### 4.1 `users`

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID | PK |
| `email` | VARCHAR(255) | UNIQUE, indexed |
| `password_hash` | VARCHAR(255) | |
| `full_name` | VARCHAR(255) | nullable |
| `is_active` | BOOLEAN | default true |
| `created_at`, `updated_at` | TIMESTAMPTZ | |

### 4.2 `refresh_tokens`

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID | PK |
| `user_id` | UUID | FK → users CASCADE |
| `token_hash` | VARCHAR(255) | UNIQUE |
| `expires_at` | TIMESTAMPTZ | |
| `revoked_at` | TIMESTAMPTZ | nullable |
| `created_at` | TIMESTAMPTZ | |

### 4.3 `files`

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID | PK |
| `user_id` | UUID | FK → users |
| `original_name` | VARCHAR(512) | |
| `storage_key` | VARCHAR(1024) | UNIQUE |
| `content_type` | VARCHAR(128) | nullable |
| `file_type` | VARCHAR(32) | csv/json/txt |
| `size_bytes` | BIGINT | |
| `checksum_sha256` | VARCHAR(64) | nullable |
| `status` | VARCHAR(32) | default `uploaded` |
| `created_at` | TIMESTAMPTZ | indexed |

### 4.4 `file_metadata`

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID | PK |
| `file_id` | UUID | FK → files, UNIQUE |
| `row_count`, `column_count` | INTEGER | nullable |
| `schema_json`, `preview_json`, `extra_json` | JSONB | nullable |
| `analyzed_at` | TIMESTAMPTZ | |

### 4.5 `scans`

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID | PK |
| `user_id`, `file_id` | UUID | FKs, indexed |
| `status` | VARCHAR(32) | e.g. pending/completed/failed |
| `risk_score` | SMALLINT | nullable |
| `compliance_status` | VARCHAR(32) | nullable |
| `classification` | VARCHAR(32) | nullable |
| `started_at`, `completed_at` | TIMESTAMPTZ | nullable |
| `error_message` | TEXT | nullable |
| `score_breakdown_json` | JSONB | nullable (migration 004) |
| `created_at` | TIMESTAMPTZ | |

### 4.6 `scan_findings`

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID | PK |
| `scan_id` | UUID | FK → scans CASCADE, indexed |
| `finding_type` | VARCHAR(64) | |
| `severity` | VARCHAR(16) | |
| `column_name` | VARCHAR(255) | nullable |
| `sample_count` | INTEGER | |
| `match_rate` | NUMERIC(5,4) | nullable |
| `evidence_json` | JSONB | nullable |
| `created_at` | TIMESTAMPTZ | |

### 4.7 `scan_recommendations`

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID | PK |
| `scan_id` | UUID | FK → scans |
| `priority` | VARCHAR(16) | |
| `title` | VARCHAR(255) | |
| `description` | TEXT | |
| `action_type` | VARCHAR(64) | |
| `finding_type`, `column_name` | nullable | |
| `metadata_json` | JSONB | nullable |
| `created_at` | TIMESTAMPTZ | |

### 4.8 `reports`

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID | PK |
| `scan_id` | UUID | FK → scans, **UNIQUE** (one report per scan in current design) |
| `user_id` | UUID | FK → users |
| `summary_json` | JSONB | NOT NULL — full report JSON |
| `json_storage_key`, `pdf_storage_key` | VARCHAR(1024) | nullable |
| `created_at` | TIMESTAMPTZ | |

### 4.9 Entity relationships (Sprint 1)

```
users 1──* files 1──1 file_metadata
users 1──* scans *──1 files
scans 1──* scan_findings
scans 1──* scan_recommendations
scans 1──0..1 reports
users 1──* refresh_tokens
users 1──* reports
```

---

## 5. Sprint 1 — API reference

All routes below are under **`/api/v1`** unless you change `API_V1_PREFIX`. Protected routes require **`Authorization: Bearer <access_token>`**.

### 5.1 Health

| Method | Path | Auth |
|--------|------|------|
| GET | `/health` | No (on `app`, not under prefix in `main.py`) |

### 5.2 Authentication (`/auth`)

| Method | Path | Description |
|--------|------|---------------|
| POST | `/auth/signup` | Register; returns token pair |
| POST | `/auth/login` | Login; returns token pair |
| POST | `/auth/refresh` | New tokens from refresh token |
| POST | `/auth/logout` | Revoke refresh token (**Bearer required**) |
| GET | `/auth/me` | Current user (**Bearer required**) |

### 5.3 Files (`/files`)

| Method | Path | Description |
|--------|------|---------------|
| POST | `/files/upload` | `multipart/form-data` field `file` |
| GET | `/files` | List (`limit`, `offset`) |
| GET | `/files/{id}` | Detail |
| DELETE | `/files/{id}` | Delete file |

### 5.4 Scans (`/scans`)

| Method | Path | Description |
|--------|------|---------------|
| POST | `/scans` | Body `{ "file_id": "<uuid>" }` — runs pipeline inline |
| GET | `/scans` | List |
| GET | `/scans/{scan_id}` | Detail + findings + recommendations + compliance_score |
| GET | `/scans/{scan_id}/recommendations` | Recommendations list |

### 5.5 Reports (`/reports`)

| Method | Path | Description |
|--------|------|---------------|
| POST | `/reports` | Body `{ "scan_id": "<uuid>" }` — generates JSON + PDF, **201** |
| GET | `/reports` | List (executive summary subset per item) |
| GET | `/reports/{report_id}` | Metadata + full `summary` (alias for stored JSON) |
| GET | `/reports/{report_id}/export?format=json|pdf` | Download blob |

**Schema note:** `ReportDetailResponse` uses `validation_alias="summary_json"` and serializes as **`summary`** in JSON responses. Factory `from_report()` must pass `summary_json=...` (implemented fix for report generation).

### 5.6 Scoring (`/scoring`)

| Method | Path | Description |
|--------|------|---------------|
| GET | `/scoring/config` | Public scoring weights/thresholds from env |

### 5.7 Protected examples (`/protected`)

| Method | Path | Description |
|--------|------|---------------|
| GET | `/protected/profile` | Example protected route |
| GET | `/protected/status` | Example protected route |

---

## 6. Sprint 1 — domain flows

### 6.1 Registration & session

1. `POST /auth/signup` or `POST /auth/login` → store `access_token`, `refresh_token` (frontend: `localStorage` via `lib/auth.ts`).
2. On **401**, frontend retries `POST /auth/refresh` then replays request (`lib/api.ts`).

### 6.2 Upload → scan → report

1. `POST /files/upload` → file row + metadata extraction.
2. `POST /scans` with `file_id` → synchronous scan; redirect UI to `/scans/{id}`.
3. `POST /reports` with `scan_id` → writes `reports` + storage artifacts.
4. `GET /reports/{id}/export?format=pdf|json` → download.

---

## 7. Sprint 1 — configuration & environment

Key settings from **`app/core/config.py`** (env aliases in parentheses):

| Area | Variables |
|------|-----------|
| App | `APP_NAME`, `APP_ENV`, `DEBUG`, `API_V1_PREFIX` |
| DB | `DATABASE_URL` (asyncpg URL) |
| JWT | `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`, `JWT_REFRESH_TOKEN_EXPIRE_DAYS` |
| CORS | `CORS_ORIGINS` (comma-separated) |
| Storage | `STORAGE_BACKEND` (local), `STORAGE_LOCAL_PATH`, `MAX_UPLOAD_SIZE_MB`, `ALLOWED_FILE_EXTENSIONS`, `METADATA_PREVIEW_ROWS` |
| Scanner | `SCAN_MAX_SAMPLE_ROWS`, `SCAN_MATCH_THRESHOLD` |
| Scoring | `SCORE_SEVERITY_WEIGHTS`, `SCORE_FINDING_TYPE_WEIGHTS`, `SCORE_COMPLIANT_MAX`, `SCORE_RISKY_MAX`, `SCORE_MAX`, `SCORE_DENSITY_MULTIPLIER`, classification thresholds, `SCORE_CRITICAL_ESCALATION_MATCH_RATE`, `SCORE_FORCE_NON_COMPLIANT_ON_CRITICAL` |

**Frontend:** `NEXT_PUBLIC_API_URL` (default `http://localhost:8000/api/v1`).

---

## 8. Sprint 1 — frontend

- **Framework:** Next.js 14 App Router, TypeScript, Tailwind.
- **Routes (typical):** `/login`, `/signup`, `/` (overview), `/files`, `/scans`, `/scans/[id]`, `/reports`.
- **API client:** `frontend/src/lib/api.ts` — Bearer header, refresh on 401.
- **Guards:** `AuthGuard` wraps dashboard layout.

---

## 9. Sprint 1 — security & operations

### 9.1 Practices

- JWT access tokens for API auth; refresh rotation/revocation via DB.
- User-scoped file and scan access in services/repositories.
- Do not commit `.env`; rotate `JWT_SECRET_KEY` per environment.
- CORS restricted via `CORS_ORIGINS`.

### 9.2 Local run (typical)

```bash
docker compose up -d postgres
cd backend && source .venv/bin/activate && alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
cd frontend && npm run dev
```

**Note:** Use project **venv** or `./run.sh` so dependencies (FastAPI, etc.) resolve. PostgreSQL must be up before auth/upload.

### 9.3 Tests

Backend: `pytest` under `backend/tests/` (unit tests for scanner, scoring, recommendations, reports, storage; integration may skip without DB).

---

## 10. Sprint 2 — planned extension (policy-driven execution security)

### 10.1 Objectives (not in repo until implemented)

| # | Capability |
|---|------------|
| 1 | **Model compliance checker** — detect external vs local/cloud models; risky combinations with dataset sensitivity |
| 2 | **Pre-execution compliance check** — validate `dataset + model` before “execution”; compute execution risk |
| 3 | **Execution blocking engine** — `ALLOW` / `WARN` / `BLOCK` with configurable thresholds |
| 4 | **Advanced rule engine** — DB-backed rules: severity, category, priority, enable/disable, custom conditions |
| 5 | **Policy management** — CRUD policies (data / execution / model), activate/deactivate, thresholds |
| 6 | **Audit logging** — uploads, scans, execution validations, blocks, policy changes, auth events |
| 7 | **RBAC** — roles: **Admin**, **User**, **Auditor**; permission-gated routes |
| 8 | **Execution workflow** — Upload → Select model → Validate → Decision → audit |
| 9 | **Dashboard** — violations, blocks, audit history, model risk, policy/rule admin screens |

**Explicitly out of scope for Sprint 2:** real-time monitoring, prompt/output AI monitoring, multi-tenant isolation, Kubernetes, CI/CD compliance pipelines.

### 10.2 Architecture extension (conceptual)

New bounded contexts:

- **`policies`** + **`rules`** → evaluated by **`RuleEngine`**
- **`models`** registry (declared execution targets, not ML weights)
- **`execution_requests`** + **`execution_evaluations`** → store allow/warn/block outcomes
- **`audit_logs`** → append-only events
- **`roles` / `permissions` / `user_roles`** → RBAC

Sprint 1 **scans** and **scoring** outputs become **inputs** to Sprint 2 evaluation context.

---

## 11. Sprint 2 — planned database additions

| Table | Purpose |
|-------|---------|
| `roles` | Seed: admin, user, auditor |
| `permissions` | Fine-grained strings (`policy:write`, `audit:read`, …) |
| `role_permissions` | M:N |
| `user_roles` | M:N user ↔ role |
| `policies` | Policy definition JSON, type, thresholds, `is_active`, versioning optional |
| `rules` | Condition JSON (DSL), action, severity, category, priority, `is_enabled`, optional `policy_id` |
| `models` (registry) | Provider, deployment (local/cloud), `is_external`, risk tier, metadata |
| `execution_requests` | `user_id`, `file_id`, `model_id`, optional `scan_id`, decision, status, timestamps |
| `execution_evaluations` | Snapshot: matched rules, scores, reason codes (replay/debug) |
| `audit_logs` | Immutable: timestamp, actor, action, resource, risk_level, status, metadata JSON |

**User table:** extend with role assignment via `user_roles` (preferred) or single `role_id` for minimal MVP.

---

## 12. Sprint 2 — planned APIs & modules

### 12.1 Planned REST areas (under `/api/v1`)

| Prefix | Audience | Purpose |
|--------|----------|---------|
| `/policies` | Admin | CRUD, activate/deactivate |
| `/rules` | Admin | CRUD, toggle, reorder priority, dry-run test |
| `/models` | Admin (write), all (read) | Model registry |
| `/executions` | User | `POST /validate`, list/get own requests |
| `/audit-logs` | Admin, Auditor | Filtered read |

### 12.2 Planned backend folders

```
app/
  models/          # + role, permission, policy, rule, model_registry, execution_*, audit_log
  repositories/    # matching repos
  services/
    policies/
    rules/
    execution/
    models_registry/   # or model_compliance.py
    audit/
  schemas/
  api/v1/          # + policies.py, rules.py, executions.py, audit.py, models_registry.py
  middleware/      # request_id, optional structured logging
auth/dependencies.py  # require_permission("...")
```

### 12.3 Planned frontend routes

- `/policies`, `/rules`, `/models`, `/executions`, `/executions/new`, `/audit`
- `lib/permissions.ts` for UI visibility based on role/permissions

---

## 13. Sprint 2 — execution validation workflow

```
Upload dataset (Sprint 1)
       ↓
Select model from registry (Sprint 2)
       ↓
Run compliance validation (reuse latest scan or trigger scan)
       ↓
Evaluate policies + rules → risk + decision
       ↓
ALLOW / WARN / BLOCK (+ persist execution_request, evaluation, audit_log)
```

Sprint 2 “execution” is **validation + persisted intent**; actual job runners/queues are a later concern.

---

## 14. Sprint 2 — RBAC, audit, rule/policy samples

### 14.1 Role → permission matrix (example)

| Permission | Admin | User | Auditor |
|------------|:-----:|:----:|:-------:|
| `file:*`, `scan:*`, `execution:request` | ✓ | ✓ | ✗ |
| `report:read` | ✓ | ✓ | ✓ |
| `policy:*`, `rule:*`, `model:*` (write) | ✓ | ✗ | ✗ |
| `audit:read` | ✓ | ✗ | ✓ |
| `user:manage` (optional) | ✓ | ✗ | ✗ |

### 14.2 Example rule (JSON condition)

```json
{
  "code": "block-password-external",
  "category": "data_leakage",
  "severity": "critical",
  "priority": 100,
  "action": "block",
  "condition": {
    "all": [
      { "finding_type_exists": "password" },
      { "eq": ["model.is_external", true] }
    ]
  }
}
```

### 14.3 Example policy (JSON)

```json
{
  "type": "execution",
  "name": "Default execution policy",
  "is_active": true,
  "thresholds": {
    "block_if_risk_score_gte": 80,
    "warn_if_risk_score_gte": 50,
    "block_on_compliance": ["non_compliant"]
  }
}
```

### 14.4 Example audit event

```json
{
  "timestamp": "2026-05-18T12:00:00Z",
  "actor_user_id": "<uuid>",
  "action": "execution.blocked",
  "risk_level": "high",
  "status": "blocked",
  "metadata": {
    "file_id": "<uuid>",
    "model_id": "<uuid>",
    "reason_codes": ["PASSWORD_WITH_EXTERNAL_MODEL"]
  }
}
```

### 14.5 Audit strategy

- **Append-only** `audit_logs`; no app-level updates/deletes.
- **AuditService** invoked from domain services (not only routers).
- **Redact** secrets and tokens from `metadata_json`.

---

## 15. Sprint 3 — scalability hooks (forward-looking)

- Partition or archive `audit_logs` by time.
- Cache active policy/rule sets with invalidation on admin writes.
- Async workers for heavy validation or future real-time features.
- Read replicas for auditor dashboards.
- Event outbox for notifications and external SIEM integration.

---

## Appendix — migrations index

| Revision | File | Description |
|----------|------|-------------|
| 001 | `001_initial_auth_tables.py` | `users`, `refresh_tokens` |
| 002 | `002_file_upload_tables.py` | `files`, `file_metadata` |
| 003 | `003_compliance_scan_tables.py` | `scans`, `scan_findings` |
| 004 | `004_scan_score_breakdown.py` | `scans.score_breakdown_json` |
| 005 | `005_scan_recommendations.py` | `scan_recommendations` |
| 006 | `006_compliance_reports.py` | `reports` |
| 007 | `007_sprint2_rbac_policy_execution_audit.py` | Sprint 2: roles, permissions, policies, rules, user_roles, audit_logs, execution_requests, model_validations, execution_results |

Sprint 2 adds further migrations (008+) for optional links (e.g. `role_permissions`, `reports` ↔ executions) as features land.

## Document maintenance

- Update **§4–§5** whenever migrations or routes change.
- After Sprint 2 implementation, replace **“planned”** sections with **“implemented”** and link to actual module paths and OpenAPI (`/docs` in development).

---

*Last consolidated: 2026-05-18 — aligns with backend migrations 001–006 and `app/api/v1/router.py` as of that date.*
