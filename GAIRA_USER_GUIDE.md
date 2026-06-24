# GAIRA in ComplianceGuard — User Guide

This guide explains how the **GAIRA** (Generative AI Risk Assessment) framework is integrated into ComplianceGuard, who should use it, and how to run assessments end-to-end.

For the general ComplianceGuard walkthrough (files, scans, executions, monitoring), see [`USER_GUIDE.md`](USER_GUIDE.md).

---

## 1. What is GAIRA?

**GAIRA** is a structured AI risk assessment framework originally published by Rosenthal (law firm). It helps organizations answer a governance question that scans and execution checks alone cannot:

> **"Should we build or deploy this AI application, and at what risk level?"**

ComplianceGuard already answers an **operational** question at runtime:

> **"Is this dataset safe to run on this model right now?"**

GAIRA adds a **governance layer** before and alongside that:

```
  Governance (GAIRA)                    Operations (ComplianceGuard)
 ┌─────────────────────────┐           ┌──────────────────────────────┐
 │ Register application    │           │ Upload → Scan → Risk score   │
 │ Triage AI risk level    │    →      │ Validate execution           │
 │ Complete GAIRA form     │           │ Monitor prompts & outputs    │
 │ Record in ROAIA         │           │ Gaps → Threats → Audit       │
 └─────────────────────────┘           └──────────────────────────────┘
```

### Two types of risk (do not confuse them)

| Concept | GAIRA | ComplianceGuard scans |
|---------|-------|------------------------|
| **What it measures** | Organizational AI risk for a *use case* | Sensitive content risk in a *dataset* |
| **Scale** | `insignificant` / `low` / `medium` / `high` / `very_high` | Score 0–100 + `compliant` / `risky` / `non_compliant` |
| **Who decides** | Application owner (with 2nd-line input) | Automated scanner + rules/policies |
| **When** | Before / during project approval | Before each execution |

Both can apply to the same project. A low scan score does not replace a GAIRA assessment, and a completed GAIRA assessment does not guarantee a dataset is safe to execute.

---

## 2. GAIRA modules in this system

The source framework lives in `GAIRA/Rosenthal_GAIRA.json` (spreadsheet export). ComplianceGuard parses it into a normalized schema at `backend/app/data/gaira/framework_v1.json`.

| Module key | Original GAIRA worksheet | Purpose |
|------------|--------------------------|---------|
| `ai_risk_levels` | AI Risk Levels | Quick triage: insignificant → high → medium → low |
| `gaira_light` | GAIRA Light | Self-service assessment for smaller / lower-risk projects |
| `gaira_comprehensive` | GAIRA Comprehensive | Full workshop assessment for high-risk projects (includes DPIA) |
| `ai_act_check` | AI Act Check | EU AI Act applicability and role classification |
| `compliance_check` | Compliance Check | Operational compliance checklist |
| `roaia` | ROAIA | Records of AI Activities — inventory columns |

### Recommended workflow

```
1. Register AI application (ROAIA entry)
2. Run AI Risk Levels triage
       │
       ├─ insignificant / low / medium → GAIRA Light
       └─ high → GAIRA Comprehensive (+ AI Act Check)
3. Submit assessment → update ROAIA risk level
4. (Separately) run dataset scans & execution validation in ComplianceGuard
```

---

## 3. Roles & permissions

| Permission | Who gets it | What it allows |
|------------|-------------|----------------|
| `gaira:read` | User, Admin, Auditor | View framework questions, applications, assessments, ROAIA |
| `gaira:manage` | User, Admin | Create applications, start assessments, save answers, submit |
| `gaira:read_all` | Admin, Auditor | Organization-wide read (same data today; reserved for future scoping) |

| Role | GAIRA access |
|------|--------------|
| **User** | Full read + manage (create and complete assessments) |
| **Admin** | Same as user + all permissions |
| **Auditor** | Read-only (review submitted assessments and ROAIA) |

If you see a permission error, sign out and back in after an admin updates your role.

---

## 4. Core concepts

### AI Application (ROAIA entry)

An **AI Application** is a registered use case — not just an AI model. One application might use one or more models.

Typical fields:

