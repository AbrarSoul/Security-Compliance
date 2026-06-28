# NIST AI RMF ↔ ComplianceGuard Mapping

This document maps **NIST AI RMF 1.0** subcategories to ComplianceGuard modules for the **ComplianceGuard Operational AI RMF Profile** (`complianceguard-operational-v1`).

**Canonical catalog:** [`nist_ai_rmf_controls.json`](nist_ai_rmf_controls.json) (72 subcategories)  
**Source framework:** [`NIST_AI_RMF.md`](NIST_AI_RMF.md)  
**Live profile API:** `GET /api/v1/nist-ai-rmf/profile/current`

## Important disclaimer

ComplianceGuard provides **operational alignment evidence**, not NIST certification. Controls marked `not_assessed` or `not_applicable` require organizational process or future product scope.

## Profile concept (NIST Section 6)

| NIST concept | ComplianceGuard implementation |
|--------------|-------------------------------|
| **Cross-sectoral profile** | LLM/data-pipeline AI use with GAIRA + guard |
| **Current profile** | Auto-evaluated from ROAIA, GAIRA, scans, guard, gaps, audit |
| **Target profile** | Future: admin-configured thresholds |
| **Gap** | Existing gap analysis + NIST-tagged detectors |

## Four functions → platform modules

| NIST function | Primary ComplianceGuard modules |
|---------------|--------------------------------|
| **GOVERN** | RBAC, policies, rules, audit logs, model approval, ROAIA |
| **MAP** | GAIRA assessments, ROAIA fields, model registry |
| **MEASURE** | Scans, execution validation, guard, analytics, gap analysis |
| **MANAGE** | allow/warn/block, notifications, gap remediation, threats |

## Automated evaluators

These evaluators drive **Current Profile** status for multiple controls:

| Evaluator | Status inputs | Example NIST refs |
|-----------|---------------|-------------------|
| `org_has_enabled_rules` | Enabled compliance rules | GOVERN-1.2, MAP-1.6 |
| `org_has_active_controls` | Rules + active policies | GOVERN-1.4, MAP-4.2 |
| `org_has_audit_and_gaps` | Audit events + gap runs | GOVERN-1.5, MEASURE-2.8 |
| `roaia_inventory` | Active AI apps + models | GOVERN-1.6, MAP-2.1 |
| `rbac_roles_configured` | User-role assignments | GOVERN-2.1 |
| `gaira_leadership_decisions` | Submitted GAIRA + proceed decision | GOVERN-2.3, MANAGE-1.1 |
| `gaira_context_documented` | ROAIA purpose documented | MAP-1.1, MAP-1.4, MAP-3.3 |
| `gaira_risk_assessed` | GAIRA status completed | MAP-5.1 |
| `no_unapproved_external_models` | External/cloud model approval | GOVERN-6.1, MAP-4.1, MANAGE-3.1 |
| `execution_blocking` | Execution results with block | GOVERN-6.2, MANAGE-2.4 |
| `production_monitoring` | Model logging enabled | MEASURE-2.4, MANAGE-4.1 |
| `privacy_scanning_active` | Dataset scans | MEASURE-2.10 |
| `security_controls_active` | Rules + scans | MEASURE-2.7 |
| `gap_analysis_recent` | Gap run within 30 days | MEASURE-1.2, MANAGE-1.2 |
| `risk_tracking_active` | Gaps + scans | MEASURE-3.1 |
| `incident_detection` | Audit trail activity | GOVERN-4.3, MANAGE-4.3 |

## NIST-specific gap detectors

| Gap type | NIST refs | Trigger |
|----------|-----------|---------|
| `missing_gaira_assessment` | MAP-5.1, GOVERN-1.6 | Active app without completed GAIRA |
| `incomplete_roaia_context` | MAP-1.1, MAP-1.4 | Active app missing purpose |
| `model_logging_disabled` | MEASURE-2.4, MANAGE-4.1 | Active model with logging off |

## Out of scope (honest gaps)

| NIST area | Examples | Why |
|-----------|----------|-----|
| DEI / workforce | GOVERN-3 | Organizational culture |
| Training | GOVERN-2.2 | LMS not in platform |
| Explainability | MEASURE-2.9 | Not implemented |
| Fairness / bias | MEASURE-2.11 | Not implemented |
| Environmental | MEASURE-2.12 | Not tracked |
| Decommissioning | GOVERN-1.7 | Lifecycle process |
| Independent TEVV | MEASURE-1.3 | Requires external assessor |

## Regenerating the catalog

```bash
cd backend
.venv/Scripts/python.exe scripts/generate_nist_controls.py
```

Updates both `backend/app/data/nist_ai_rmf/controls_v1.json` and `Frameworks/nist_ai_rmf_controls.json`.

## Next steps

1. **Target profile** — admin thresholds (e.g. 100% ROAIA with GAIRA completed)
2. **Playbook links** — attach NIST Playbook actions per control in UI
3. **ISO 42001 / EU AI Act** — crosswalk tags on same control IDs
4. **Reports** — PDF section grouped by GOVERN / MAP / MEASURE / MANAGE
