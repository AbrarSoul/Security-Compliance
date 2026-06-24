# ComplianceGuard — User Guide

A practical walkthrough for new users. Read top-to-bottom the first time; later you can jump to a section.

---

## 1. What is ComplianceGuard?

ComplianceGuard helps security & compliance teams answer one question:

> **"Is this dataset (or this AI prompt / output) safe to use?"**

It scans your data for sensitive content (PII, secrets, restricted fields), scores the risk, decides if it can be used with a specific AI model, monitors the actual prompts & outputs in real time, alerts you when something looks wrong, and keeps an audit trail of everything.

You will move through four logical stages (GAIRA is under **Governance → GAIRA** in the sidebar):

```
   0. AI governance (GAIRA)   1. Data preparation        2. Execution governance     3. Live monitoring
 ┌─────────────────────────┐   ┌──────────────────────┐   ┌────────────────────────┐   ┌──────────────────────────────┐
 │ Register application    │   │ Upload → Scan → Fix  │ → │ Validate → Acknowledge │ → │ Monitor → Alerts → Analytics │
 │ Triage → Assess → ROAIA │   │            ↓ Report  │   │            Execute     │   │  Gaps → Threats → Audit      │
 └─────────────────────────┘   └──────────────────────┘   └────────────────────────┘   └──────────────────────────────┘
```

---

## 2. Roles & what you can do

When you sign up you become a **User** by default. An admin can promote you.

| Role | Typical purpose | Can do |
|------|-----------------|--------|
| **User** | Day-to-day analyst | Upload files, run scans & reports, request executions, **register and complete GAIRA assessments**, view your own analytics/gaps/threats |
| **Admin** | Platform owner | Everything users can + manage policies & rules, **sync GPT-Lab models**, **run gap analysis**, **run threat detection**, manage notifications platform-wide |
| **Auditor** | Compliance officer | Read-only access to **all** users' scans, executions, gaps, threats, **GAIRA records**, audit logs |

If a button is missing or you see "no permission", your role does not grant that action — ask an admin.

---

## 3. First-time setup (2 minutes)

1. Open the app (`http://localhost:3000`).
2. Click **Sign up**, use an email + a password (≥ 8 chars, upper, lower, digit).
3. You are signed in automatically — you land on the **Overview** dashboard.

If your account needs admin or auditor access, ask the admin to assign your role; then **sign out and sign back in** so your token picks up the new permissions.

Your current role is shown at the **bottom-left of the sidebar** (below your email), e.g. `user`, `admin`, or `auditor`.

---

## 4. The dashboard, section by section

The sidebar groups pages as **Platform**, **Compliance**, **Governance**, **Monitoring**, and **Audit**. Your role appears at the bottom-left (below your email).

### 4.1 Overview
**Why:** A quick health check.
**What you see:** Totals for scans, executions, reports; a compliance breakdown (compliant / risky / non-compliant); most recent scans.
**When to use:** Every login — confirms nothing alarming happened overnight.

### 4.2 Files
**Why:** ComplianceGuard scans *files*. You must upload one before anything else.
**What to do:**
1. Click **Upload**, choose a `.csv`, `.json`, or `.txt` file (≤ 50 MB by default).
2. Wait for the metadata extraction (row count, schema preview).
3. The file now appears in the list; you can delete it anytime.

> The system stores files locally under `STORAGE_LOCAL_PATH`. No third-party upload.

### 4.3 Scans
**Why:** Detects sensitive content in a file: emails, phone numbers, passwords, API keys, names, sensitive column names.
**What to do:**
1. Open **Scans**, click **New scan**, pick a file.
2. Open the scan detail to see:
   - **Risk score** (0 – 100, low = green, medium = amber, high = red)
   - **Compliance status:** `compliant` / `risky` / `non_compliant`
   - **Findings** (each with severity)
   - **Recommendations** (e.g. mask password column, rotate secret, restrict access)

> A *critical* finding can force a `non_compliant` verdict even if the score is low. Treat critical findings as blockers.

### 4.4 Reports
**Why:** Share scan results outside the app.
**What to do:**
1. From the scan detail (or **Reports** page) click **Generate report**.
2. Download **JSON** for systems, **PDF** for humans / auditors.

### 4.5 Models
**Why:** You can only use an AI model that the platform knows. The **Models** page is a **governance registry** — it stores metadata about which AI endpoints your organization allows (provider, deployment, approval state). It does **not** host or run model weights.

**What you see in the table:**

