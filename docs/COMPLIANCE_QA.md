# Compliance Q&A — Plain-Language Answers for Supervisors

This document answers common questions about what “compliance” means in our Security Compliance platform. It is written for a non-technical audience.

---

## (1) “Compliance with what?” How does the user know what is being tested?

### Short answer

When the system says something is “compliant,” it means **compliant with the rules and checks built into this tool** — not automatically compliant with a named standard like ISO 27001, NIST, or SOC 2.

### What the system actually checks

Think of it like a **security health check** on data and AI use. The tool looks for things such as:

- Personal information (emails, phone numbers, names)
- Passwords and secret keys
- Other sensitive data in files or AI conversations

It then gives a result such as **compliant**, **risky**, or **non-compliant**, based on how serious the findings are and what rules the organisation has set up.

The tool can also **allow, warn, or block** certain actions — for example, using sensitive data with an external AI model.

### How does the user know what was tested?

A user can see:

- **What was found** — e.g. “passwords detected in this file”
- **Why the score was given** — a breakdown of what contributed to the risk level
- **Which rules and policies were applied** — the organisation’s own guardrails

So the user is not left guessing. They can see the evidence behind the result.

### How were these checks chosen?

They were chosen as **sensible defaults for data security and AI risk** — things most organisations would want to catch (leaked passwords, personal data exposed, risky AI use, and so on).

An administrator can later **adjust the rules and policies** to better match the organisation’s needs. But the tool does **not** come pre-loaded as a full, official mapping to ISO, NIST, or similar standards.

---

## (2) Can the user see results per framework — so they know which standards they pass and which they don’t?

### Short answer

**Not in the way you might expect.** The system does not currently show separate results like “ISO 27001: pass / fail” or “NIST: 80% compliant.”

### What the user *can* see today

- Results **per file or dataset scan** — what was found and the overall risk level
- Results **per rule or policy** — which internal guardrails were triggered
- Reports that summarise findings and recommendations

### What this means in practice

If a supervisor asks, *“Are we compliant with ISO?”*, this tool **cannot answer that directly today**. It can show whether sensitive data was found, whether risky actions were blocked, and whether internal policies were followed — but it does not group those results under official framework names.

To support per-framework reporting in the future, we would need to **map** our checks to specific standard controls (e.g. “this finding relates to ISO control X”) and display results that way.

---

## (3) Can the user choose which frameworks to check — for example, only ISO?

### Short answer

**No — not as a list of official standards.** The user cannot tick a box for “ISO only” and have the system evaluate just that standard.

### What the user *can* choose

- **Which internal rules and policies are turned on** — so the organisation enforces only what it cares about
- **How strict the scoring is** — what counts as compliant vs. risky vs. non-compliant

### What this means in practice

If an organisation follows only one ISO standard, the tool does **not** automatically limit itself to that standard. Instead, an administrator would need to **configure the rules** so they reflect what that organisation actually requires.

In other words: the tool is flexible, but it works through **custom rules**, not through a menu of official compliance frameworks.

---

## (4) Is this only about security compliance, or other types of compliance too?

### Short answer

**Mainly security and data protection** — especially around sensitive data and safe use of AI.

### What falls within scope

- Checking files for sensitive or leaked information
- Blocking or warning against risky AI use (e.g. sending secrets to an external model)
- Monitoring AI inputs and outputs for security issues
- Keeping audit records of who did what
- Identifying security gaps and threats

### What falls outside scope (today)

The tool is **not** designed for other compliance areas such as:

- Financial reporting (e.g. accounting rules)
- HR or employment law
- Environmental or industry-specific regulations (unless we add those checks)

So the name “Security Compliance” is accurate: it focuses on **protecting data and managing AI-related security risk**, not on every type of organisational compliance.

---

## (5) What does it mean that GAIRA was added to the system?

### Short answer

GAIRA is **not something you need to be “compliant with.”** It is a **questionnaire tool** — developed by a law firm — that helps assess whether an AI application may fall under the **EU AI Act** (for example, whether it is high-risk or prohibited).

We integrated it so users can **run that assessment inside our platform** and keep the results in one place.

### What GAIRA does in our system

- Presents structured questions about an AI application (purpose, risk level, impact on people, and so on)
- Helps classify the application under EU AI Act thinking
- Stores the assessment so it can be reviewed later, with proper access controls and audit trail

### What GAIRA does *not* mean

- It does **not** mean the organisation is “GAIRA compliant”
- It does **not** replace legal advice or an official certification
- It is a **supporting tool for AI risk assessment**, not a compliance standard in itself

### Why this matters for a supervisor

If someone asks, *“Are we compliant with GAIRA?”* — that is the wrong question. The right question is: *“Have we completed a GAIRA-style assessment for our AI applications, and what did it tell us about our EU AI Act exposure?”*

GAIRA helps answer that second question. It is one input into governance — not a badge of compliance.

---

## Summary for quick reference

| Question | Plain answer |
|----------|--------------|
| Compliant with what? | With **this tool’s own rules and checks**, not automatically with ISO/NIST/etc. |
| Results per framework? | **No** — results are per scan and per internal rule, not per official standard |
| Choose frameworks? | **No** — but admins can turn rules on/off to match what the org needs |
| Security only? | **Mostly yes** — data protection and AI security risk, not all compliance types |
| What is GAIRA? | An **EU AI Act risk questionnaire** built into the platform — not a standard to comply with |
