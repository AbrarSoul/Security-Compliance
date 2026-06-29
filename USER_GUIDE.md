# ComplianceGuard — User Guide

A practical guide for everyone who uses the platform — analysts, project owners, compliance officers, and administrators. You do not need a technical background to follow this document.

**How to use this guide:** Read Sections 1–3 first (what the system does, your role, getting started). Jump to any later section when you need help with a specific task.

**Related docs:** [`GAIRA_USER_GUIDE.md`](GAIRA_USER_GUIDE.md) (detailed AI governance questionnaires) · [`Running_commands.md`](Running_commands.md) (for developers running the app locally)

---

## 1. What is ComplianceGuard?

ComplianceGuard helps your organization answer two related questions:

| Question | Plain-language meaning | Where in the app |
|----------|------------------------|------------------|
| **Should we build or deploy this AI application?** | Is the *project* itself acceptable from a governance and risk perspective? | **Governance → GAIRA**, **Compliance posture** |
| **Is this data safe to use with this AI model right now?** | Can we *run* this dataset or prompt through a specific model today? | **Files → Scans → Executions → Models** |

Think of it like airport security with two checkpoints:

1. **Project gate (GAIRA)** — Before you build, you fill out a structured risk questionnaire: *“What is this AI for? Who does it affect? How risky is it?”*
2. **Operational gate (Scans & Executions)** — Before you run data through a model, the system checks the file and the model combination: *“Does this file contain passwords? Is this model allowed? Should we block, warn, or allow?”*

Both matter. A project can pass GAIRA but still be blocked at execution if a file contains secrets. A clean file can still be blocked if the model is not approved.

### The four stages of using the platform

```
 Stage 0 — AI governance          Stage 1 — Data preparation       Stage 2 — Execution check        Stage 3 — Live monitoring
 ┌──────────────────────────┐     ┌─────────────────────────┐     ┌──────────────────────────┐     ┌─────────────────────────────┐
 │ Register AI application  │     │ Upload dataset          │     │ Validate execution       │     │ Monitor prompts & outputs   │
 │ Triage → Assess → ROAIA  │  →  │ Run compliance scan     │  →  │ Acknowledge warnings     │  →  │ Analytics & trends          │
 │                          │     │ Generate report         │     │ Start execution + guard  │     │ Gap analysis & threats      │
 │                          │     │ Fix critical findings   │     │                          │     │ Audit logs & notifications  │
 └──────────────────────────┘     └─────────────────────────┘     └──────────────────────────┘     └─────────────────────────────┘
```

### What “compliant” means here

When the system says something is **compliant**, it means **compliant with the rules and policies configured in this platform** — not automatic certification against ISO, NIST, SOC 2, or the EU AI Act.

The platform shows you **evidence**: what was found, which rules fired, and what to fix. Admins tune rules and policies to match your organization’s requirements. See Section 5 for how frameworks, rules, and policies fit together.

---

## 2. User roles — who does what?

Every account has one role: **User**, **Admin**, or **Auditor**. Your role controls which pages and buttons you see. Your role appears at the **bottom-left of the sidebar** (below your email).

After an admin changes your role, **sign out and sign back in** so your permissions update.

### Role at a glance

| Role | Who is this? | In one sentence |
|------|--------------|-----------------|
| **User** | Analysts, data scientists, project owners | Do day-to-day work: upload data, scan, run executions, complete GAIRA assessments |
| **Admin** | Platform owner, security lead, IT admin | Everything a User can do, plus configure rules, policies, models, and approve new accounts |
| **Auditor** | Compliance officer, internal audit, legal reviewer | Read-only view across the whole organization — no changes, full visibility |

---

### User — day-to-day operator

**Typical job titles:** Data analyst, ML engineer, business analyst, AI project owner

**What you use the system for:**

- Upload datasets and check them for sensitive content (emails, passwords, API keys)
- Request permission to run a dataset through an approved AI model
- Register AI applications and complete GAIRA risk assessments
- Watch alerts when something is blocked during live AI use
- Review your own analytics and open gaps