- **Name** — e.g. "Project Alpha"
- **Owner** — application owner / business lead
- **Purpose** — what the system does
- **Audience** — who interacts with it
- **Technology / AI provider** — model and vendor details
- **Linked compliance model** — optional link to a registered model in ComplianceGuard
- **Risk level** — set when an assessment is submitted
- **GAIRA status** — `none` → `in_progress` → `done`
- **Next assessment date** — when to revisit (set manually today)

### Assessment

A **Gaira Assessment** is one completed or in-progress run of a GAIRA module for an application.

| Field | Meaning |
|-------|---------|
| `assessment_type` | Which module (`ai_risk_levels`, `gaira_light`, etc.) |
| `status` | `draft` → `submitted` (or `superseded` when replaced) |
| `answers_json` | All question answers |
| `computed_json` | System recommendations (routing, risk tier, flags) |
| `overall_risk_level` | Final owner decision (on submit) |
| `proceed_decision` | How the owner intends to proceed |

### Answer format

Answers are stored as a JSON object keyed by question ID (e.g. `"2.01"`, `"3.06"`):

```json
{
  "2.01": {
    "value": "Yes",
    "description": "Optional explanation",
    "source": "user"
  },
  "4.01": {
    "value": "Yes",
    "source": "compliance_model",
    "note": "Model metadata indicates data leaves platform"
  }
}
```

For Step 4 problematic answers in GAIRA Light, flagged items can include:

```json
{
  "4.20": {
    "value": "No",
    "flagged": true,
    "second_line_reviewer": "legal@company.com",
    "second_line_comment": "Accepted with contractual controls"
  }
}
```

Submit is **blocked** if any flagged Step 4 answer lacks second-line review.

---

## 5. How scoring works

### AI Risk Levels (`ai_risk_levels`)

Evaluated in priority order:

1. **Step 1 — Insignificant?** If *any* Step 1 question is **Yes** → risk = `insignificant`
2. **Step 2 — High?** Else if *any* Step 2 question is **Yes** → risk = `high` → recommend **GAIRA Comprehensive**
3. **Step 3 — Medium?** Else if *any* Step 3 question is **Yes** → risk = `medium` → recommend **GAIRA Light**
4. **Otherwise** → risk = `low` → recommend **GAIRA Light**

### GAIRA Light routing (Step 3)

If *any* of questions `3.01`–`3.08` is **Yes**, the system recommends **GAIRA Comprehensive** instead of staying on Light only.

Common triggers include:

- Training or fine-tuning models on restricted data
- Decisions that materially affect people
- High-volume interaction on sensitive topics
- EU AI Act prohibited / high-risk classification
- Large investment or strategic importance

### GAIRA Light Step 4 (controls)

The system counts **problematic** answers in Step 4. If any are flagged and missing `second_line_reviewer`, submit is rejected until 2nd-line functions (legal, DPO, CISO, etc.) record their review.

> **Note:** Full spreadsheet conditional logic (questions fading based on preparatory answers) is not yet replicated in the UI. All Step 4 questions are available via the API; answer only those relevant to your project.

### GAIRA Comprehensive

Questions are available and answers can be stored. The full 4×4 risk matrix scoring from the original spreadsheet is **not yet automated** — the application owner still sets `overall_risk_level` on submit.

---

## 6. Auto-prefill from ComplianceGuard data

When you start an assessment, ComplianceGuard can pre-populate answers from data you already have:

| Source | What gets prefilled |
|--------|---------------------|
| **Application record** | Company, department, owner, purpose, scope, technology |
| **Linked compliance model** | Provider name, data-leaves-platform (Step 4.01), logging gaps (flagged if logging disabled) |
| **Linked scan** (optional `scan_id`) | Personal data detected → Step 4.06 suggested as **Yes** |

Prefilled values include `"source": "application"`, `"compliance_model"`, or `"scan"`. **Always review and confirm** — the application owner remains accountable per GAIRA methodology.

---

## 7. API workflow (step by step)

Base URL: `http://localhost:8000/api/v1/gaira`  
Interactive docs: `http://localhost:8000/docs` (tag: **gaira**)

All requests require `Authorization: Bearer <token>`.

### 7.1 Browse the framework

```http
GET /gaira/framework
GET /gaira/framework/gaira_light
GET /gaira/framework/ai_risk_levels
```

Returns module metadata, steps, and the full question list with explanations.

### 7.2 Register an application

