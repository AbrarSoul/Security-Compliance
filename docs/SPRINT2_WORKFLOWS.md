# Sprint 2 Example Workflows

Step-by-step examples using seeded demo data (migration `016`) and test fixtures.

## Prerequisites

```bash
docker compose up -d postgres
cd backend && alembic upgrade head && uvicorn app.main:app --reload
cd frontend && npm run dev
```

Sign up or log in as a user with `execution:request`. Assign `admin` for policy/rule management demos.

---

## 1. Safe local model execution

**Goal:** Email-only internal dataset with an approved local model → allow (or low warn).

1. Upload `backend/tests/fixtures/datasets/safe_internal.csv`
2. Run scan on the uploaded file
3. Select model **Demo Local LLM** (`DEMO_LOCAL_LLM`)
4. POST `/api/v1/executions/validate` with scan + model IDs
5. Expect `decision: "allow"` (or `"warn"` if email rule fires)
6. GET `/executions/{id}/status` → `can_start: true`
7. POST `/executions/{id}/start` → status `started`

**Audit:** `execution.requested`, `execution.decision` with `allow` or `warn`.

---

## 2. Warning-level execution

**Goal:** Risky dataset or unapproved cloud model → warn, acknowledgement required.

1. Upload `warning_confidential.csv`
2. Complete scan
3. Use **Demo Cloud Model (Unapproved)** (`DEMO_CLOUD_UNAPPROVED`)
4. Validate execution → `decision: "warn"`
5. Status → `warning_pending_acknowledgement`, `requires_acknowledgement: true`
6. POST `/executions/{id}/acknowledge-warning` with a note
7. POST `/executions/{id}/start` after acknowledgement

---

## 3. Blocked external API execution

**Goal:** Password/API key data with external model → block, cannot start.

1. Upload `blocked_passwords.csv`
2. Complete scan (detects `password`, possibly `api_key`)
3. Use **Demo External API (GPT)** (`DEMO_EXTERNAL_API`)
4. Validate → `decision: "block"`
5. `triggered_rules` includes password/API rules; `policy_violations` may list demo policies
6. GET status → `can_start: false`, `blocking_reasons` populated
7. POST `/start` → **403/400** (rejected)

**Audit:** `execution.blocked` event logged.

---

## Automated verification

```bash
cd backend
pytest -m integration tests/test_sprint2_e2e_workflow.py -v
```

These tests run the same flows against a live database.