**Example — Maria, marketing analyst:**

Maria wants to summarize customer feedback using an internal AI model.

1. She uploads `customer_feedback.csv` under **Files**.
2. She runs a **Scan** — the system finds email addresses and marks the file as **risky**.
3. She follows the scan **Recommendations** (mask or remove email columns).
4. She re-scans until the file is **compliant** or acceptable.
5. Under **Executions**, she picks her file, scan, and the approved local model → gets **allow**.
6. She starts the execution; the live guard watches each prompt and output.

Maria cannot create new rules or approve other users — she works within guardrails set by Admin.

---

### Admin — platform owner

**Typical job titles:** Security lead, platform administrator, compliance program manager

**What you use the system for:**

- Approve or reject new user registrations
- Create and maintain **Rules** and **Policies**
- Register or sync AI **Models** from GPT-Lab
- Run **Gap analysis** and **Threat detection** scans
- Manage notification settings platform-wide
- Everything a User can do

**Example — James, security admin:**

James sets up the platform for his team.

1. He approves new signups under **Governance → Registrations**, assigning each person User or Auditor role.
2. He syncs real models from GPT-Lab under **Models → Sync from GPT-Lab**.
3. He reviews **Rules** — e.g. “Password detected → block” — and enables the ones his org needs.
4. He bundles rules into **Policies** (e.g. “Data Protection Policy”) and sets them to **active**.
5. Monthly, he runs **Gap analysis** and assigns remediation tasks.
6. He checks **Compliance posture** and **NIST AI RMF** to see alignment gaps.

---

### Auditor — compliance reviewer

**Typical job titles:** Internal auditor, compliance officer, DPO, risk manager

**What you use the system for:**

- Review **all users’** scans, executions, and reports (not just your own)
- Inspect GAIRA assessments and the ROAIA inventory
- Read **Audit logs** for forensic review
- Monitor organization-wide **Analytics**, **Gaps**, and **Threats**
- Export evidence for external audits

**What you cannot do:** Upload files, run scans, change rules, approve users, or start executions. Auditors observe — they do not operate.

**Example — Priya, compliance officer:**

Before a quarterly review, Priya logs in as Auditor.

1. She opens **Reports** and reviews scan PDFs across the organization.
2. She checks **Executions** for blocked runs and reads blocking reasons.
3. She opens **GAIRA** → ROAIA inventory to confirm each AI app has a completed assessment.
4. She reviews **Compliance posture** and **NIST AI RMF** for open control gaps.
5. She exports **Audit logs** showing who approved what and when.

---

### Permission summary (what each role can access)

| Area | User | Admin | Auditor |
|------|:----:|:-----:|:-------:|
| Upload files, run scans, generate own reports | ✓ | ✓ | — |
| View all users’ reports | — | ✓ | ✓ |
| Request & run executions (own data) | ✓ | ✓ | — |
| View all executions | — | ✓ | ✓ |
| Register & complete GAIRA assessments | ✓ | ✓ | Read only |
| Create/edit rules & policies | — | ✓ | — |
| Approve user registrations | — | ✓ | — |
| Sync/register AI models | — | ✓ | — |
| Run gap analysis & threat detection | — | ✓ | — |
| View gaps, threats, analytics (org-wide) | Own scope | ✓ | ✓ |
| Audit logs | — | ✓ | ✓ |

If a button is missing or you see “no permission”, your role does not include that action — contact an admin.

---

## 3. Getting started

### Sign up and sign in

1. Open the app (e.g. `http://localhost:3000` in local development).
2. Click **Sign up** and enter your email, name, and a password (at least 8 characters with upper, lower, and a digit).
3. Your registration is submitted — **you cannot sign in yet**. An administrator must approve your account first.
4. After approval, sign in with your email and password. You land on the **Overview** dashboard.

**Need a different role?** Ask an admin to approve you as **User**, **Auditor**, or **Admin** under **Governance → Registrations**. Then sign out and sign back in.

### Sidebar navigation

The sidebar groups pages into five sections:

