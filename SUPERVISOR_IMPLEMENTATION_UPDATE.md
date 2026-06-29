# Security Compliance — Implementation Update by Section

**Purpose:** Summary of what has been built in each area of the left navigation panel, for supervisor review and demo walkthrough.

**Product name in UI:** Security Compliance (GPT-LAB SANDBOX)  

---

## Executive summary

Security Compliance is a full-stack compliance platform (Next.js dashboard + FastAPI backend + PostgreSQL) that helps teams govern AI projects and operational data use. Work is organized across three delivery phases:

| Phase | Focus | Status |
|-------|--------|--------|
| **Sprint 1** | File upload, dataset scanning, risk scoring, reports | Implemented |
| **Sprint 2** | RBAC, rules/policies, model registry, execution validation, audit logs | Implemented |
| **Sprint 3** | Live monitoring guard, analytics, gap analysis, threat detection, notifications (API) | Implemented |

The left sidebar groups pages into **Platform**, **Compliance**, **Governance**, **Monitoring**, and **Audit**. Each page is permission-gated for **User**, **Admin**, or **Auditor** roles.

---

## Platform

### Overview (`/`)

**What was built**

- Landing dashboard after login with role-aware data loading.
- Summary cards: uploaded files, total scans, average risk score, report count.
- Compliance breakdown chart (compliant / risky / non-compliant scans).
- Recent scans list with risk score and status badges; links to scan detail.
- Optional governance snapshot: policy count, rule count, execution count, model count (shown when the user has access).
- Framework compliance preview (NIST AI RMF, GAIRA, internal guardrails) with open-issue counts and link to full **Compliance posture** page.

**Who can see it:** All authenticated users (widgets adapt to permissions).

---

### Files (`/files`)

**What was built**

- Upload datasets via file picker or drag-and-drop (CSV, JSON, TXT; size limits enforced by backend).
- Paginated file list with name, size, upload date, and row/column metadata.
- Delete files.
- Quick **Run scan** action from the file row to start a compliance scan without leaving the page.

**Backend:** User-scoped storage, metadata extraction, REST upload/list/delete APIs.

**Who can see it:** Users and Admins with `file:read` / `file:upload`.

---

### Scans (`/scans`, `/scans/[id]`)

**What was built**

**List page**

- Scan history table with file name, risk score, compliance status, and date.
- Link to each scan’s detail view.

**Detail page**

- Risk score gauge and executive summary.
- Score breakdown by finding category.
- Findings grouped by severity (email, phone, password, API key, sensitive column names, etc.).
- Recommendations grouped by priority (anonymize, mask, remove column, rotate secret, etc.).
- **Generate report** and download JSON/PDF from the scan detail page.

**Scoring:** Risk score 0–100 maps to `compliant`, `risky`, or `non_compliant`; critical findings can force non-compliant status.

**Who can see it:** Users and Admins with `scan:read` / `scan:run`.

---

### Reports (`/reports`)

**What was built**

- List of all generated compliance reports.
- Download each report as **JSON** (system integration) or **PDF** (human review).
- Reports are created from completed scans (primary path: scan detail → Generate report).

**Backend:** ReportLab PDF generation, structured JSON summary.

**Who can see it:** Users see own reports; Admins and Auditors can see organization-wide reports where permitted.

---

## Compliance

### Executions (`/executions`, `/executions/validate`, `/executions/[id]`)

**What was built**

**List page**

- Execution validation history with status and decision badges.
- Filters: all, blocked, warning, and individual statuses.
- **Request validation** button (Users/Admins) linking to the validation wizard.

**Validation wizard (`/executions/validate`)**

- Select file + completed scan + approved compliance model.
- Pre-execution evaluation runs rules, active policies, and model risk checks.
- Outcome: **allow**, **warn**, or **block** with blocking reasons and triggered rules.

**Detail page**

- Full execution record: decision, status, model, scan context, policy violations.
- **Acknowledge warning** flow when decision is `warn`.
- **Start execution** when allowed (enforcement gate; no external job runner).
- Status lifecycle: pending → allowed / warning / blocked → started → completed / interrupted.

**Backend (Sprint 3):** Live compliance guard APIs monitor prompts and outputs during execution; events feed notifications, threats, and audit logs. *Note: prompt/output submission UI is API-driven; the dashboard focuses on validation and status, not a live chat-style runner.*

**Who can see it:** Users request runs; Admins see all executions; Auditors have read-only org-wide view.

---

### Models (`/models`, `/models/[id]`, `/models/validations/[id]`)

**What was built**

