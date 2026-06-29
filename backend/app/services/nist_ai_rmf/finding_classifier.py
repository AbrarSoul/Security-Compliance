"""Classify NIST control outcomes as violations vs alignment gaps."""

from __future__ import annotations

from typing import Any

# Evaluators where not_met/partial can mean an active policy breach (inventory in use).
BREACH_EVALUATORS = frozenset(
    {
        "no_unapproved_external_models",
        "gaira_risk_assessed",
        "gaira_context_documented",
        "production_monitoring",
    }
)


def has_active_breach(evaluator_key: str | None, detail: dict[str, Any]) -> bool:
    if not evaluator_key or evaluator_key not in BREACH_EVALUATORS:
        return False
    if evaluator_key == "no_unapproved_external_models":
        return int(detail.get("unapproved", 0)) > 0
    if evaluator_key == "gaira_risk_assessed":
        total = int(detail.get("total", 0))
        assessed = int(detail.get("assessed", 0))
        return total > 0 and assessed < total
    if evaluator_key == "gaira_context_documented":
        total = int(detail.get("total", 0))
        documented = int(detail.get("documented", 0))
        return total > 0 and documented < total
    if evaluator_key == "production_monitoring":
        active = int(detail.get("active", 0))
        monitored = int(detail.get("monitored", 0))
        return active > 0 and monitored < active
    return False


def classify_finding_kind(
    status: str,
    coverage: str,
    evaluator_key: str | None,
    detail: dict[str, Any],
) -> str:
    if coverage == "none" or status == "not_applicable":
        return "out_of_scope"
    if status == "not_assessed":
        return "unchecked"
    if status == "met":
        return "satisfied"

    if status in ("not_met", "partial") and has_active_breach(evaluator_key, detail):
        return "violation"

    if status == "not_met":
        return "alignment_gap"
    if status == "partial":
        return "improvement"
    return "satisfied"
