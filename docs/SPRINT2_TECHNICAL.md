# Sprint 2 Technical Documentation

ComplianceGuard Sprint 2 delivers governance controls: RBAC, audit logging, a database-driven rule engine, policy management, model compliance checks, pre-execution validation, execution blocking, and dashboard modules.

## Architecture Overview

```
┌─────────────┐     JWT + RBAC      ┌──────────────────────────────────────┐
│  Next.js    │ ◄──────────────────►│  FastAPI (/api/v1)                   │
│  Dashboard  │                     │  ├─ auth, files, scans, reports      │
└─────────────┘                     │  ├─ rules, policies, models            │
                                    │  ├─ executions (validate/block/start)  │
                                    │  └─ audit-logs                         │
                                    └──────────────┬───────────────────────┘
                                                   │
                                    ┌──────────────▼───────────────────────┐
                                    │  PostgreSQL                          │
                                    │  users, roles, permissions, rules,     │
                                    │  policies, models, executions, audit │
                                    └──────────────────────────────────────┘
```

### Evaluation pipeline (shared orchestrator)

`ComplianceEvaluationOrchestrator` (`app/services/compliance/orchestrator.py`) runs a single evaluation pass:

1. Build `DatasetContext` from scan findings
2. Build `RuleEvaluationContext` (scan + model deployment flags)
3. Evaluate enabled rules → `RuleEvaluationResult`
4. Evaluate active policies → `PoliciesEvaluationResult`
5. Run model built-in risk checks → `ModelComplianceCheckResult`
6. `PreExecutionValidator.aggregate()` combines outcomes → **allow / warn / block**

Used by both `ExecutionValidationService` and `ModelComplianceService`.

---

## Execution Workflow

```
Upload dataset (POST /files/upload)
        ↓
Run scan (POST /scans)
        ↓
Select compliance model (GET /models)
        ↓
Pre-execution validation (POST /executions/validate)
        ├─ Rule evaluation
        ├─ Policy evaluation (thresholds)
        └─ Model risk checks
        ↓
Decision: ALLOW | WARN | BLOCK
        ↓
Status update on execution_request
        ├─ allowed → can start
        ├─ warn → warning_pending_acknowledgement
        └─ block → blocked
        ↓
(Optional) Acknowledge warning (POST /executions/{id}/acknowledge-warning)
        ↓
Start execution (POST /executions/{id}/start) — enforcement only, no runner
        ↓
Audit events (execution.requested, execution.decision, execution.blocked, …)
```

### Example workflows (seed data migration 016)

| Scenario | Dataset fixture | Model code | Expected decision |
|----------|-----------------|------------|-------------------|
| Safe local | `safe_internal.csv` (email only) | `DEMO_LOCAL_LLM` | allow or warn |
| Warning path | `warning_confidential.csv` | `DEMO_CLOUD_UNAPPROVED` | warn (may need ack) |
| Blocked external | `blocked_passwords.csv` | `DEMO_EXTERNAL_API` | block |

Demo policies: **Demo Execution Baseline**, **Demo Data Protection** (active, linked to seeded rules).

---

## RBAC Structure

### Roles

| Role | Purpose |
|------|---------|
| `user` | Upload, scan, request executions, read own data |
| `admin` | Full management: policies, rules, models, all executions |
| `auditor` | Read-only: audit logs, reports, execution history |

### Key permissions

| Permission | Description |
|------------|-------------|
| `file:upload`, `file:read` | Dataset management |
| `scan:run`, `scan:read` | Compliance scans |
| `execution:request` | Validate and start executions |
| `execution:read`, `execution:read_all` | View own vs all executions |
| `policy:manage` | CRUD policies, register models |
| `rule:manage` | CRUD rules, enable/disable |
| `audit:read` | Audit log access |

JWT access tokens include `roles` and `permissions` claims; `/auth/me` returns fresh RBAC from DB.

---

## Rule Engine

