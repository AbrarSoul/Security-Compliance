# Security Compliance — System Overview

A plain-language guide to what the **Security Compliance** platform (GPT-LAB SANDBOX) is for, how work flows through it today, and what each section does — with simple examples.

**Related docs:** [`USER_GUIDE.md`](USER_GUIDE.md) · [`SUPERVISOR_IMPLEMENTATION_UPDATE.md`](SUPERVISOR_IMPLEMENTATION_UPDATE.md) · [`Running_commands.md`](Running_commands.md)

---

## 1. What is this system the compliance for?

**Security Compliance** helps organizations govern **AI projects** and **operational use of data with AI models**. It is not a certificate for ISO, SOC 2, or the EU AI Act. Instead, it checks your work against **rules and policies you configure** and maps gaps to familiar frameworks so you know what to fix.

The system answers two related questions:

| Question | Plain meaning | Main areas |
|----------|---------------|------------|
| **Should we build or deploy this AI application?** | Is the *project* acceptable from a governance and risk perspective? | GAIRA, Compliance posture, NIST AI RMF |
| **Is this data safe to use with this AI model right now?** | Can we *run* this dataset or prompt through a specific model today? | Files, Scans, Models, Executions |

### What “compliant” means here

When the platform says something is **compliant**, it means **compliant with the rules and policies configured in this platform** — backed by evidence (findings, triggered rules, audit logs). Admins tune those rules to match organizational requirements.

### Frameworks the platform aligns with (operationally)

| Framework | What it represents |
|-----------|-------------------|
| **NIST AI RMF** | Alignment with the [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework) — Govern, Map, Measure, Manage |
| **GAIRA governance** | Structured AI application risk assessments and ROAIA (Records of AI Activities) inventory |
| **Internal guardrails** | Your own rules, policies, approved models, encryption settings, and monitoring |
| **EU AI Act (via GAIRA)** | Questionnaire-based check for AI Act applicability — not legal certification |

### What the scanner looks for (data compliance)

| Type | Examples |
|------|----------|
| Email | Email addresses in datasets |
| Phone | Phone number patterns |
| Password | Password-like values or column names |
| API key | Secret key patterns |
| Sensitive fields | Column names like `ssn`, `credit_card`, `password` |

### Two checkpoints (simple analogy)

Think of airport security with two gates:

1. **Project gate (GAIRA)** — Before you build: *“What is this AI for? Who does it affect? How risky is it?”*
2. **Operational gate (Scans & Executions)** — Before you run data: *“Does this file contain passwords? Is this model approved? Allow, warn, or block?”*

Both matter. A project can pass GAIRA but still be blocked at execution if a file contains secrets. A clean file can still be blocked if the model is not approved.

---

## 2. Workflow up to now

Work is organized in **four stages** across three delivery sprints. All major sidebar areas are implemented.

### Delivery phases

| Phase | Focus | Status |
|-------|--------|--------|
| **Sprint 1** | File upload, dataset scanning, risk scoring, reports | Done |
| **Sprint 2** | RBAC, rules/policies, model registry, execution validation, audit logs | Done |
| **Sprint 3** | Live monitoring guard, analytics, gap analysis, threat detection, notifications (API) | Done |

### Four-stage platform lifecycle

```
 Stage 0 — AI governance          Stage 1 — Data preparation       Stage 2 — Execution check        Stage 3 — Live monitoring
 ┌──────────────────────────┐     ┌─────────────────────────┐     ┌──────────────────────────┐     ┌─────────────────────────────┐
 │ Register AI application  │     │ Upload dataset          │     │ Validate execution       │     │ Monitor prompts & outputs   │
 │ Triage → Assess → ROAIA  │  →  │ Run compliance scan     │  →  │ Acknowledge warnings     │  →  │ Analytics & trends          │
 │                          │     │ Generate report         │     │ Start execution + guard  │     │ Gap analysis & threats      │
 │                          │     │ Fix critical findings   │     │                          │     │ Audit logs & notifications  │
 └──────────────────────────┘     └─────────────────────────┘     └──────────────────────────┘     └─────────────────────────────┘
```