| Column | Meaning |
|--------|---------|
| **Name** | Human-readable label (click for full profile) |
| **Code** | Stable internal ID (e.g. `GPTLAB_LLAMA3_1_8B`) — used in APIs and audit logs |
| **Provider** | Who runs the model (e.g. GPT-Lab (TUNI), OpenAI, Internal) |
| **Deployment** | **Local** = data stays in your governed environment; **External** = data is sent to another system |
| **Approved** | `Yes` = compliance has signed off; `No` = registered but not cleared for general use |
| **Active** | `Yes` = appears in execution/validation dropdowns |

**Key fields when registering manually (admin):**

- **Code** — unique short identifier (no spaces). Example: `GPTLAB_LLAMA3_1_8B`. Synced models get codes automatically.
- **Data leaves platform** — `Yes` if prompts/data are sent outside ComplianceGuard (e.g. remote GPT-Lab API). `No` for truly on-prem inference.
- **Pre-approved** — whether the model is on the org allowlist (`is_approved`).

**What to do:**

1. Browse the list to see what's approved and active.
2. Click a model for its full risk profile (endpoint, retention, logging).
3. Use **Run validation** to dry-run **scan + model** — get `allow` / `warn` / `block` before execution.
4. **Admins:** click **Sync from GPT-Lab** to pull chat models from your configured GPU farm into the registry (requires `GPTLAB_API_KEY` in backend `.env`). Embedding-only models are skipped. Demo seed models can be deactivated on sync.
5. **Admins:** use **Register model** to add endpoints manually when not using GPT-Lab sync.

> The two demo rows (`Demo Local LLM`, `Demo External API`) are placeholders for workflow demos. Replace them with real entries (sync or manual register) for production use.

Registered models also appear under **Executions → Validate** when requesting an execution.

### 4.6 Executions
**Why:** This is where the platform decides **"can I actually run this dataset through this model?"** before any prompt is sent.

**Step-by-step workflow:**

```
1. Request validation:  Files + Scan + Model → Decision (allow / warn / block)
2. If "warn":           Acknowledge the warning explicitly
3. Start execution:     Runs prompts/outputs through the guard
4. Live monitoring:     Each prompt & output is scanned; risky ones interrupt
5. Result:              completed | interrupted | blocked
```

**Common statuses you will see:**

| Status | Meaning |
|--------|---------|
| `pending_validation` | Waiting on the system |
| `allowed` | Safe to start |
| `warning_pending_acknowledgement` | Risky but allowed if you confirm |
| `approved_after_warning` | You acknowledged; safe to start |
| `blocked` | Cannot be started or continued |
| `started` | Currently running |
| `interrupted` | Guard stopped a running execution |
| `completed` | Finished successfully |

Open any execution to see its prompts, outputs, guard actions, and reasons.

### 4.7 Policies & Rules (governance)
**Why:** They define the compliance logic that scans and executions are judged against. **Admins manage these.**

- **Rules:** Atomic checks (e.g. "if API key detected → block"). Each rule has a severity, action (`allow`/`warn`/`block`), and priority.
- **Policies:** Bundles of rules tied to standards (GDPR, HIPAA, …). A policy is evaluated as a whole.

**Most users:** browse to see what's enforced. **Admins:** create/edit, enable/disable, adjust priorities.

### 4.8 GAIRA (AI risk assessment)
**Why:** Before you deploy an AI use case, you need a structured **governance** assessment — not just a dataset scan. **GAIRA** (Generative AI Risk Assessment) answers:

> **"Should we build or deploy this AI application, and at what risk level?"**

That is separate from scan/execution checks, which answer:

> **"Is this dataset safe to run on this model right now?"**

**Where:** **Governance → GAIRA** in the sidebar.

**Who:**

| Role | GAIRA access |
|------|--------------|
| **User** | Register applications, start assessments, save answers, compute, submit |
| **Admin** | Same as user |
| **Auditor** | Read-only — review submitted assessments and ROAIA inventory |

**UI workflow:**

```
1. Register application     → GAIRA → Register application
2. Start assessment         → Application detail → Start assessment
3. Answer questions         → Step tabs, Yes/No or text → Save answers
4. Compute recommendations  → Shows suggested risk level & next module
5. Submit                   → Sets overall risk, proceed decision, comments
6. Verify ROAIA             → GAIRA inventory shows gaira_status: done, risk level
```

**Recommended first assessment:** **AI Risk Levels (triage)** — a short questionnaire that recommends **GAIRA Light** or **GAIRA Comprehensive** based on your answers.

**Tips:**

- Link a **compliance model** when registering the application (prefills provider, data-leaves-platform, etc.).
- Link a **scan** when starting an assessment (prefills personal-data indicators).
- Prefilled answers show a **Prefilled: …** badge — always review; the application owner remains accountable.
- If **Compute** flags **second-line review required**, add a reviewer email on flagged Step 4 answers before submit.

