"""Unified compliance posture across frameworks."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance_gap import ComplianceGap
from app.services.compliance.framework_mappings import (
    FRAMEWORK_CATALOG,
    FRAMEWORK_GAIRA,
    FRAMEWORK_INTERNAL_GUARDRAILS,
    FRAMEWORK_NIST_AI_RMF,
    gap_belongs_to_framework,
    resolve_framework_refs,
)
from app.services.gaps.gap_service import GapAnalysisService
from app.services.nist_ai_rmf.profile_service import NistAiRmfProfileService


def _framework_status_from_gaps(gaps: list[ComplianceGap]) -> str:
    if not gaps:
        return "met"
    severities = {g.severity for g in gaps}
    if severities & {"critical", "high"}:
        return "not_met"
    if severities & {"medium"}:
        return "partial"
    return "partial"


def _nist_overall_status(summary: dict[str, int]) -> str:
    if summary.get("not_met", 0) > 0:
        return "not_met"
    if summary.get("partial", 0) > 0:
        return "partial"
    if summary.get("met", 0) > 0:
        return "met"
    return "not_assessed"


def _gap_issue(gap: ComplianceGap) -> dict[str, Any]:
    refs = resolve_framework_refs(gap)
    return {
        "id": str(gap.id),
        "title": gap.title,
        "severity": gap.severity,
        "remediation": gap.recommendation,
        "source": "gap",
        "gap_type": gap.gap_type,
        "control_ids": [r["control_id"] for r in refs if r["framework"]],
        "framework_refs": refs,
        "resource_type": gap.resource_type,
        "resource_id": str(gap.resource_id) if gap.resource_id else None,
    }


class CompliancePostureService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.gap_service = GapAnalysisService(db)
        self.nist_service = NistAiRmfProfileService(db)

    async def get_posture(self) -> dict[str, Any]:
        gaps, _, latest_run = await self.gap_service.list_current_gaps(limit=200)
        nist_profile = await self.nist_service.get_current_profile()
        evaluated_at = datetime.now(UTC).isoformat()

        nist_gaps = [g for g in gaps if gap_belongs_to_framework(g, FRAMEWORK_NIST_AI_RMF)]
        internal_gaps = [
            g for g in gaps if gap_belongs_to_framework(g, FRAMEWORK_INTERNAL_GUARDRAILS)
        ]
        gaira_gaps = [g for g in gaps if gap_belongs_to_framework(g, FRAMEWORK_GAIRA)]

        nist_not_met_controls = [
            c
            for c in nist_profile["controls"]
            if c["status"] in ("not_met", "partial")
        ][:15]

        nist_gap_issues = [_gap_issue(g) for g in nist_gaps]

        nist_control_issues = [
            {
                "id": c["id"],
                "title": f"{c['id']}: {c['text'][:120]}{'…' if len(c['text']) > 120 else ''}",
                "severity": "high" if c["status"] == "not_met" else "medium",
                "remediation": (
                    "; ".join(c["evidence"])
                    if c["evidence"]
                    else (c.get("notes") or "Review control requirements and platform evidence.")
                ),
                "source": "nist_control",
                "gap_type": None,
                "control_ids": [c["id"]],
                "framework_refs": [{"framework": FRAMEWORK_NIST_AI_RMF, "control_id": c["id"]}],
                "resource_type": None,
                "resource_id": None,
            }
            for c in nist_not_met_controls
        ]

        nist_open_issues = (nist_gap_issues + nist_control_issues)[:20]

        frameworks: list[dict[str, Any]] = [
            {
                "id": FRAMEWORK_NIST_AI_RMF,
                "name": FRAMEWORK_CATALOG[FRAMEWORK_NIST_AI_RMF]["name"],
                "description": FRAMEWORK_CATALOG[FRAMEWORK_NIST_AI_RMF]["description"],
                "status": _nist_overall_status(nist_profile["summary"]),
                "alignment_score": nist_profile["alignment_score"],
                "summary": nist_profile["summary"],
                "open_issue_count": len(nist_gaps) + nist_profile["summary"].get("not_met", 0),
                "open_issues": nist_open_issues,
                "detail_url": "/nist-ai-rmf",
            },
            {
                "id": FRAMEWORK_GAIRA,
                "name": FRAMEWORK_CATALOG[FRAMEWORK_GAIRA]["name"],
                "description": FRAMEWORK_CATALOG[FRAMEWORK_GAIRA]["description"],
                "status": _framework_status_from_gaps(gaira_gaps),
                "alignment_score": _score_from_gaps(gaira_gaps),
                "summary": _gap_summary(gaira_gaps),
                "open_issue_count": len(gaira_gaps),
                "open_issues": [_gap_issue(g) for g in gaira_gaps[:20]],
                "detail_url": "/gaira",
            },
            {
                "id": FRAMEWORK_INTERNAL_GUARDRAILS,
                "name": FRAMEWORK_CATALOG[FRAMEWORK_INTERNAL_GUARDRAILS]["name"],
                "description": FRAMEWORK_CATALOG[FRAMEWORK_INTERNAL_GUARDRAILS]["description"],
                "status": _framework_status_from_gaps(internal_gaps),
                "alignment_score": _score_from_gaps(internal_gaps),
                "summary": _gap_summary(internal_gaps),
                "open_issue_count": len(internal_gaps),
                "open_issues": [_gap_issue(g) for g in internal_gaps[:20]],
                "detail_url": "/gaps",
            },
        ]

        return {
            "evaluated_at": evaluated_at,
            "last_gap_analysis_at": (
                (latest_run.completed_at or latest_run.started_at).isoformat()
                if latest_run
                else None
            ),
            "frameworks": frameworks,
            "disclaimer": (
                "Framework posture shows operational alignment from ComplianceGuard telemetry. "
                "It is not official certification or conformance with any standard."
            ),
        }


def _gap_summary(gaps: list[ComplianceGap]) -> dict[str, int]:
    return {
        "total": len(gaps),
        "critical": sum(1 for g in gaps if g.severity == "critical"),
        "high": sum(1 for g in gaps if g.severity == "high"),
        "medium": sum(1 for g in gaps if g.severity == "medium"),
        "low": sum(1 for g in gaps if g.severity == "low"),
    }


def _score_from_gaps(gaps: list[ComplianceGap]) -> float:
    if not gaps:
        return 100.0
    penalty = sum(
        {"critical": 25, "high": 15, "medium": 8, "low": 3}.get(g.severity, 5) for g in gaps
    )
    return max(0.0, round(100.0 - min(penalty, 100), 1))