### End-to-end workflow (typical user journey)

#### A. Getting access

```
1. Sign up                    →  Account created (pending)
2. Admin approves             →  Governance → Registrations (assign User / Admin / Auditor)
3. Sign in                    →  Land on Overview dashboard
```

#### B. New AI project (governance first)

```
1. Register AI application    →  GAIRA → Register application
2. Run AI Risk Levels triage  →  Answer questions → Compute → Submit
3. Complete GAIRA Light or    →  As recommended by triage
   Comprehensive assessment
4. (Optional) Second-line     →  GAIRA reviews / GAIRA approvals (if flagged)
5. (Admin) Sync real models   →  Models → Sync from GPT-Lab
```

#### C. Operational compliance (dataset + execution)

```
1. Upload dataset             →  Files
2. Run scan                   →  Scans (fix critical findings first)
3. Generate report (optional) →  Reports (JSON or PDF)
4. Validate execution         →  Executions (pick file + scan + model)
5. Acknowledge warning?       →  If decision = warn
6. Start execution            →  Live guard monitors prompts and outputs
7. Watch notifications        →  Real-time alerts (backend API)
8. Check analytics weekly     →  Analytics
9. Run gap analysis monthly   →  Gap analysis (admin)
10. Review threats & audit    →  Threat detection, Audit logs
```

### How rules, policies, and frameworks connect

```
FRAMEWORKS  —  “What standards are we aligning with?”
(NIST AI RMF, GAIRA, Internal guardrails)
        │
        ▼ maps gaps & controls to
POLICIES  —  “Named bundles of rules for a purpose”
(e.g. Data Protection Policy)
        │
        ▼ contains
RULES  —  “Single if-then checks”
(e.g. If password found → block)
```

**When rules run:** during scans (risk scoring), execution validation (allow/warn/block), and live execution (guard can interrupt).

### User roles

| Role | Who | In one sentence |
|------|-----|-----------------|
| **User** | Analysts, data scientists, project owners | Upload data, scan, run executions, complete GAIRA assessments |
| **Admin** | Security lead, platform owner | Everything a User can do, plus configure rules, policies, models, and approve accounts |
| **Auditor** | Compliance officer, internal audit | Read-only org-wide view — no changes, full visibility |

---

## 3. Purpose of every section (with easy examples)

The left sidebar groups pages into **Platform**, **Compliance**, **Governance**, **Monitoring**, and **Audit**.

---

### Platform

#### Overview (`/`)

**Purpose:** Quick health check when you log in.

**What you see:** Totals for files, scans, reports; compliance breakdown (compliant / risky / non-compliant); recent scans; optional framework snapshot.

**Example:** You open the app Monday morning and see one scan turned **non-compliant** overnight — you click it to investigate before your team meeting.

---

#### Files (`/files`)

**Purpose:** Upload datasets before scanning or executing. Compliance checks run on *files*, so this is the starting point for data work.

**What you do:** Upload `.csv`, `.json`, or `.txt` (≤ 50 MB by default); view row/column metadata; delete files; start a scan from the file row.

**Example:** Maria uploads `customer_feedback.csv` containing a column with customer email addresses.

---

#### Scans (`/scans`)

**Purpose:** Detect sensitive content in uploaded data *before* using it with AI.

**What you do:** Create a new scan for a file; review risk score (0–100), compliance status, findings, and recommendations.

| Score | Status |
|-------|--------|
| 0 – 30 | Compliant |
| 31 – 60 | Risky |
| 61 – 100 | Non-compliant |

**Example:** Maria’s scan finds email addresses and marks the file **risky** with a recommendation to mask or remove the email column. She fixes the file and re-scans until acceptable.

---

#### Reports (`/reports`)

**Purpose:** Export scan results as evidence for managers, auditors, or other systems.

**What you do:** Generate a report from a scan; download **JSON** (integration) or **PDF** (human review).

**Example:** Before a quarterly review, Priya (Auditor) downloads PDF reports for all high-risk scans across the organization.

---

### Compliance

#### Executions (`/executions`)

**Purpose:** Answer *“Can I run this dataset through this model?”* — before and during AI use.