| Section | Pages | Purpose |
|---------|-------|---------|
| **Platform** | Overview, Files, Scans, Reports | Upload data, scan it, export results |
| **Compliance** | Executions, Models | Validate and run AI on approved models |
| **Governance** | Registrations*, Compliance posture, NIST AI RMF, GAIRA, Policies, Rules | AI governance, frameworks, guardrails |
| **Monitoring** | Analytics, Gap analysis, Threat detection | Trends, missing controls, security threats |
| **Audit** | Audit logs | Who did what, when |

\* **Registrations** is visible to admins only.

---

## 4. Frameworks, rules, and policies — explained simply

This section explains the “compliance logic” of the platform. You do not need to configure these unless you are an Admin — but understanding them helps you interpret scan and execution results.

### The hierarchy (how pieces fit together)

```
┌─────────────────────────────────────────────────────────────────┐
│  FRAMEWORKS  —  “What standards are we aligning with?”          │
│  (NIST AI RMF, GAIRA governance, Internal guardrails)           │
│  Shown on: Compliance posture, NIST AI RMF, Gap analysis          │
└───────────────────────────────┬─────────────────────────────────┘
                                │ maps gaps & controls to
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  POLICIES  —  “Named bundles of rules for a purpose”            │
│  (e.g. Data Protection Policy, Execution Baseline)              │
│  Shown on: Policies page; evaluated during Executions             │
└───────────────────────────────┬─────────────────────────────────┘
                                │ contains
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  RULES  —  “Single if-then checks”                              │
│  (e.g. If password found → block)                               │
│  Shown on: Rules page; fire during Scans and Executions           │
└─────────────────────────────────────────────────────────────────┘
```

**Analogy:** Think of a **Rule** as one traffic law (“stop at red lights”). A **Policy** is a traffic code chapter that groups related laws. A **Framework** is a national standard (like the Highway Code) that your local rules are designed to support — but passing the platform’s checks is not the same as an official certification.

---

### Frameworks

Frameworks help you see **alignment** with recognized AI governance structures. They group open issues and gaps under familiar headings so you know *what area* needs attention.

| Framework | What it represents | Where to view it |
|-----------|-------------------|------------------|
| **NIST AI RMF** | Alignment with the [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework) — Govern, Map, Measure, Manage | **Governance → NIST AI RMF**, **Compliance posture** |
| **GAIRA governance** | Your organization’s AI application risk assessments and ROAIA inventory requirements | **Governance → GAIRA**, **Compliance posture** |
| **Internal guardrails** | Your own rules, policies, model approvals, monitoring, and platform security settings | **Governance → Policies/Rules**, **Compliance posture** |

**Important:** Framework views show **operational alignment** based on platform telemetry (gaps, model status, GAIRA completion, etc.). They do **not** mean you hold an official NIST or EU AI Act certification. Use them as a dashboard for “what to fix next”, not as legal proof of compliance.

#### Compliance posture (Governance → Compliance posture)

A single page that summarizes all three frameworks:

- **Compliant (met)** — no open issues mapped to this framework
- **Partial** — medium-severity gaps remain
- **Not met** — critical or high-severity gaps remain

Each framework card lists open issues with **Fix:** remediation steps and linked control IDs (e.g. `GOVERN-1.5`, `GAIRA-ASSESS`). Click **View details** to drill into NIST AI RMF, GAIRA, or Gap analysis.

#### NIST AI RMF (Governance → NIST AI RMF)

Shows your organization’s profile against NIST AI RMF control outcomes across four functions:

| Function | Plain meaning |
|----------|---------------|
| **Govern** | Policies, roles, and oversight are in place |
| **Map** | AI use cases and risks are identified |
| **Measure** | You can detect and score risks (scans, monitoring) |
| **Manage** | You respond to risks (blocks, gaps, remediation) |

Each control shows **met**, **partial**, **not met**, or **not assessed**, with evidence from platform data (e.g. “audit logging enabled”, “unapproved external models exist”).

---

### Rules

A **rule** is a single automated check. When conditions match, the rule fires and produces an action.