```http
POST /gaira/applications
Content-Type: application/json

{
  "name": "Project Alpha",
  "owner_name": "Peter Parker",
  "department": "Wealth Management",
  "purpose": "Transcribe and summarize client meetings",
  "audience": "Relationship managers",
  "technology_description": "DeltaPI-4 LLM via CloudCo tenant",
  "ai_provider": "CloudCo AI Services",
  "compliance_model_id": "<optional-uuid>"
}
```

### 7.3 View ROAIA inventory

```http
GET /gaira/roaia
```

Returns all registered applications with GAIRA status, risk level, compliance check status, and latest assessment reference.

### 7.4 Start an assessment

```http
POST /gaira/applications/{application_id}/assessments
Content-Type: application/json

{
  "assessment_type": "ai_risk_levels",
  "scan_id": "<optional-scan-uuid>"
}
```

Valid `assessment_type` values:

- `ai_risk_levels`
- `gaira_light`
- `gaira_comprehensive`
- `ai_act_check`
- `compliance_check`

### 7.5 Save answers

```http
PATCH /gaira/assessments/{assessment_id}/answers
Content-Type: application/json

{
  "merge": true,
  "answers": {
    "2.01": { "value": "Yes" },
    "2.02": { "value": "No" }
  }
}
```

Set `"merge": false` to replace the entire answer set.

### 7.6 Compute recommendations

```http
POST /gaira/assessments/{assessment_id}/compute
```

Returns updated `computed_json` with routing advice, risk tier, and flags.

### 7.7 Submit (finalize)

```http
POST /gaira/assessments/{assessment_id}/submit
Content-Type: application/json

{
  "overall_risk_level": "medium",
  "proceed_decision": "Proceed with conditions",
  "decision_comments": "Pilot in Q2 with legal review of client consent flow."
}
```

On submit:

- Assessment status → `submitted`
- Application `gaira_status` → `done`
- Application `risk_level` updated
- Previous submitted assessment of the same type → `superseded`

### 7.8 List and inspect

```http
GET /gaira/applications
GET /gaira/applications/{id}
GET /gaira/applications/{id}/assessments
GET /gaira/assessments/{id}
```

---

## 8. End-to-end example (typical project)

```
Day 1 — Register
  POST /gaira/applications          → create "AI Meeting Analyzer"
  GET  /gaira/roaia                 → confirm it appears in inventory

Day 2 — Triage
  POST .../assessments              → type: ai_risk_levels
  PATCH .../answers                 → answer Step 1–3 questions
  POST .../compute                  → result: "high" → use Comprehensive
  POST .../submit                   → record triage decision

Day 3–5 — Full assessment (business-led workshop)
  POST .../assessments              → type: gaira_light (or gaira_comprehensive)
  PATCH .../answers                 → work through steps 1–6
  POST .../compute                  → check routing & Step 4 flags
  (If flagged) add second_line_reviewer to flagged answers
  POST .../submit                   → overall_risk_level: "medium"

Ongoing — Operational compliance (existing ComplianceGuard flow)
  Upload client data → Scan → Validate execution → Monitor
  Link the same compliance_model_id on the application for consistency
```

---

