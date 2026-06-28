"""Map gap types and findings to compliance framework control references."""

from __future__ import annotations

from typing import Any

from app.models.compliance_gap import ComplianceGap
from app.services.gaps.constants import (
    GAP_DISABLED_MONITORING,
    GAP_INACTIVE_POLICY,
    GAP_INCOMPLETE_ROAIA_CONTEXT,
    GAP_MISSING_AUDIT_LOGS,
    GAP_MISSING_ENCRYPTION,
    GAP_MISSING_GAIRA_ASSESSMENT,
    GAP_MODEL_LOGGING_DISABLED,
    GAP_NO_ENABLED_RULES,
    GAP_RISKY_MODEL,
    GAP_UNAPPROVED_EXTERNAL_API,
    GAP_UNAPPROVED_MODEL,
    GAP_WEAK_RBAC,
)

FRAMEWORK_NIST_AI_RMF = "nist_ai_rmf"
FRAMEWORK_INTERNAL_GUARDRAILS = "internal_guardrails"
FRAMEWORK_GAIRA = "gaira"

FRAMEWORK_CATALOG: dict[str, dict[str, str]] = {
    FRAMEWORK_NIST_AI_RMF: {
        "name": "NIST AI RMF",
        "description": "Operational alignment with NIST AI Risk Management Framework outcomes.",
    },
    FRAMEWORK_INTERNAL_GUARDRAILS: {
        "name": "Internal guardrails",
        "description": "Organization rules, policies, and platform security controls.",
    },
    FRAMEWORK_GAIRA: {
        "name": "GAIRA governance",
        "description": "AI application risk assessment and ROAIA inventory requirements.",
    },
}

GAP_FRAMEWORK_MAPPINGS: dict[str, list[dict[str, str]]] = {
    GAP_MISSING_ENCRYPTION: [
        {"framework": FRAMEWORK_NIST_AI_RMF, "control_id": "MEASURE-2.7"},
        {"framework": FRAMEWORK_INTERNAL_GUARDRAILS, "control_id": "SEC-ENC-REST"},
    ],
    GAP_MISSING_AUDIT_LOGS: [
        {"framework": FRAMEWORK_NIST_AI_RMF, "control_id": "GOVERN-1.5"},
        {"framework": FRAMEWORK_NIST_AI_RMF, "control_id": "MEASURE-2.8"},
        {"framework": FRAMEWORK_INTERNAL_GUARDRAILS, "control_id": "GOV-AUDIT"},
    ],
    GAP_WEAK_RBAC: [
        {"framework": FRAMEWORK_NIST_AI_RMF, "control_id": "GOVERN-2.1"},
        {"framework": FRAMEWORK_INTERNAL_GUARDRAILS, "control_id": "ACC-RBAC"},
    ],
    GAP_INACTIVE_POLICY: [
        {"framework": FRAMEWORK_NIST_AI_RMF, "control_id": "GOVERN-1.4"},
        {"framework": FRAMEWORK_INTERNAL_GUARDRAILS, "control_id": "GOV-POLICY"},
    ],
    GAP_DISABLED_MONITORING: [
        {"framework": FRAMEWORK_NIST_AI_RMF, "control_id": "MEASURE-2.4"},
        {"framework": FRAMEWORK_NIST_AI_RMF, "control_id": "MANAGE-4.1"},
        {"framework": FRAMEWORK_INTERNAL_GUARDRAILS, "control_id": "MON-RT"},
    ],
    GAP_NO_ENABLED_RULES: [
        {"framework": FRAMEWORK_NIST_AI_RMF, "control_id": "GOVERN-1.2"},
        {"framework": FRAMEWORK_NIST_AI_RMF, "control_id": "MAP-1.6"},
        {"framework": FRAMEWORK_INTERNAL_GUARDRAILS, "control_id": "GOV-RULES"},
    ],
    GAP_RISKY_MODEL: [
        {"framework": FRAMEWORK_NIST_AI_RMF, "control_id": "GOVERN-6.1"},
        {"framework": FRAMEWORK_NIST_AI_RMF, "control_id": "MAP-4.1"},
        {"framework": FRAMEWORK_INTERNAL_GUARDRAILS, "control_id": "SEC-MODEL"},
    ],
    GAP_UNAPPROVED_EXTERNAL_API: [
        {"framework": FRAMEWORK_NIST_AI_RMF, "control_id": "GOVERN-6.1"},
        {"framework": FRAMEWORK_NIST_AI_RMF, "control_id": "MANAGE-3.1"},
        {"framework": FRAMEWORK_INTERNAL_GUARDRAILS, "control_id": "SEC-EXT-API"},
    ],
    GAP_UNAPPROVED_MODEL: [
        {"framework": FRAMEWORK_NIST_AI_RMF, "control_id": "GOVERN-6.1"},
        {"framework": FRAMEWORK_INTERNAL_GUARDRAILS, "control_id": "GOV-MODEL"},
    ],
    GAP_MISSING_GAIRA_ASSESSMENT: [
        {"framework": FRAMEWORK_NIST_AI_RMF, "control_id": "MAP-5.1"},
        {"framework": FRAMEWORK_NIST_AI_RMF, "control_id": "GOVERN-1.6"},
        {"framework": FRAMEWORK_GAIRA, "control_id": "GAIRA-ASSESS"},
    ],
    GAP_INCOMPLETE_ROAIA_CONTEXT: [
        {"framework": FRAMEWORK_NIST_AI_RMF, "control_id": "MAP-1.1"},
        {"framework": FRAMEWORK_NIST_AI_RMF, "control_id": "MAP-1.4"},
        {"framework": FRAMEWORK_GAIRA, "control_id": "GAIRA-ROAIA"},
    ],
    GAP_MODEL_LOGGING_DISABLED: [
        {"framework": FRAMEWORK_NIST_AI_RMF, "control_id": "MEASURE-2.4"},
        {"framework": FRAMEWORK_NIST_AI_RMF, "control_id": "MANAGE-4.1"},
        {"framework": FRAMEWORK_INTERNAL_GUARDRAILS, "control_id": "MON-MODEL"},
    ],
}