| Rule part | What it means | Example |
|-----------|---------------|---------|
| **Condition** | When does this rule apply? | “File contains a password” |
| **Severity** | How serious? | `critical`, `high`, `medium`, `low` |
| **Action** | What should happen? | `allow`, `warn`, or `block` |
| **Priority** | Which rule wins if several match? | Higher number = evaluated first |
| **Category** | What area? | `data`, `model`, `security`, `privacy`, `execution` |
| **Enabled** | Is it turned on? | Admins can disable without deleting |

**Built-in example rules (seeded in the system):**

| Rule | What it checks | Action |
|------|----------------|--------|
| Email detected | Dataset contains email addresses | Warn |
| Password detected | Dataset contains password-like values | Block |
| API key detected | Dataset contains secret key patterns | Block |
| Sensitive data + external model | Passwords/keys + data sent outside your environment | Block |
| Confidential data + cloud model | Confidential classification + cloud-hosted model | Warn |

**When rules run:**

- During **scans** — contributes to risk scoring and recommendations
- During **execution validation** — helps decide allow / warn / block before you start
- During **live execution** — the guard can block or interrupt risky prompts and outputs

**Users:** Browse **Governance → Rules** to see what is enforced. You cannot edit rules.

**Admins:** Create, edit, enable, or disable rules. Use clear names so non-technical colleagues understand what each rule does.

---

### Policies

A **policy** bundles multiple rules under one named standard or organizational requirement. Policies also support **score thresholds** — automatic warn/block based on the validation risk score.

| Policy part | What it means | Example |
|-------------|---------------|---------|
| **Name** | Human-readable title | “Demo Data Protection” |
| **Type** | Purpose category | `data_policy`, `model_policy`, `execution_policy`, `security_policy` |
| **Status** | Lifecycle | `draft` → `active` → `inactive` / `archived` |
| **Attached rules** | Which rules belong to this policy | Password rule + API key rule + external-model rule |
| **Thresholds** | Score-based decisions | Block if score below 40; warn if below 70 |

**Built-in example policies (seeded in the system):**

| Policy | Purpose | Key rules attached |
|--------|---------|-------------------|
| Demo Execution Baseline | General execution guardrails for demos | Email detected, confidential + cloud model |
| Demo Data Protection | Blocks high-risk sensitive data combinations | Password, API key, sensitive + external model |

**How policies are evaluated:**

When you request an execution, the system evaluates all **active** policies. Each policy runs its rules and checks thresholds. The **strictest** outcome wins: if any policy says **block**, the execution is blocked.

**Users:** Browse **Governance → Policies** to understand what your organization enforces.

**Admins:**

1. Create a policy (start in `draft`).
2. Attach rules on the policy detail page.
3. Set thresholds if needed.
4. Set status to **active** when ready.
5. Deactivate policies you no longer need without deleting history.

---

### Rules vs policies vs frameworks — quick comparison

| | Rules | Policies | Frameworks |
|---|-------|----------|------------|
| **Purpose** | Single check | Group of checks + thresholds | Map issues to standards |
| **Who configures** | Admin | Admin | System-mapped (admin fixes underlying gaps) |
| **Affects executions** | Yes | Yes | Indirectly (via gaps) |
| **Example** | “API key → block” | “Data Protection Policy” | “NIST GOVERN-1.5” |

---

## 5. Dashboard sections — step by step

### 5.1 Overview

**Why:** Quick health check when you log in.

**What you see:** Totals for scans, executions, and reports; a compliance breakdown (compliant / risky / non-compliant); recent scans.

**When to use:** Every login — confirms nothing alarming happened overnight.

---

### 5.2 Files

**Why:** ComplianceGuard scans *files*. Upload a dataset before scanning or executing.

**What to do:**

1. Click **Upload**, choose a `.csv`, `.json`, or `.txt` file (≤ 50 MB by default).
2. Wait for metadata extraction (row count, column preview).
3. The file appears in your list; you can delete it anytime.

Files are stored locally on the server — not sent to third-party cloud storage by default.