**Workflow:**

```
1. Request validation   →  Pick file + scan + model  →  Decision (allow / warn / block)
2. If "warn"            →  Acknowledge the warning explicitly
3. Start execution      →  Live guard monitors each prompt and output
4. Result               →  completed | interrupted | blocked
```

**Example outcomes:**

| Scenario | Typical result |
|----------|----------------|
| Clean internal data + approved local model | **Allow** |
| Risky data or unapproved cloud model | **Warn** (acknowledge to proceed) |
| Passwords/API keys + external model | **Block** |

**Example:** Maria picks her cleaned file, latest scan, and an approved local model → gets **allow** → starts execution; the guard watches each prompt and output.

---

#### Models (`/models`)

**Purpose:** Registry of **approved AI endpoints** (metadata only — the platform does not host model weights). Only registered, approved models appear in execution dropdowns.

**Key ideas:** Provider, deployment type (local vs external/cloud), approval status, dry-run validation.

**Example:** James (Admin) syncs models from GPT-Lab so the team can use `LLAMA3_8B` (local) but not an unapproved external API. A User dry-runs validation: risky scan + cloud model → **block**.

---

### Governance

#### Registrations (`/users`) — Admin only

**Purpose:** New users cannot sign in until an admin approves them and assigns a role.

**Example:** A new analyst signs up; James sees a badge on **Registrations**, approves them as **User**, and tells them they can sign in.

---

#### Compliance posture (`/compliance`)

**Purpose:** Single page summarizing alignment across NIST AI RMF, GAIRA governance, and internal guardrails.

**Statuses:** **Compliant (met)** · **Partial** · **Not met** — with open issues, remediation steps, and links to detail pages.

**Example:** Leadership opens Compliance posture and sees GAIRA is **partial** because two AI apps lack completed assessments — each issue shows a **Fix:** step.

---

#### NIST AI RMF (`/nist-ai-rmf`)

**Purpose:** Operational view of alignment with NIST AI RMF across four functions:

| Function | Plain meaning |
|----------|---------------|
| **Govern** | Policies, roles, and oversight |
| **Map** | AI use cases and risks identified |
| **Measure** | Risks detected and scored (scans, monitoring) |
| **Manage** | Risks responded to (blocks, gaps, remediation) |

**Example:** Control `GOVERN-1.5` shows **not met** because audit logging is disabled — the page links to the related gap and remediation.

---

#### GAIRA (`/gaira`)

**Purpose:** Structured **AI risk assessment** for applications *before* deployment — separate from dataset scanning. Maintains the **ROAIA inventory** (all registered AI apps).

**Workflow:**

```
1. Register application     →  Name, owner, purpose
2. Start assessment         →  Pick module (triage, Light, Comprehensive, AI Act, Compliance)
3. Answer questions         →  Save per step
4. Compute recommendations  →  Suggested risk level
5. Submit                   →  Overall risk and proceed decision
```

**GAIRA modules:**

| Module | When to use |
|--------|-------------|
| **AI Risk Levels** (triage) | Start here — routes to Light or Comprehensive |
| **GAIRA Light** | Lower-risk projects; self-service |
| **GAIRA Comprehensive** | Higher-risk projects; full workshop |
| **AI Act check** | EU AI Act applicability |
| **Compliance check** | Operational compliance checklist |

**Example:** A team registers “Customer Support Chatbot”, completes triage → GAIRA Light → submits **medium risk, proceed with conditions** before going to production.

---

#### GAIRA reviews (`/gaira/reviews`)

**Purpose:** Second-line review queue for flagged GAIRA assessment answers that need a reviewer before submit.

**Example:** An assessment flags a high-risk data-sharing answer; a governance reviewer opens **GAIRA reviews**, checks the justification, and approves or sends back.

---

#### GAIRA approvals (`/gaira/approvals`)

**Purpose:** Approval queue for GAIRA application registrations or assessment outcomes that require formal sign-off.

**Example:** An admin sees a pending approval for a new “HR Screening AI” application and approves it after the assessment is complete.

---

#### Policies (`/policies`)