- Compliance model registry (metadata only — not model weights).
- List with type filter (local, external API, cloud-hosted, etc.).
- Model profile: provider, deployment type, approval status, whether data leaves the platform.
- **Dry-run validation:** test a scan + model combination and see allow/warn/block without creating an execution.
- **Admin — Register model** manually.
- **Admin — Sync from GPT-Lab** when `GPTLAB_API_KEY` is configured.
- Demo models seeded for workflow testing (`DEMO_LOCAL_LLM`, `DEMO_CLOUD_UNAPPROVED`, `DEMO_EXTERNAL_API`).

**Who can see it:** All users with `scan:read`; model registration/sync requires Admin (`policy:manage`).

---

## Governance

### Registrations (`/users`)

**What was built**

- Admin-only queue for pending user signups.
- Approve with role assignment: **User**, **Admin**, or **Auditor**.
- Reject registration requests.
- Sidebar badge on **Registrations** showing pending count (updates after approve/reject).

**Workflow:** New signups default to pending until an Admin approves them.

**Who can see it:** Admins with `user:manage` only.

---

### Compliance posture (`/compliance`)

**What was built**

- Unified view of alignment across three tracked frameworks:
  - **NIST AI RMF**
  - **GAIRA governance**
  - **Internal guardrails** (platform rules, policies, encryption, MFA-style checks)
- Summary stats: frameworks tracked, compliant / partial counts, total open issues.
- Per-framework cards with alignment score, status badge, and expandable open issues.
- Each issue shows severity, control IDs, remediation steps, and link to related detail page.
- Disclaimer clarifies this is operational alignment evidence, not external certification.

**Data sources:** Aggregates open gaps, GAIRA assessment state, and NIST control profile.

**Who can see it:** Users/Admins/Auditors with gap or GAIRA read permissions.

---

### NIST AI RMF (`/nist-ai-rmf`)

**What was built**

- Operational mapping to NIST AI Risk Management Framework functions: **Govern · Map · Measure · Manage**.
- Current profile summary: overall alignment score, counts of controls met / partial / not met.
- Filterable control table by function and status.
- Per-control detail: status, evidence notes, linked open gaps, remediation guidance.
- Disclaimer that this reflects configured platform state, not a formal NIST audit.

**Who can see it:** Same permissions as Compliance posture.

---

### GAIRA (`/gaira`, `/gaira/applications/[id]`, `/gaira/assessments/[id]`)

**What was built**

**ROAIA inventory (main GAIRA page)**

- Paginated table of registered AI applications.
- Columns: name, owner, department, GAIRA status, risk level, linked model.
- **Register application** form (name, owner, purpose, optional compliance model link).

**Application detail**

- Application profile and assessment history.
- **Start assessment** — pick module type and optional linked scan for auto-prefill.
- Supported modules: AI Risk Levels triage, GAIRA Light, GAIRA Comprehensive, AI Act check, Compliance check.

**Assessment wizard**

- Step-based questionnaire UI loaded from GAIRA framework definition.
- Save answers per step; **Compute** for machine-generated recommendations.
- **Submit** with overall risk level and proceed decision (proceed / proceed with conditions / do not proceed).
- Read-only mode for Auditors and submitted assessments.

**Still not implemented (known gaps)**

- Automatic execution gate blocking runs without completed GAIRA.
- Gap detector for missing/expired assessments.
- Full GAIRA Comprehensive 4×4 matrix auto-scoring.
- Dedicated GAIRA entries in audit logs.

**Who can see it:** Users/Admins manage assessments; Auditors read-only org-wide.

---

### Policies (`/policies`, `/policies/[id]`)

**What was built**

- List policies with status filter (draft, active, archived).
- Create policy: name, type (data, model, execution, security), description, priority, score thresholds (`block_below`, `warn_below`).
- Policy detail: view metadata, attached rules, activate/deactivate/archive.
- **Admin** can attach/detach rules and change status.
- **All users** can browse active policies to understand what is enforced at execution time.

**Who can see it:** Browse with `scan:read`; full CRUD with `policy:manage` (Admin).

---

### Rules (`/rules`)

**What was built**

- List rules with category and enabled/disabled filters.
- Rule detail in table: code, name, category, severity, action (allow/warn/block), priority, enabled flag.
- **Admin — Create rule** with JSON condition, severity, action, priority.
- **Enable / disable** rules without deleting.
- Seeded examples: email detected → warn; password/API key + external model → block.

**Evaluation:** Rules fire during execution validation and contribute to scan-time context.

**Who can see it:** Browse with `scan:read`; manage with `rule:manage` (Admin).