---

### 5.3 Scans

**Why:** Detect sensitive content before using data with AI.

**What the scanner looks for:**

| Type | Examples |
|------|----------|
| Email | Email addresses in data |
| Phone | Phone number patterns |
| Password | Password-like values or column names |
| API key | Secret key patterns |
| Sensitive field | Column names like `ssn`, `credit_card`, `password` |

**What to do:**

1. Open **Scans** → **New scan** → pick a file.
2. Open the scan detail to see:
   - **Risk score** (0–100: green = low, amber = medium, red = high)
   - **Compliance status:** `compliant` / `risky` / `non_compliant`
   - **Findings** (each with severity)
   - **Recommendations** (mask, remove column, rotate secret, etc.)

> A **critical** finding can force `non_compliant` even if the score looks low. Treat critical findings as blockers.

**Risk score bands (default):**

| Score | Status |
|-------|--------|
| 0 – 30 | Compliant |
| 31 – 60 | Risky |
| 61 – 100 | Non-compliant |

---

### 5.4 Reports

**Why:** Share scan results with auditors, managers, or external systems.

**What to do:**

1. From a scan detail page (or **Reports**) click **Generate report**.
2. Download **JSON** for systems integration, **PDF** for human review.

Generate a new report after each scan if you need up-to-date evidence.

---

### 5.5 Models

**Why:** The platform only allows AI models it knows about. The **Models** page is a **governance registry** — it stores metadata about approved AI endpoints (provider, deployment, approval state). It does **not** host or run model weights.

**Key columns:**

| Column | Meaning |
|--------|---------|
| **Name** | Human-readable label (click for full profile) |
| **Code** | Stable internal ID (e.g. `GPTLAB_LLAMA3_1_8B`) |
| **Provider** | Who runs the model (GPT-Lab, OpenAI, Internal, etc.) |
| **Deployment** | **Local** = data stays in your environment; **External** = data is sent elsewhere |
| **Approved** | Compliance has signed off for general use |
| **Active** | Appears in execution dropdowns |

**What to do:**

1. Browse the list to see what is approved.
2. Click a model for its full profile.
3. Use **Run validation** to dry-run scan + model → get `allow` / `warn` / `block` before execution.
4. **Admins:** **Sync from GPT-Lab** to pull models from your GPU farm, or **Register model** manually.

Demo models (`Demo Local LLM`, `Demo External API`) are placeholders for testing — replace with real entries for production.

---

### 5.6 Executions

**Why:** Decides **“Can I run this dataset through this model?”** before and during AI use.

**Step-by-step workflow:**

```
1. Request validation   →  Pick file + scan + model  →  Decision (allow / warn / block)
2. If "warn"            →  Acknowledge the warning explicitly
3. Start execution      →  Live guard monitors each prompt and output
4. Result               →  completed | interrupted | blocked
```

**Common statuses:**

| Status | Meaning |
|--------|---------|
| `pending_validation` | System is evaluating |
| `allowed` | Safe to start |
| `warning_pending_acknowledgement` | Risky but allowed if you confirm |
| `approved_after_warning` | You acknowledged; safe to start |
| `blocked` | Cannot start or continue |
| `started` | Currently running |
| `interrupted` | Guard stopped a running execution |
| `completed` | Finished successfully |

Open any execution to see prompts, outputs, guard actions, and blocking reasons.

**Example outcomes:**

| Scenario | Typical result |
|----------|----------------|
| Clean internal data + approved local model | **Allow** |
| Risky data or unapproved cloud model | **Warn** (acknowledge to proceed) |
| Passwords/API keys + external model | **Block** |

---

### 5.7 GAIRA (AI risk assessment)

**Why:** Structured governance assessment for AI applications *before* deployment — separate from dataset scanning.

**Where:** **Governance → GAIRA**

| Role | Access |
|------|--------|
| **User / Admin** | Register applications, complete assessments |
| **Auditor** | Read-only review of submitted assessments and ROAIA inventory |

**Workflow:**