## 9. How GAIRA fits the ComplianceGuard lifecycle

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PROJECT LIFECYCLE                               │
├─────────────────────────────────────────────────────────────────────────┤
│  GAIRA (governance)          │  ComplianceGuard (operations)          │
│  ─────────────────           │  ────────────────────────────            │
│  Register application        │                                         │
│  AI Risk Levels triage       │                                         │
│  GAIRA Light / Comprehensive │                                         │
│  EU AI Act check             │                                         │
│  Submit → ROAIA updated      │                                         │
│                              │  Upload dataset                         │
│                              │  Scan → findings & score                │
│                              │  Register / pick model                  │
│                              │  Validate execution                     │
│                              │  Execute with live guard                │
│                              │  Gap analysis & threat detection        │
└─────────────────────────────────────────────────────────────────────────┘
```

**Today:** GAIRA and execution validation are **separate gates**. A submitted GAIRA assessment does not yet automatically block executions — that integration is planned.

**Practical rule until then:** Do not approve production execution for an application whose GAIRA status is not `done` or whose risk level has not been reviewed.

---

## 10. GAIRA Light steps (reference)

The original GAIRA Light form has six steps. The API exposes all questions under `GET /gaira/framework/gaira_light`.

| Step | Title | What you document |
|------|-------|-------------------|
| **1** | What is your application about? | Description, GenAI techniques, controls, project plan |
| **2** | EU AI Act | Applicability, prohibited/high-risk, roles, transparency |
| **3** | High-risk for the company? | Routing questions → Light vs Comprehensive |
| **4** | Generative AI risks | Provider, data transfer, logging, IP, human oversight, etc. |
| **5** | DPIA | Whether DPIA is required + simplified DPIA (if personal data) |
| **6** | Conclusion | Overall risk level, proceed decision, stakeholder comments |

---

## 11. ROAIA columns (inventory view)

The `GET /gaira/roaia` endpoint maps applications to the ROAIA register:

| ROAIA column | Application field |
|--------------|-------------------|
| Application / use case | `name` |
| Purpose | `purpose` |
| Owner | `owner_name` |
| Audience | `audience` |
| AI Product / Provider | `ai_provider` |
| Technology (incl. model) | `technology_description` |
| EU AI Act | `ai_act_category` |
| Compl.-check | `compliance_check_status` |
| DPIA | `dpia_status` |
| GAIRA | `gaira_status` |
| Risk Level | `risk_level` |
| Deployed | `deployed_at` |
| Next assessment | `next_assessment_at` |

Update `ai_act_category`, `dpia_status`, `deployed_at`, and `next_assessment_at` via `PATCH /gaira/applications/{id}`.

---

## 12. Regenerating the framework from source

If `GAIRA/Rosenthal_GAIRA.json` is updated:

```powershell
cd backend
$env:PYTHONPATH="."
python scripts/parse_gaira_json.py
```

This rewrites `backend/app/data/gaira/framework_v1.json`. Restart the backend to pick up changes.

---

## 13. Common issues

| Problem | Likely cause | Fix |
|---------|--------------|-----|
| `403` on GAIRA endpoints | Missing `gaira:read` or `gaira:manage` | Check role; re-login after permission change |
| Submit rejected — second-line review | Step 4 answer flagged without reviewer | Add `second_line_reviewer` (and comment) to flagged answers |
| `404` on framework module | Wrong module key | Use keys from `GET /gaira/framework` |
| Answers not updating | Assessment already `submitted` | Start a new assessment; submitted runs are immutable |
| Prefill missing | No linked model or scan | Pass `scan_id` when starting assessment; set `compliance_model_id` on application |
| Risk level seems wrong | Triage uses OR logic per step | Any single **Yes** in a step tier triggers that tier |

---

## 14. Glossary

- **GAIRA** — Generative AI Risk Assessment (Rosenthal framework).
- **ROAIA** — Records of AI Activities; central inventory of AI systems in the organization.
- **AI Risk Levels** — Short triage worksheet to classify organizational AI risk.
- **GAIRA Light** — Simplified assessment for lower-risk projects.
- **GAIRA Comprehensive** — Full assessment including DPIA for high-risk projects.
- **2nd line** — Legal, compliance, DPO, CISO, or other expert functions that review flagged answers.
- **Application owner** — Business owner accountable for the risk decision (per GAIRA methodology).
- **Assessment** — One run of a GAIRA module for an application.
- **Computed JSON** — Machine-generated recommendations from your answers.
- **Superseded** — A previous submitted assessment replaced by a newer submission of the same type.

---

## 15. Related documentation

| Document | Audience | Content |
|----------|----------|---------|
| [`USER_GUIDE.md`](USER_GUIDE.md) | All users | Files, scans, executions, monitoring, gaps, threats |
| [`backend/README.md`](backend/README.md) | Developers | Backend setup, environment, migrations |
| `http://localhost:8000/docs` | Developers / integrators | Full OpenAPI reference including `/gaira` |
| `GAIRA/Rosenthal_GAIRA.json` | Compliance leads | Original Rosenthal spreadsheet export (source of truth for question text) |

---

## 16. Roadmap (not yet available)

The following are planned but **not implemented** in the current release:

- Dashboard UI for ROAIA and assessment wizard
- Automatic execution gate (block validate/start without current GAIRA)
- Gap detector for missing or expired assessments
- Full GAIRA Comprehensive 4×4 matrix auto-scoring
- Audit log entries dedicated to GAIRA submit events

Use the API workflow in Section 7 until the UI is delivered.