- **Storage:** `compliance_rules` table (seeded in migration 010)
- **Package:** `app/services/rules/`
- **Condition JSON:** field/operator/value or compound `all` / `any` / `not`
- **Actions:** `allow`, `warn`, `block`
- **API:** `GET/POST/PATCH /rules`, `POST /rules/{id}/enable|disable`

### Seeded rules (examples)

| Code | Trigger | Action |
|------|---------|--------|
| `data.email_detected` | email in dataset | warn |
| `data.password_detected` | password column | block |
| `data.api_key_detected` | api_key pattern | block |
| `model.sensitive_data_external` | sensitive + external model | block |

---

## Policy Engine

- **Storage:** `compliance_policies`, `policy_rules` (many-to-many)
- **Thresholds:** `definition_json.thresholds` — `block_below`, `warn_below` (risk score 0–100)
- **Statuses:** draft, active, inactive, archived
- **Package:** `app/services/policies/`
- **API:** `GET/POST/PATCH /policies`, activate/deactivate, attach/detach rules

Policy evaluation aggregates rule outcomes per policy and applies threshold-based decisions.

---

## API Reference (Sprint 2)

Base URL: `http://localhost:8000/api/v1`  
Interactive docs: `GET /docs` (development)

### Executions

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| POST | `/executions/validate` | `execution:request` | Full pre-execution check |
| GET | `/executions` | `execution:request\|read\|read_all` | List history |
| GET | `/executions/{id}` | same | Request detail |
| GET | `/executions/{id}/status` | same | Blocking status |
| POST | `/executions/{id}/acknowledge-warning` | `execution:request` | Accept warn |
| POST | `/executions/{id}/start` | `execution:request` | Start (if allowed) |

### Policies & rules

| Method | Path | Permission |
|--------|------|------------|
| GET | `/policies`, `/policies/active` | `scan:read` |
| POST/PATCH | `/policies` | `policy:manage` |
| GET | `/rules` | `scan:read` |
| POST/PATCH | `/rules` | `rule:manage` |

### Models & audit

| Method | Path | Permission |
|--------|------|------------|
| GET/POST | `/models` | read: `scan:read`, create: `policy:manage` |
| POST | `/models/validate` | `execution:request` |
| GET | `/audit-logs` | `audit:read` |

### Error responses

HTTP errors return backward-compatible `detail` plus structured `error`:

```json
{
  "detail": "Missing permissions: policy:manage",
  "error": {
    "code": 403,
    "message": "Missing permissions: policy:manage",
    "type": "http_error"
  }
}
```

---

## Database & Performance

### Indexes (Sprint 2 relevant)

- `compliance_policies`: `is_active`, `policy_type`, `status`, `priority`
- `compliance_rules`: `code`, `category`, `is_enabled`
- `execution_requests`: `user_id`, `status`
- `audit_logs`: `user_id`, `action`, `created_at`

### Pagination

List endpoints accept `limit` (1–200) and `offset`. Responses include `items`, `total`, `limit`, `offset`.

---

## Testing

### Backend

```bash
cd backend
alembic upgrade head   # through 016
pytest                 # unit tests
pytest -m integration  # PostgreSQL required
```

| Suite | File | Coverage |
|-------|------|----------|
| E2E workflow | `tests/test_sprint2_e2e_workflow.py` | Upload → scan → validate → start |
| API integration | `tests/test_sprint2_api_integration.py` | RBAC, policies, rules, audit |
| Orchestrator | `tests/test_compliance_orchestrator.py` | Shared evaluation |

Fixtures: `tests/fixtures/datasets/*.csv`

### Frontend

```bash
cd frontend
npm run test        # Vitest (unit)
npm run test:e2e    # Playwright (dashboard)
```

---

## Migrations

| Rev | Description |
|-----|-------------|
| 007–008 | RBAC tables + seed roles/permissions |
| 010 | Rule engine + seed rules |
| 011 | Policy status/priority |
| 012 | Model compliance tables |
| 013–015 | Pre-execution + blocking fields |
| 016 | Demo models, policies, rule links |