```
1. Register application     →  GAIRA → Register application
2. Start assessment         →  Application detail → Start assessment
3. Answer questions         →  Step tabs; save as you go
4. Compute recommendations  →  Suggested risk level & next module
5. Submit                   →  Set overall risk and proceed decision
6. ROAIA inventory          →  Main GAIRA page lists all apps with status
```

**GAIRA modules:**

| Module | When to use |
|--------|-------------|
| **AI Risk Levels** (triage) | Start here — short questionnaire routes you to Light or Comprehensive |
| **GAIRA Light** | Lower-risk projects; self-service |
| **GAIRA Comprehensive** | Higher-risk projects; full workshop |
| **AI Act check** | EU AI Act applicability |
| **Compliance check** | Operational compliance checklist |

> GAIRA helps assess EU AI Act exposure — it is **not** a certification. See [`GAIRA_USER_GUIDE.md`](GAIRA_USER_GUIDE.md) for scoring details.

---

### 5.8 Registrations (Admin only)

**Why:** New users cannot sign in until an admin approves them.

**What to do:**

1. Open **Governance → Registrations** (badge shows pending count).
2. For each pending user, choose a role: **User**, **Auditor**, or **Admin**.
3. Click **Approve** or **Reject**.
4. Tell the user they can now sign in (or that their request was rejected).

---

### 5.9 Analytics

**Why:** Trends over days and weeks — not individual events.

**What you see:** Total scans, blocked/allowed counts, average risk score, time-series charts, high-risk users/models.

**Filters:** 1 / 7 / 30 day windows. Admins and auditors see organization-wide data.

**When to use:** Weekly reviews, before audits, to spot abnormal patterns.

---

### 5.10 Gap analysis

**Why:** Identifies **what is missing** for a healthier compliance posture — e.g. “no encryption configured”, “inactive policy”, “GAIRA assessment not completed”.

**Workflow:**

1. View open gaps grouped by severity (`critical`, `high`, `medium`, `low`).
2. Each gap shows **Remediation** — what to do to close it.
3. **Acknowledge** — seen, not fixed yet.
4. **Resolve** — fixed, moves to history.
5. **Run analysis** (admin) — recomputes gaps from current platform state.

**Posture score** at the top: higher = healthier. Treat `critical` gaps as production blockers.

Gaps are linked to framework controls — visible on **Compliance posture** and **NIST AI RMF**.

---

### 5.11 Threat detection

**Why:** Security monitoring beyond compliance — suspicious behavior patterns.

**What it detects:** Repeated guard blocks, prompt-injection patterns, output leakage, unusual violation rates.

**Workflow:**

1. Dashboard shows open threats by severity.
2. Click a threat for triggering events and suggested response.
3. **Investigate** or **Resolve** (admin).
4. **Run detection** (admin) — batch recompute.

---

### 5.12 Audit logs

**Why:** Immutable record of who did what — required for compliance and forensics.

**What you see:** Logins, scans, execution decisions, guard actions, policy changes, threat updates — with actor, target, timestamp.

**Who has access:** Admin and Auditor.

---

### 5.13 Notifications

**Why:** Real-time alerts so you do not have to refresh pages.

**Bell icon** shows unread count. Alerts fire when:

- A guard blocks your prompt or output
- A rule triggers on your scan
- A threat affects you
- A high/critical gap is detected

Adjust preferences to enable or disable categories (in-app and email when configured).

---

## 6. End-to-end workflows

### New AI project (governance first)

```
1. Register AI application       →  GAIRA → Register application
2. Run AI Risk Levels triage     →  Answer → Compute → Submit
3. Complete GAIRA Light/Comp.    →  As recommended by triage
4. (Admin) Sync real models      →  Models → Sync from GPT-Lab
```

### Operational compliance (dataset + execution)

```
1. Upload dataset                →  Files
2. Run scan                      →  Scans (fix critical findings first)
3. Generate report (optional)    →  Reports
4. Validate execution            →  Executions (file + scan + model)
5. Acknowledge warning?          →  If decision = warn
6. Start execution               →  Live guard runs
7. Watch notifications           →  Real-time alerts
8. Check analytics weekly        →  Analytics
9. Run gap analysis monthly      →  Gaps (admin)
10. Review threats & audit       →  Threats, Audit logs
```