**Purpose:** Named **bundles of rules** (plus optional score thresholds) that define organizational standards evaluated at execution time.

**Example:** James creates **“Data Protection Policy”** (active), attaches rules for password detection, API key detection, and sensitive-data + external-model → any execution violating these rules is blocked or warned.

---

#### Rules (`/rules`)

**Purpose:** Single **if-then** compliance checks — the atomic building blocks of enforcement.

| Built-in example | What it checks | Action |
|------------------|----------------|--------|
| Email detected | Dataset contains emails | Warn |
| Password detected | Password-like values | Block |
| API key detected | Secret key patterns | Block |
| Sensitive + external model | Secrets sent outside your environment | Block |

**Example:** Admin disables “Email detected → warn” for a demo environment but keeps “API key → block” enabled.

---

### Monitoring

#### Analytics (`/analytics`)

**Purpose:** Trends over days and weeks — block rates, violations, high-risk users/models — not individual events.

**Example:** James filters the last 30 days and sees block rate spiked after a new external model was registered — he investigates under Executions and Models.

---

#### Gap analysis (`/gaps`)

**Purpose:** Identifies **what is missing** for a healthier compliance posture (e.g. inactive policy, missing GAIRA assessment, encryption not configured).

**Workflow:** View open gaps → **Acknowledge** (seen) or **Resolve** (fixed) → Admin runs **Run analysis** to refresh.

**Example:** Gap **“GAIRA assessment not completed for App X”** (high severity) appears with remediation: *Complete GAIRA Light assessment and submit.*

---

#### Threat detection (`/threats`)

**Purpose:** Security monitoring beyond compliance — suspicious patterns like repeated guard blocks, prompt injection, or output leakage.

**Example:** System detects repeated prompt-injection attempts from one session → Admin opens the threat, investigates triggering events, and resolves after blocking the user’s execution.

---

### Audit

#### Audit logs (`/audit`)

**Purpose:** Immutable record of **who did what, when** — logins, scans, execution decisions, guard actions, policy changes.

**Who:** Admin and Auditor (read-only for Auditors).

**Example:** Priya exports audit logs showing who approved a warn-level execution and when the live guard blocked a prompt containing an API key.

---

### Cross-cutting (not separate sidebar items)

| Capability | Purpose | Example |
|------------|---------|---------|
| **Authentication & RBAC** | Secure login; three roles with fine-grained permissions | User cannot see Registrations; Auditor sees all executions read-only |
| **Notifications (backend)** | Alerts for blocks, rule triggers, threats, gaps | Guard blocks a prompt → in-app notification (API; bell UI may be partial) |
| **Live monitoring guard (backend)** | Scans prompts/outputs during execution; can warn, block, or interrupt | API submits a prompt with a password → guard blocks and logs the event |

---

## Quick reference — sidebar map

| Section | Pages |
|---------|-------|
| **Platform** | Overview, Files, Scans, Reports |
| **Compliance** | Executions, Models |
| **Governance** | Registrations*, Compliance posture, NIST AI RMF, GAIRA, GAIRA reviews*, GAIRA approvals*, Policies, Rules |
| **Monitoring** | Analytics, Gap analysis, Threat detection |
| **Audit** | Audit logs |

\* Admin or permission-gated only.

---

## Suggested demo order

1. **Overview** — health metrics and framework snapshot  
2. **Files → Scans** — upload sample CSV, run scan, review findings  
3. **Reports** — download PDF evidence  
4. **Models → Executions** — validate file + scan + model; show allow / warn / block  
5. **Governance** — GAIRA application + assessment; Compliance posture + NIST AI RMF  
6. **Policies & Rules** — how enforcement is configured (Admin)  
7. **Monitoring** — Analytics, Gap analysis, Threat detection  
8. **Audit logs** — forensic trail (Auditor view)

---

*Document purpose: onboarding and supervisor overview. For step-by-step user instructions, see [`USER_GUIDE.md`](USER_GUIDE.md). For implementation status by page, see [`SUPERVISOR_IMPLEMENTATION_UPDATE.md`](SUPERVISOR_IMPLEMENTATION_UPDATE.md).*
