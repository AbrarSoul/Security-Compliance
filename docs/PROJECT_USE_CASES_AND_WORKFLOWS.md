# ComplianceGuard — Use Cases & Workflows Reference

A single reference for every major capability in the **Security-Compliance** project (branded **ComplianceGuard** in the UI). Use this document for onboarding, demos, audits, and future development planning.

**Related docs:** [`USER_GUIDE.md`](../USER_GUIDE.md) · [`GAIRA_USER_GUIDE.md`](../GAIRA_USER_GUIDE.md) · [`PLATFORM_REFERENCE.md`](PLATFORM_REFERENCE.md) · [`Running_commands.md`](../Running_commands.md)

---

## Table of contents

1. [What this project does](#1-what-this-project-does)
2. [Architecture at a glance](#2-architecture-at-a-glance)
3. [Roles and permissions](#3-roles-and-permissions)
4. [Platform lifecycle (four stages)](#4-platform-lifecycle-four-stages)
5. [Module reference — use cases & workflows](#5-module-reference--use-cases--workflows)
6. [End-to-end scenario workflows](#6-end-to-end-scenario-workflows)
7. [API quick reference](#7-api-quick-reference)
8. [Local setup & operations](#8-local-setup--operations)
9. [Status & decision vocabulary](#9-status--decision-vocabulary)
10. [Glossary](#10-glossary)
11. [Document index](#11-document-index)

---

## 1. What this project does

**ComplianceGuard** helps security and compliance teams answer two related questions:

| Layer | Question | How it is answered |
|-------|----------|-------------------|
| **Governance (GAIRA)** | Should we build or deploy this AI application, and at what risk level? | Structured GAIRA questionnaires, ROAIA inventory |
| **Operations** | Is this dataset (or prompt/output) safe to use with this AI model right now? | File scanning, rules/policies, execution validation, live guard |

### Primary use cases

| # | Use case | Who | Outcome |
|---|----------|-----|---------|
| 1 | **Dataset compliance scanning** | Analyst, Admin | Risk score, findings, recommendations per file |
| 2 | **Compliance reporting** | Analyst, Auditor | Shareable JSON/PDF audit artifacts |
| 3 | **AI model governance** | Admin | Registry of approved models (local vs external) |
| 4 | **Pre-execution validation** | Analyst | `allow` / `warn` / `block` before running AI on data |
| 5 | **Live execution guard** | Analyst | Real-time prompt/output scanning during execution |
| 6 | **Policy & rule management** | Admin | Configurable compliance logic (GDPR-style bundles, atomic rules) |
| 7 | **GAIRA AI risk assessment** | User, Admin | Project-level AI governance before deployment |
| 8 | **Analytics & trends** | All roles (scoped) | Block rates, violations, high-risk users/models |
| 9 | **Gap analysis** | Admin (run), All (view) | Posture score + remediation backlog |
| 10 | **Threat detection** | Admin (run), All (view) | Security threats from abnormal behavior |
| 11 | **Notifications** | All users | In-app (and optional email) alerts |
| 12 | **Audit trail** | Admin, Auditor | Immutable log of actions and decisions |

### What compliance means here

The platform checks against **internal rules and policies** configured in the system — not automatic certification against ISO, NIST, or SOC 2. Admins tune rules to reflect organizational requirements. See [`COMPLIANCE_QA.md`](COMPLIANCE_QA.md) for supervisor-friendly explanations.

---

## 2. Architecture at a glance

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Next.js 14 Dashboard (http://localhost:3000)                               │
│  Overview · Files · Scans · Reports · Executions · Models · GAIRA · …       │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ JWT Bearer + RBAC
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  FastAPI Backend (http://localhost:8000/api/v1)                           │
│  auth · files · scans · reports · rules · policies · models · executions  │
│  gaira · monitoring · guard · notifications · analytics · gaps · threats    │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          ▼                         ▼                         ▼
   PostgreSQL              Local file storage          Outbox worker
   (users, scans,           (uploads, reports)         (notifications,
    rules, executions,                                  threats, SSE)
    gaira, events, …)
```

### Backend layering

| Layer | Location | Responsibility |
|-------|----------|----------------|
| API | `backend/app/api/v1/` | HTTP routes, auth deps, request/response mapping |
| Auth | `backend/app/auth/` | JWT signup/login/refresh, `ActiveUser`, RBAC |
| Services | `backend/app/services/` | Business logic (scan, score, guard, gaira, …) |
| Repositories | `backend/app/repositories/` | Database access |
| Models | `backend/app/models/` | SQLAlchemy ORM |
| Storage | `backend/app/storage/` | User-scoped local file paths |

### Key internal pipelines

**Scan pipeline:**
```
POST /scans { file_id }
  → load file from storage
  → ComplianceScanner (detectors: email, phone, password, api_key, sensitive fields)
  → ComplianceScoringEngine → risk_score + compliance_status
  → RecommendationEngine → scan_recommendations
  → persist Scan + findings
```

**Execution validation pipeline:**
```
POST /executions/validate { file_id, scan_id, model_id }
  → ComplianceEvaluationOrchestrator
  → evaluate enabled rules + active policies against scan context + model metadata
  → decision: allow | warn | block
  → persist ExecutionRequest
```

**Live monitoring pipeline (Sprint 3):**
```
POST /monitoring/guard/executions/{id}/prompt|output
  → PromptMonitoringService / OutputMonitoringService
  → ComplianceGuardService (runtime rules)
  → domain_events + event_outbox
  → OutboxWorker → notifications, threat detection, audit logs
```

---

## 3. Roles and permissions

New signups get the **user** role. Admins assign **admin** or **auditor**. After a role change, the user must **sign out and sign back in** for the JWT to pick up new permissions.

### Role summary

| Role | Purpose | Typical access |
|------|---------|----------------|
| **user** | Day-to-day analyst | Upload, scan, report, request executions, GAIRA assessments, own analytics |
| **admin** | Platform owner | Everything + manage rules/policies, sync models, run gap/threat analysis |
| **auditor** | Compliance officer | Read-only org-wide: reports, executions, GAIRA, gaps, threats, audit logs |

### Permission matrix (canonical)

| Permission | Admin | User | Auditor |
|------------|:-----:|:----:|:-------:|
| `file:upload`, `file:read` | ✓ | ✓ | — |
| `scan:run`, `scan:read` | ✓ | ✓ | — |
| `report:read` | ✓ | ✓ | — |
| `report:read_all` | ✓ | — | ✓ |
| `execution:request` | ✓ | ✓ | — |
| `execution:read` | ✓ | — | ✓ |
| `execution:read_all` | ✓ | — | — |
| `rule:manage`, `policy:manage` | ✓ | — | — |
| `audit:read` | ✓ | — | ✓ |
| `monitoring:*` (read/publish/manage) | ✓ | read/publish/manage | read/read_all |
| `notification:*` | ✓ | read/manage | read/read_all |
| `analytics:read` | ✓ | ✓ | read_all |
| `gap:read`, `gap:analyze` | ✓ | read | read/read_all |
| `threat:read`, `threat:manage` | ✓ | read | read/read_all |
| `gaira:read`, `gaira:manage` | ✓ | ✓ | read/read_all |

Source of truth: `backend/app/core/permissions.py`

### Dashboard navigation (sidebar groups)

| Group | Pages |
|-------|-------|
| **Platform** | Overview, Files, Scans, Reports |
| **Compliance** | Executions, Models |
| **Governance** | GAIRA, Policies, Rules |
| **Monitoring** | Analytics, Gap analysis, Threat detection |
| **Audit** | Audit logs |

Pages are hidden when the user's role lacks the required permission.

---

## 4. Platform lifecycle (four stages)

```
 Stage 0 — AI Governance          Stage 1 — Data Preparation       Stage 2 — Execution Gov.        Stage 3 — Live Monitoring
 ┌──────────────────────────┐     ┌─────────────────────────┐     ┌──────────────────────────┐     ┌─────────────────────────────┐
 │ Register AI application  │     │ Upload dataset          │     │ Validate execution       │     │ Monitor prompts & outputs   │
 │ AI Risk Levels triage    │  →  │ Run compliance scan     │  →  │ Acknowledge warnings     │  →  │ Analytics & trends          │
 │ GAIRA Light/Comprehensive│     │ Generate report         │     │ Start execution + guard  │     │ Gap analysis & threats      │
 │ ROAIA inventory updated  │     │ Fix critical findings   │     │                          │     │ Audit logs & notifications  │
 └──────────────────────────┘     └─────────────────────────┘     └──────────────────────────┘     └─────────────────────────────┘
```

**Important:** GAIRA (Stage 0) and execution validation (Stage 2) are **separate gates** today. A completed GAIRA assessment does not automatically block executions — treat `gaira_status: done` as an organizational policy requirement before production.

---

## 5. Module reference — use cases & workflows

### 5.1 Authentication

**Use case:** Secure access to all platform features.

| UI | API |
|----|-----|
| `/login`, `/signup` | `POST /api/v1/auth/login`, `POST /api/v1/auth/signup` |

**Workflow:**
1. User signs up (password: ≥8 chars, upper, lower, digit) → receives JWT access + refresh tokens.
2. Frontend stores tokens; sends `Authorization: Bearer <access_token>` on API calls.
3. Token refresh via `POST /auth/refresh`; logout revokes refresh token.
4. `GET /auth/me` returns current user profile and roles.

---

### 5.2 Files

**Use case:** Upload datasets before scanning.

| UI | API |
|----|-----|
| `/files` | `POST /files/upload`, `GET /files`, `DELETE /files/{id}` |

**Workflow:**
1. Click **Upload** → select `.csv`, `.json`, or `.txt` (default max 50 MB).
2. Backend stores file under `STORAGE_LOCAL_PATH` (default `./uploads`), scoped per user.
3. Metadata extracted automatically: row/column counts, schema preview.
4. File appears in list; can be deleted anytime.
5. A file is required before creating a scan.

**Supported detection inputs:** CSV rows, JSON structures, plain text.

---

### 5.3 Scans

**Use case:** Detect sensitive content and classify dataset risk.

| UI | API |
|----|-----|
| `/scans`, `/scans/[id]` | `POST /scans`, `GET /scans/{id}`, `GET /scans/{id}/recommendations` |

**What is detected:**

| Detector | Examples |
|----------|----------|
| Email | Email addresses in cell values |
| Phone | Phone number patterns |
| Password | Password-like values and columns |
| API key | Secret key patterns |
| Sensitive field | Column names like `ssn`, `password`, `credit_card` |
| Name | Person-name heuristics (where configured) |

**Workflow:**
1. **Scans** → **New scan** → pick uploaded file.
2. Scanner samples rows (`scan_max_sample_rows` from config).
3. Scoring engine computes **risk score** (0–100) and **compliance status**.
4. Recommendation engine generates remediation actions.
5. Open scan detail to review findings (severity, column, evidence) and recommendations.

**Scoring bands (defaults):**

| Risk score | Status |
|------------|--------|
| 0 – 30 | `compliant` |
| 31 – 60 | `risky` |
| 61 – 100 | `non_compliant` |

Critical findings can force `non_compliant` regardless of score (`SCORE_FORCE_NON_COMPLIANT_ON_CRITICAL=true`).

**Recommendation action types:** `anonymize`, `mask`, `remove_column`, `rotate_secret`, `encrypt`, `restrict_access`, `review_policy`, `audit_logging`.

---

### 5.4 Reports

**Use case:** Export scan results for auditors, stakeholders, or external systems.

| UI | API |
|----|-----|
| `/reports`, scan detail **Generate report** | `POST /reports`, `GET /reports/{id}/export?format=json|pdf` |

**Workflow:**
1. From a completed scan → **Generate report** (or from Reports page).
2. Backend builds JSON summary + PDF (ReportLab).
3. Download JSON for systems integration; PDF for human review.
4. One report per scan in current design.

---

### 5.5 Models (compliance model registry)

**Use case:** Govern which AI endpoints the organization allows — metadata only, not model weights.

| UI | API |
|----|-----|
| `/models`, `/models/[id]`, `/models/validations/[id]` | `GET/POST/PATCH /compliance-models`, `POST /compliance-models/sync-gptlab`, `POST /compliance-models/validate` |

**Key fields:**

| Field | Meaning |
|-------|---------|
| **Code** | Stable ID (e.g. `GPTLAB_LLAMA3_1_8B`) |
| **Provider** | GPT-Lab, OpenAI, Internal, etc. |
| **Deployment** | `local` (data stays in environment) vs `external` (data leaves) |
| **is_approved** | Compliance sign-off for general use |
| **is_active** | Appears in execution dropdowns |
| **data_leaves_platform** | Whether prompts/data are sent outside ComplianceGuard |

**Workflows:**

| Workflow | Steps | Who |
|----------|-------|-----|
| **Browse models** | Models page → click row for profile | All |
| **Dry-run validation** | Model detail → **Run validation** (scan + model → allow/warn/block) | All |
| **Sync from GPT-Lab** | Models → **Sync from GPT-Lab** (needs `GPTLAB_API_KEY`) | Admin |
| **Manual register** | Models → **Register model** | Admin |

Demo models (`DEMO_LOCAL_LLM`, `DEMO_CLOUD_UNAPPROVED`, `DEMO_EXTERNAL_API`) ship with seeded data for workflow testing.

---

### 5.6 Executions

**Use case:** Decide whether a dataset can run through a specific AI model, then execute with live guard.

| UI | API |
|----|-----|
| `/executions`, `/executions/validate`, `/executions/[id]` | `POST /executions/validate`, `GET /executions/{id}/status`, `POST /executions/{id}/acknowledge-warning`, `POST /executions/{id}/start` |

**Workflow:**

```
1. Request validation     file + scan + model  →  decision (allow / warn / block)
2. If warn:               Acknowledge warning explicitly
3. Start execution        Guard monitors each prompt and output
4. Runtime                Risky content → warn, block, or interrupt
5. Final status           completed | interrupted | blocked
```

**Execution statuses:**

| Status | Meaning |
|--------|---------|
| `pending_validation` | Awaiting evaluation |
| `allowed` | Safe to start |
| `warning_pending_acknowledgement` | Risky; needs user confirmation |
| `approved_after_warning` | Warning acknowledged; can start |
| `blocked` | Cannot start or continue |
| `started` | Running |
| `interrupted` | Guard stopped mid-run |
| `completed` | Finished successfully |

**Decision outcomes:**

| Decision | `can_start` | Next action |
|----------|-------------|-------------|
| `allow` | true | Start immediately |
| `warn` | false until ack | `POST .../acknowledge-warning`, then start |
| `block` | false | Review `blocking_reasons` and `triggered_rules` |

---

### 5.7 Rules

**Use case:** Atomic compliance checks evaluated against scans and executions.

| UI | API |
|----|-----|
| `/rules` | `GET/POST/PATCH /rules`, `POST /rules/{id}/enable|disable` |

**Rule anatomy:**

| Attribute | Purpose |
|-----------|---------|
| **Condition** | What triggers the rule (finding type, model flags, etc.) |
| **Severity** | `critical`, `high`, `medium`, `low` |
| **Action** | `allow`, `warn`, or `block` |
| **Priority** | Evaluation order when multiple rules match |
| **enabled** | On/off switch |

**Workflow (admin):**
1. **Rules** → create or edit rule.
2. Set condition, severity, action, priority.
3. Enable/disable without deleting.
4. Rules fire during scan scoring context and execution validation.

**Example rules (seeded):** password detected + external model → block; email only + local model → allow or warn.

---

### 5.8 Policies

**Use case:** Bundle rules under a named standard or organizational policy.

| UI | API |
|----|-----|
| `/policies`, `/policies/[id]` | `GET/POST/PATCH /policies`, `POST /policies/{id}/rules`, `POST /policies/evaluate` |

**Workflow (admin):**
1. Create policy (e.g. GDPR-style data protection bundle).
2. Attach rules via `POST /policies/{id}/rules`.
3. Activate/deactivate/archive policy.
4. During execution validation, active policies contribute to `policy_violations` in the response.

**Workflow (all users):** Browse active policies to understand what is enforced.

---

### 5.9 GAIRA (AI risk assessment)

**Use case:** Structured governance assessment for AI applications before deployment.

| UI | API |
|----|-----|
| `/gaira`, `/gaira/applications/[id]`, `/gaira/assessments/[id]` | `/api/v1/gaira/*` |

**GAIRA modules:**

| Module key | Purpose |
|------------|---------|
| `ai_risk_levels` | Quick triage → routes to Light or Comprehensive |
| `gaira_light` | Self-service assessment for lower-risk projects |
| `gaira_comprehensive` | Full workshop for high-risk projects |
| `ai_act_check` | EU AI Act applicability |
| `compliance_check` | Operational compliance checklist |
| `roaia` | Records of AI Activities inventory columns |

**Workflow:**

```
1. Register application        GAIRA → Register application
2. Start assessment            Application detail → Start assessment (pick module)
3. Answer questions            Step tabs; save answers (PATCH)
4. Compute                     System recommends risk tier + routing
5. Submit                      Owner sets overall_risk_level + proceed_decision
6. ROAIA inventory             Main GAIRA page shows gaira_status, risk_level
```

**Recommended path:**
1. Register application → link optional `compliance_model_id`.
2. Run **AI Risk Levels** triage.
3. Based on result → **GAIRA Light** (low/medium) or **GAIRA Comprehensive** (high).
4. If Step 4 answers are flagged → add `second_line_reviewer` before submit.

**Auto-prefill sources:** application record, linked compliance model, optional linked scan.

**Risk scales (do not confuse with scan scores):**

| GAIRA risk | Scan compliance |
|------------|-----------------|
| `insignificant` / `low` / `medium` / `high` / `very_high` | `compliant` / `risky` / `non_compliant` + 0–100 score |

Deep reference: [`GAIRA_USER_GUIDE.md`](../GAIRA_USER_GUIDE.md)

---

### 5.10 Real-time monitoring & compliance guard

**Use case:** Scan prompts and outputs during live AI execution; enforce rules at runtime.

| Component | API prefix |
|-----------|------------|
| Monitoring sessions | `/monitoring/sessions`, `/monitoring/events` |
| Prompt scanning | `/monitoring/prompts/scan` |
| Output scanning | `/monitoring/outputs/scan` |
| Compliance guard | `/monitoring/guard/executions/{id}/prompt`, `.../output` |

**Workflow (during execution):**
1. Execution starts → monitoring session opens.
2. Each **prompt** submitted → scanned for PII, secrets, injection, jailbreak patterns.
3. **ComplianceGuardService** evaluates runtime rules → `allowed`, `warned`, `blocked`, or `interrupted`.
4. Each **model output** scanned → leakage detection; sensitive values masked (`[EMAIL_MASKED]`, etc.).
5. Block/violation events → outbox → notifications + threat detection + audit log.
6. SSE streams available: `/monitoring/sessions/{id}/stream`, `/notifications/stream/alerts`.

---

### 5.11 Analytics

**Use case:** Trend analysis for compliance posture over time.

| UI | API |
|----|-----|
| `/analytics` | `GET /analytics/dashboard`, `/summary`, `/trends/*`, `/high-risk/users`, `/high-risk/models` |

**What you see:**
- Total scans, blocked/allowed executions, average risk score
- Time-series: block rate, alert rate, violations by category
- High-risk users and models leaderboards
- Real-time violation widget

**Filters:** 1 / 7 / 30 day windows; optional user/model filters (admin/auditor see org-wide with `analytics:read_all`).

---

### 5.12 Gap analysis

**Use case:** Identify missing controls or misconfigurations (e.g. encryption at rest disabled, no MFA policy).

| UI | API |
|----|-----|
| `/gaps` | `POST /gaps/analyze`, `GET /gaps/dashboard`, `POST /gaps/{id}/acknowledge|resolve` |

**Workflow:**
1. View **posture score** and open gaps grouped by severity.
2. Each gap shows category, remediation steps, detected date.
3. **Acknowledge** — seen, not fixed yet.
4. **Resolve** — fixed, moves to history.
5. **Run analysis** (admin) — recomputes gaps from current platform state.

**Severity guidance:** `critical` = production blocker; `medium`/`low` = backlog items.

---

### 5.13 Threat detection

**Use case:** Security monitoring beyond compliance — suspicious behavior patterns.

| UI | API |
|----|-----|
| `/threats` | `POST /threats/detect`, `GET /threats/dashboard`, `POST /threats/{id}/investigate|resolve` |

**What it detects:**
- Repeated guard blocks from same user (probing)
- Prompt-injection patterns
- Output leakage (secrets, PII in responses)
- Unusual policy violation rates
- Suspicious monitoring session behavior

**Workflow:**
1. Dashboard shows open threats by severity + recent security events.
2. Click threat → see triggering events, affected user/model, suggested response.
3. **Investigate** or **Resolve** (admin).
4. **Run detection** (admin) — batch recompute from recent events.
5. Real-time handler also runs on block/violation domain events.

---

### 5.14 Notifications

**Use case:** Alert users without manual polling.

| UI | API |
|----|-----|
| Bell icon (header) | `GET /notifications`, `GET /notifications/unread-count`, `PATCH /notifications/preferences/me` |

**Alert triggers:**
- Guard blocks your prompt/output
- Rule triggers on your scan
- Threat affects you
- High/critical gap detected

**Channels:** In-app (SSE stream); email when `SMTP_ENABLED=true`.

---

### 5.15 Audit logs

**Use case:** Immutable forensic record for compliance reviews.

| UI | API |
|----|-----|
| `/audit` | `GET /audit-logs` |

**Logged events include:** login, scan, execution decisions, guard actions, policy changes, threat updates, GAIRA actions (where implemented).

**Access:** `audit:read` — typically admin and auditor.

---

### 5.16 Overview dashboard

**Use case:** Landing-page health check after login.

| UI | API |
|----|-----|
| `/` | Aggregates from scans, executions, reports APIs |

**Shows:** Totals, compliance breakdown (compliant/risky/non-compliant), recent scans.

---

## 6. End-to-end scenario workflows

### 6.1 New AI project (governance-first)

```
Day 1   Register AI application          → GAIRA
        Link compliance model (optional)

Day 2   AI Risk Levels triage            → Start assessment → answer → compute → submit
        Result: high → schedule Comprehensive workshop

Day 3–5 GAIRA Light or Comprehensive     → Answer steps → compute → submit
        ROAIA shows gaira_status: done, risk_level set

Ongoing Admin syncs real models          → Models → Sync from GPT-Lab or Register
```

### 6.2 Operational compliance (dataset + execution)

```
1. Upload dataset              → Files
2. Run scan                    → Scans (fix critical findings first)
3. Generate report (optional)  → Reports
4. Validate execution          → Executions (file + scan + model)
5. Acknowledge warning?        → If decision = warn
6. Start execution             → Live guard runs
7. Watch notifications         → Real-time alerts
8. Weekly analytics review     → Analytics
9. Monthly gap analysis        → Gaps (admin runs)
10. Review threats & audit     → Threats, Audit logs
```

### 6.3 Safe local execution (demo data)

**Goal:** Email-only internal data + approved local model → allow.

1. Upload `backend/tests/fixtures/datasets/safe_internal.csv`
2. Run scan
3. Select **Demo Local LLM** (`DEMO_LOCAL_LLM`)
4. Validate → `decision: allow`
5. Start execution → status `started` → `completed`

### 6.4 Warning-level execution

**Goal:** Risky dataset or unapproved cloud model → warn + acknowledgement.

1. Upload `warning_confidential.csv`
2. Complete scan
3. Use **Demo Cloud Model (Unapproved)** (`DEMO_CLOUD_UNAPPROVED`)
4. Validate → `decision: warn`
5. Acknowledge warning with note
6. Start execution

### 6.5 Blocked external execution

**Goal:** Passwords/API keys + external model → block.

1. Upload `blocked_passwords.csv`
2. Complete scan (password, api_key findings)
3. Use **Demo External API (GPT)** (`DEMO_EXTERNAL_API`)
4. Validate → `decision: block`, `can_start: false`
5. Start attempt → rejected (403/400)

### 6.6 Auditor review session

```
1. Log in as auditor
2. Review org-wide reports           → Reports
3. Inspect execution decisions       → Executions
4. Review GAIRA ROAIA inventory    → GAIRA
5. Check gap posture & open threats  → Gaps, Threats
6. Export audit trail                → Audit logs
```

### 6.7 API-only GAIRA assessment

For automation or integrations without UI:

```http
POST   /api/v1/gaira/applications
POST   /api/v1/gaira/applications/{id}/assessments   { "assessment_type": "ai_risk_levels" }
PATCH  /api/v1/gaira/assessments/{id}/answers        { "merge": true, "answers": { ... } }
POST   /api/v1/gaira/assessments/{id}/compute
POST   /api/v1/gaira/assessments/{id}/submit         { "overall_risk_level": "medium", ... }
GET    /api/v1/gaira/roaia
```

All requests require `Authorization: Bearer <token>`.

---

## 7. API quick reference

Base URL: `http://localhost:8000/api/v1`  
Interactive docs: `http://localhost:8000/docs`  
Health: `http://localhost:8000/health`

| Module | Key endpoints |
|--------|---------------|
| **Auth** | `POST /auth/signup`, `/login`, `/refresh`, `/logout`, `GET /me` |
| **Files** | `POST /files/upload`, `GET /files`, `DELETE /files/{id}` |
| **Scans** | `POST /scans`, `GET /scans/{id}`, `GET /scans/{id}/recommendations` |
| **Scoring** | `GET /scoring/config` |
| **Reports** | `POST /reports`, `GET /reports/{id}/export?format=json\|pdf` |
| **Rules** | `GET/POST/PATCH /rules`, `POST /rules/{id}/enable\|disable` |
| **Policies** | `GET/POST/PATCH /policies`, `POST /policies/evaluate` |
| **Models** | `GET/POST/PATCH /compliance-models`, `POST /compliance-models/sync-gptlab`, `POST /compliance-models/validate` |
| **Executions** | `POST /executions/validate`, `GET /executions/{id}/status`, `POST /.../acknowledge-warning`, `POST /.../start` |
| **GAIRA** | `GET /gaira/framework`, `POST /gaira/applications`, `POST /gaira/assessments/{id}/compute\|submit` |
| **Monitoring** | `GET /monitoring/sessions`, `POST /monitoring/prompts/scan`, `POST /monitoring/outputs/scan` |
| **Guard** | `POST /monitoring/guard/executions/{id}/prompt\|output` |
| **Notifications** | `GET /notifications`, `GET /notifications/stream/alerts` |
| **Analytics** | `GET /analytics/dashboard`, `/trends/*`, `/high-risk/*` |
| **Gaps** | `POST /gaps/analyze`, `GET /gaps/dashboard`, `POST /gaps/{id}/acknowledge\|resolve` |
| **Threats** | `POST /threats/detect`, `GET /threats/dashboard`, `POST /threats/{id}/investigate\|resolve` |
| **Audit** | `GET /audit-logs` |

---

## 8. Local setup & operations

### Prerequisites

- Python 3.12+
- Node.js (for frontend)
- Docker (PostgreSQL)

### Start commands

```bash
# 1. Database
docker compose up -d postgres

# 2. Backend (first time)
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head

# 3. Backend (run)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. Frontend (first time)
cd frontend
npm install
copy .env.local.example .env.local

# 5. Frontend (run)
npm run dev
```

| Service | URL |
|---------|-----|
| App | http://localhost:3000 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

### Key environment variables

| Variable | Purpose |
|----------|---------|
| `JWT_SECRET_KEY` | Required for auth |
| `DATABASE_URL` | PostgreSQL connection |
| `STORAGE_LOCAL_PATH` | Upload/report storage (default `./uploads`) |
| `GPTLAB_API_KEY` | GPT-Lab model sync |
| `SCORE_*` | Scoring thresholds and weights |
| `MONITORING_OUTBOX_WORKER_ENABLED` | Background event processing |
| `SMTP_ENABLED`, `SMTP_*` | Email notifications |

### Run tests

```bash
cd backend
pytest                                    # all tests
pytest -m integration tests/test_sprint2_e2e_workflow.py -v
pytest -m sprint3 tests/test_sprint3_integration.py -v
```

Full command reference: [`Running_commands.md`](../Running_commands.md)

---

## 9. Status & decision vocabulary

### UI color legend

| Color | Meaning | Examples |
|-------|---------|----------|
| Green | Safe / done | `compliant`, `allow`, `completed`, `resolved` |
| Amber | Caution / pending | `risky`, `warn`, `pending_*`, `investigating` |
| Red | Blocked / failed | `non_compliant`, `block`, `critical`, `interrupted` |
| Blue | In progress | `validating`, `scanning`, `queued` |
| Grey | Inactive | `disabled`, `cancelled`, `draft` |

### Scan vs execution vs GAIRA

| Concept | Values | Layer |
|---------|--------|-------|
| **Compliance status** (file) | `compliant`, `risky`, `non_compliant` | Scan |
| **Decision** (execution) | `allow`, `warn`, `block` | Execution |
| **Guard action** (runtime) | `allowed`, `warned`, `blocked`, `interrupted` | Live monitoring |
| **GAIRA risk level** | `insignificant` … `very_high` | Governance |

---

## 10. Glossary

| Term | Definition |
|------|------------|
| **Finding** | Single sensitive item detected in a scan |
| **Recommendation** | Remediation tied to a finding |
| **Rule** | Atomic compliance check with action |
| **Policy** | Named bundle of rules |
| **Model registry** | Catalog of approved AI endpoints (metadata only) |
| **Execution** | Request to run a dataset through a model with guard |
| **Guard** | Runtime enforcement on prompts/outputs |
| **Session** | Monitoring window for one execution |
| **Outbox** | Reliable event delivery queue |
| **Posture score** | 0–100 gap-analysis health score |
| **GAIRA** | Generative AI Risk Assessment framework |
| **ROAIA** | Records of AI Activities inventory |
| **Assessment** | One GAIRA module run for an application |
| **2nd line** | Legal/DPO/CISO review of flagged GAIRA answers |

---

## 11. Document index

| Document | Audience | Content |
|----------|----------|---------|
| **This file** | Everyone | Use cases, workflows, API map |
| [`USER_GUIDE.md`](../USER_GUIDE.md) | End users | Step-by-step UI walkthrough |
| [`GAIRA_USER_GUIDE.md`](../GAIRA_USER_GUIDE.md) | Governance leads | GAIRA scoring, API, ROAIA |
| [`PLATFORM_REFERENCE.md`](PLATFORM_REFERENCE.md) | Developers | Architecture, schema, sprint history |
| [`SPRINT2_WORKFLOWS.md`](SPRINT2_WORKFLOWS.md) | QA / devs | Execution scenario tests |
| [`SPRINT2_TECHNICAL.md`](SPRINT2_TECHNICAL.md) | Developers | Rules, policies, orchestrator |
| [`backend/docs/SPRINT3_TECHNICAL.md`](../backend/docs/SPRINT3_TECHNICAL.md) | Developers | Monitoring, guard, outbox |
| [`COMPLIANCE_QA.md`](COMPLIANCE_QA.md) | Supervisors | Plain-language compliance FAQ |
| [`Running_commands.md`](../Running_commands.md) | Developers | Local run commands |
| `http://localhost:8000/docs` | Integrators | Live OpenAPI reference |

---

*Last updated: June 2026 — reflects Sprint 1–4 capabilities (files through GAIRA).*