**ROAIA inventory** (main GAIRA page) lists all registered AI applications with GAIRA status, risk level, owner, and provider.

> Deeper detail (scoring rules, API reference, glossary): **[`GAIRA_USER_GUIDE.md`](GAIRA_USER_GUIDE.md)**

### 4.9 Analytics
**Why:** Trends over days/weeks — not the raw events.
**What you see:**
- Total scans, blocked / allowed counts, average risk score
- Time-series charts (block rate, alert rate, violations by category)
- High-risk users / models leaderboard
- Real-time violation widget

**Filters:** time window (1 / 7 / 30 days), optional user / model filters.
**When to use:** Weekly reviews, before an audit, to spot abnormal traffic.

### 4.10 Gap analysis
**Why:** Reads your current platform state and tells you **what's missing** to be compliant: e.g. "encryption at rest disabled", "no MFA policy", "no rule for password masking".
**Workflow:**
1. **Open gaps tab** — current unresolved gaps grouped by severity.
2. Each gap shows:
   - Severity badge (`critical`, `high`, `medium`, `low`)
   - Category & type
   - **Remediation** — what to actually do to close it
   - Detected date, score
3. Admin actions:
   - **Acknowledge** — "I see it, not fixing yet" (keeps showing).
   - **Resolve** — "fixed, close it" (moves to history).
4. **Run analysis** (admin only) — recomputes the gap list against the latest state.
5. **Posture score** at the top: a single number (higher = healthier).

**Tip:** Treat `critical` gaps as production blockers; `medium`/`low` can usually wait for the next sprint.

### 4.11 Threat detection
**Why:** Real-time security monitoring on top of the compliance layer.
**What it detects:**
- Repeated guard blocks from the same user (brute force probing)
- Prompt-injection patterns
- Output leakage (secrets, PII in responses)
- Unusual policy violation rates per user / model
- Suspicious behavior in monitoring sessions

**Workflow:**
1. **Dashboard** — open threats by severity + recent security event log.
2. Click a threat to see the events that triggered it, affected user / model, suggested response.
3. Admin actions:
   - **Investigate** — flags it as being worked on.
   - **Resolve** — closes the threat.
4. **Run detection** (admin) — recomputes threats from recent events.

### 4.12 Audit logs
**Why:** Immutable record of who did what — required for compliance and forensics.
**What you see:** Every login, scan, execution decision, guard action, policy change, threat update, with actor, target, IP, timestamp.
**Who has access:** Anyone with `audit:read` (typically admins + auditors).

### 4.13 Notifications
**Why:** You don't have to refresh — the system pushes alerts.
**How:** Bell icon (or `/notifications` if surfaced) shows unread count. Alerts fire when:
- A guard blocks one of *your* prompts/outputs
- A rule triggers on one of your scans
- A threat affects you
- A gap of `high`/`critical` severity is detected

**Preferences:** You can disable email or in-app channels per category (suspicious activity, policy violations, etc.).

---

## 5. The end-to-end happy path (typical day)

**New AI project (governance first):**

```
1. Register AI application     → GAIRA → Register application
2. Run AI Risk Levels triage   → Start assessment → answer → compute → submit
3. Complete GAIRA Light/Comp.  → As recommended by triage
4. (Admin) Sync real models    → Models → Sync from GPT-Lab (or register manually)
```

**Operational compliance (dataset + execution):**

```
1. Upload dataset              → Files
2. Run scan                    → Scans   (fix any critical findings first)
3. Generate report             → Reports (optional, for audit trail)
4. Validate execution          → Executions  (Dataset + Scan + Model)
5. Acknowledge warning?        → Yes / No
6. Start execution             → Live guard runs prompt + output checks
7. Watch notifications         → Real-time alerts on blocks/warnings
8. Check analytics weekly      → Analytics
9. Run gap analysis monthly    → Gaps (admin)
10. Review threats             → Threats / Audit logs
```

> GAIRA and execution validation are **separate gates** today. A completed GAIRA assessment does not automatically block executions — treat `gaira_status: done` as a policy requirement before production use.

---

## 6. Flag color legend

The UI is dark-themed with lime accents for branding. **Status flags** keep semantic colors so meaning is obvious at a glance:

| Color | Meaning | Common labels |
|-------|---------|---------------|
| 🟢 Green | Good / safe / done | `compliant`, `allow`, `allowed`, `low`, `done`, `submitted`, `insignificant`, `started`, `running`, `completed`, `enabled`, `active`, `resolved`, `acknowledged`, `approved` |
| 🟠 Amber | Caution / pending | `risky`, `warn`, `warning`, `medium`, `pending_*`, `in_progress`, `investigating`, `review`, `draft` |
| 🔴 Red | Bad / blocked / failed | `non_compliant`, `block`, `blocked`, `interrupted`, `critical`, `high`, `failed`, `error`, `denied` |
| 🔵 Blue | Informational / in-progress | `info`, `queued`, `validating`, `validated`, `scanning` |
| ⚪ Grey | Inactive / N/A | `disabled`, `inactive`, `draft`, `cancelled`, `unknown` |

Risk score colors follow the same scale:
- **0 – 30** green (low)
- **31 – 60** amber (medium)
- **61 – 100** red (high)

---

## 7. Common pitfalls

| Problem | Likely cause | Fix |
|---------|--------------|-----|
| "No permission" banner on a page | Role doesn't include the perm | Ask admin to assign role; **sign out and sign back in** |
| No **Sync from GPT-Lab** on Models | Not admin (`policy:manage`) | Ask admin to promote you; re-login |
| GPT-Lab sync fails | Missing/invalid API key or VPN | Set `GPTLAB_API_KEY` in `backend/.env`; restart backend; connect to TUNI VPN if off campus |
| Models show **External** for GPT-Lab | Data is sent to remote GPU farm | Expected — `data_leaves_platform: Yes` is correct for GPT-Lab |
| GAIRA page missing or 403 | Migration not run or stale token | Run `alembic upgrade head`; sign out and back in |
| GAIRA submit rejected | Flagged Step 4 without 2nd-line reviewer | Add `second_line_reviewer` on flagged answers in the wizard |
| Execution blocked with no obvious reason | A critical finding or a runtime rule fired | Open execution → check `blocking_reasons` and audit log |
| Notifications never arrive | Outbox worker disabled or prefs muted | Admin: confirm `MONITORING_OUTBOX_WORKER_ENABLED=true`; user: check notification preferences |
| Gap analysis says "no gaps" but you expect some | Analysis hasn't been re-run | Admin → **Run analysis** |
| Reports show old data | Generated before last scan | Generate a new report after the latest scan |
| Stuck `warning_pending_acknowledgement` | Nobody acknowledged the warning | Open the execution → **Acknowledge** to proceed, or leave it blocked |

---

## 8. Glossary

- **Finding** — a single piece of sensitive content the scanner detected (e.g. an email address in column `contact`).
- **Recommendation** — concrete remediation tied to a finding (mask / anonymize / rotate / etc.).
- **Compliance status** — the file-level verdict: `compliant` / `risky` / `non_compliant`.
- **Decision** — the execution-level verdict: `allow` / `warn` / `block`.
- **Guard action** — a live decision made during execution (`allowed`, `warned`, `blocked`, `interrupted`).
- **Outbox** — internal queue that delivers domain events to handlers (notifications, threats, analytics) reliably.
- **Posture score** — single 0-100 gap-analysis score; higher = healthier compliance posture.
- **Severity** — `critical` > `high` > `medium` > `low`.
- **Session** — a real-time monitoring window grouping prompts/outputs of one execution.
- **Model registry** — catalog of approved AI endpoints (metadata only; not model weights). See **Models**.
- **Code** — stable unique ID for a registered model (e.g. `GPTLAB_LLAMA3_1_8B`), distinct from the display name.
- **Data leaves platform** — whether using a model sends data outside the ComplianceGuard environment.
- **Pre-approved** — admin flag (`is_approved`) indicating compliance has cleared the model for use.
- **GAIRA** — Generative AI Risk Assessment framework for project-level AI governance. See [`GAIRA_USER_GUIDE.md`](GAIRA_USER_GUIDE.md).
- **ROAIA** — Records of AI Activities; inventory of registered AI applications in ComplianceGuard (**GAIRA** page).
- **Assessment** — one run of a GAIRA module (e.g. AI Risk Levels, GAIRA Light) for an application.

---

## 9. Where to go next

- New developer? Read [`backend/README.md`](backend/README.md) for setup and API endpoints.
- **Running locally?** See [`Running_commands.md`](Running_commands.md).
- **GAIRA / AI risk assessment (detailed)?** Read [`GAIRA_USER_GUIDE.md`](GAIRA_USER_GUIDE.md).
- **GPT-Lab local models?** See [`Local Models/Using_models.md`](Local%20Models/Using_models.md).
- Working on monitoring / guard / analytics? Read [`backend/docs/SPRINT3_TECHNICAL.md`](backend/docs/SPRINT3_TECHNICAL.md).
- API reference: `http://localhost:8000/docs` (when the backend is running).

Welcome aboard.