> GAIRA and execution validation are **separate gates**. A completed GAIRA assessment does not automatically block executions — treat `gaira_status: done` as an organizational requirement before production use.

---

## 7. Status colors (what the badges mean)

| Color | Meaning | Common labels |
|-------|---------|---------------|
| Green | Good / safe / done | `compliant`, `allow`, `completed`, `resolved`, `met` |
| Amber | Caution / pending | `risky`, `warn`, `pending_*`, `partial`, `draft` |
| Red | Blocked / failed | `non_compliant`, `block`, `critical`, `not_met` |
| Blue | In progress | `validating`, `scanning`, `queued` |
| Grey | Inactive | `disabled`, `cancelled`, `unknown` |

Risk scores: **0–30** green · **31–60** amber · **61–100** red

---

## 8. Common problems and fixes

| Problem | Likely cause | Fix |
|---------|--------------|-----|
| Cannot sign in after signup | Account pending approval | Wait for admin to approve under **Registrations** |
| "No permission" on a page | Role lacks access | Ask admin to assign role; **sign out and back in** |
| No **Sync from GPT-Lab** button | Not admin | Ask admin to promote you |
| GPT-Lab sync fails | Missing API key or VPN | Admin: set `GPTLAB_API_KEY` in backend `.env`; connect VPN if required |
| GAIRA submit rejected | Flagged answer needs 2nd-line reviewer | Add reviewer email on flagged Step 4 answers |
| Execution blocked unexpectedly | Critical finding or rule fired | Open execution → check blocking reasons and audit log |
| Notifications never arrive | Worker disabled or prefs muted | Admin: check outbox worker; user: check notification preferences |
| Gap list empty but issues expected | Analysis not re-run | Admin → **Run analysis** on Gaps page |
| Report shows old data | Generated before latest scan | Generate a new report after re-scanning |

---

## 9. Glossary

| Term | Plain definition |
|------|------------------|
| **Finding** | One piece of sensitive content detected (e.g. an email in a column) |
| **Recommendation** | Concrete fix for a finding (mask, remove, rotate, etc.) |
| **Compliance status** | File-level verdict: `compliant` / `risky` / `non_compliant` |
| **Decision** | Execution-level verdict: `allow` / `warn` / `block` |
| **Guard action** | Live decision during execution: `allowed`, `warned`, `blocked`, `interrupted` |
| **Rule** | Single if-then compliance check with an action |
| **Policy** | Named bundle of rules (and optional score thresholds) |
| **Framework** | Standard alignment view (NIST AI RMF, GAIRA, Internal guardrails) |
| **Model registry** | Catalog of approved AI endpoints (metadata only) |
| **GAIRA** | Generative AI Risk Assessment — project-level AI governance questionnaires |
| **ROAIA** | Records of AI Activities — inventory of registered AI applications |
| **Assessment** | One GAIRA module run for an application |
| **Posture score** | Single 0–100 gap-analysis health score; higher = better |
| **Session** | Monitoring window grouping prompts/outputs of one execution |

---

## 10. Where to go next

| Document | Audience | Content |
|----------|----------|---------|
| [`GAIRA_USER_GUIDE.md`](GAIRA_USER_GUIDE.md) | Project owners, governance leads | GAIRA scoring, modules, API |
| [`docs/PROJECT_USE_CASES_AND_WORKFLOWS.md`](docs/PROJECT_USE_CASES_AND_WORKFLOWS.md) | Everyone | Detailed use cases and API map |
| [`docs/COMPLIANCE_QA.md`](docs/COMPLIANCE_QA.md) | Supervisors | Plain-language compliance FAQ |
| [`Running_commands.md`](Running_commands.md) | Developers | Local setup commands |
| `http://localhost:8000/docs` | Integrators | Live API reference (when backend is running) |

Welcome aboard.