def _dedupe_refs(refs: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, str]] = []
    for ref in refs:
        key = (ref["framework"], ref["control_id"])
        if key in seen:
            continue
        seen.add(key)
        out.append(ref)
    return out


def framework_refs_for_gap_type(gap_type: str) -> list[dict[str, str]]:
    return list(GAP_FRAMEWORK_MAPPINGS.get(gap_type, []))


def attach_framework_refs_to_metadata(
    gap_type: str, metadata: dict[str, Any] | None
) -> dict[str, Any]:
    """Merge canonical framework refs into gap metadata at detection time."""
    meta = dict(metadata or {})
    existing = meta.get("framework_refs")
    if isinstance(existing, list) and existing:
        return meta
    refs = framework_refs_for_gap_type(gap_type)
    if refs:
        meta["framework_refs"] = refs
    legacy_nist = meta.get("nist_refs")
    if isinstance(legacy_nist, list) and legacy_nist and not refs:
        meta["framework_refs"] = [
            {"framework": FRAMEWORK_NIST_AI_RMF, "control_id": cid} for cid in legacy_nist
        ]
    return meta


def resolve_framework_refs(gap: ComplianceGap) -> list[dict[str, str]]:
    """Resolve framework refs from persisted metadata or canonical mapping."""
    meta = gap.metadata_json or {}
    stored = meta.get("framework_refs")
    if isinstance(stored, list) and stored:
        refs: list[dict[str, str]] = []
        for item in stored:
            if isinstance(item, dict) and item.get("framework") and item.get("control_id"):
                refs.append(
                    {"framework": str(item["framework"]), "control_id": str(item["control_id"])}
                )
        if refs:
            return _dedupe_refs(refs)
    legacy_nist = meta.get("nist_refs")
    if isinstance(legacy_nist, list) and legacy_nist:
        return _dedupe_refs(
            [{"framework": FRAMEWORK_NIST_AI_RMF, "control_id": str(cid)} for cid in legacy_nist]
        )
    return framework_refs_for_gap_type(gap.gap_type)


def gap_belongs_to_framework(gap: ComplianceGap, framework_id: str) -> bool:
    return any(ref["framework"] == framework_id for ref in resolve_framework_refs(gap))


def aggregate_by_framework(gaps: list[ComplianceGap]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for gap in gaps:
        for ref in resolve_framework_refs(gap):
            fid = ref["framework"]
            counts[fid] = counts.get(fid, 0) + 1
    return counts