---

## Monitoring

### Analytics (`/analytics`)

**What was built**

- Dashboard with 1 / 7 / 30-day filters and severity/granularity options.
- Summary metrics: total scans, blocked vs allowed executions, average risk score, unread notifications count.
- Charts: block rate over time, alert rate, violations by category (bar/line/pie).
- **High-risk users** and **high-risk models** leaderboards.
- **Real-time violations** widget with periodic refresh (30s polling).
- Org-wide view for Admin/Auditor (`analytics:read_all`); Users see own-scoped data.

**Who can see it:** All roles with analytics permissions (scoped by role).

---

### Gap analysis (`/gaps`)

**What was built**

- Posture score and open gaps grouped by severity.
- Tabs: **Open gaps** and **History** (resolved items).
- Filters by severity and framework (NIST, GAIRA, internal).
- Per-gap actions: **Acknowledge** (seen, not fixed) and **Resolve** (moved to history).
- **Admin — Run analysis** recomputes gaps from current platform state (encryption, MFA policy, inactive rules, GAIRA gaps, etc.).
- Remediation text and framework control mapping on each gap.

**Who can see it:** All with `gap:read`; run analysis requires `gap:analyze` (Admin).

---

### Threat detection (`/threats`)

**What was built**

- Threat dashboard: open threats by severity, recent security events.
- Threat types: repeated guard blocks, prompt-injection patterns, output leakage, unusual violation rates, suspicious sessions.
- **Investigate** and **Resolve** actions (Admin).
- **Admin — Run detection** batch scan from recent events.
- Real-time handler on block/violation domain events (background outbox worker).
- User behavior analysis table for Admin/Auditor org-wide view.
- Auto-refresh every 30 seconds.

**Who can see it:** All with `threat:read`; manage/detect requires `threat:manage` (Admin).

---

## Audit

### Audit logs (`/audit`)

**What was built**

- Searchable, paginated activity trail.
- Filters: free-text search, action type, severity, sort order.
- Columns: timestamp, actor email, action, resource type, severity, details.
- Logged events include: authentication, scans, execution decisions, guard actions, policy/rule changes, threat updates, and related governance actions.

**Who can see it:** Admin and Auditor with `audit:read` (read-only for Auditors).

---

## Cross-cutting capabilities (not separate sidebar items)

### Authentication & access control

- **Login** and **signup** with JWT access + refresh tokens.
- Password policy: minimum 8 characters, upper, lower, digit.
- **RBAC:** three roles (User, Admin, Auditor) with fine-grained permissions.
- Sidebar and pages hidden when the user lacks permission; `RequirePermission` guards on sensitive routes.
- Role shown at bottom of sidebar; sign-out from header.

### Notifications (backend)

- In-app notification APIs and SSE alert stream are implemented on the backend.
- Triggers: guard blocks, rule triggers, threats, high/critical gaps.
- Optional email when SMTP is configured.
- *Dashboard gap:* no dedicated notification bell/inbox UI in the header yet; unread count appears on the Analytics dashboard.

### Live monitoring guard (backend)

- Prompt and output scanning during execution (PII, secrets, injection, jailbreak).
- Compliance guard can warn, block, or interrupt runs.
- Domain events → outbox worker → notifications, threats, audit logs.
- Primarily exercised via API and E2E tests; not a full interactive “chat with model” UI in the dashboard.

---

## Suggested demo flow for supervisor

1. **Overview** — show health metrics and framework snapshot.
2. **Files → Scans** — upload sample CSV, run scan, review findings.
3. **Reports** — download PDF evidence.
4. **Models → Executions** — validate file+scan+model, show allow/warn/block.
5. **Governance** — GAIRA application + assessment; Compliance posture + NIST AI RMF alignment.
6. **Policies & Rules** — show how enforcement is configured (Admin).
7. **Monitoring** — Analytics trends, run Gap analysis, review Threats.
8. **Audit logs** — forensic trail (Auditor view).

---

## Document info

| Item | Value |
|------|--------|
| Generated for | Supervisor presentation |
| Sidebar source | `frontend/src/components/layout/Sidebar.tsx` |
| Technical references | [`docs/PROJECT_USE_CASES_AND_WORKFLOWS.md`](docs/PROJECT_USE_CASES_AND_WORKFLOWS.md), [`docs/SPRINT2_TECHNICAL.md`](docs/SPRINT2_TECHNICAL.md), [`backend/docs/SPRINT3_TECHNICAL.md`](backend/docs/SPRINT3_TECHNICAL.md) |
