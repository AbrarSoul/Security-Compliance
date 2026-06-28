"""Evaluate ComplianceGuard evidence against NIST AI RMF controls."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.compliance_model import ComplianceModel
from app.models.compliance_policy import CompliancePolicy
from app.models.compliance_rule import ComplianceRule
from app.models.execution_request import ExecutionRequest
from app.models.execution_result import ExecutionResult
from app.models.gaira import AIApplication, GairaAssessment
from app.models.scan import Scan
from app.models.user_role import UserRole
from app.repositories.gap_repository import GapRepository
from app.services.nist_ai_rmf.framework import NistAiRmfFramework, get_nist_ai_rmf_framework
from app.services.policies.constants import ACTIVE_POLICY_STATUS


@dataclass
class EvaluatorResult:
    status: str
    evidence: list[str] = field(default_factory=list)
    detail: dict[str, Any] = field(default_factory=dict)


class NistAiRmfProfileService:
    """Build a Current Profile from live platform telemetry."""

    def __init__(self, db: AsyncSession, framework: NistAiRmfFramework | None = None):
        self.db = db
        self.framework = framework or get_nist_ai_rmf_framework()
        self._cache: dict[str, EvaluatorResult] | None = None

    async def get_controls_catalog(self) -> dict[str, Any]:
        data = self.framework.data
        return {
            "version": self.framework.version,
            "source": data.get("source"),
            "source_url": data.get("source_url"),
            "playbook_url": data.get("playbook_url"),
            "profile": self.framework.profile,
            "trustworthiness_characteristics": data.get("trustworthiness_characteristics", []),
            "control_count": data.get("control_count", len(self.framework.controls)),
            "controls": self.framework.controls,
        }

    async def get_current_profile(self) -> dict[str, Any]:
        await self._ensure_cache()
        assert self._cache is not None

        controls_out: list[dict[str, Any]] = []
        summary = {"met": 0, "partial": 0, "not_met": 0, "not_assessed": 0, "not_applicable": 0}
        by_function: dict[str, dict[str, int]] = {}

        for control in self.framework.controls:
            cid = control["id"]
            fn = control["function"]
            evaluator_key = control.get("evaluator")
            static_coverage = control.get("coverage", "partial")

            if evaluator_key and evaluator_key in self._cache:
                result = self._cache[evaluator_key]
                status = result.status
                evidence = result.evidence
                detail = result.detail
            elif static_coverage == "none":
                status = "not_applicable"
                evidence = []
                detail = {"reason": control.get("notes") or "Out of platform scope"}
            else:
                status = "not_assessed"
                evidence = []
                detail = {
                    "reason": control.get("notes") or "Manual attestation or future automation required"
                }

            summary[status] = summary.get(status, 0) + 1
            by_function.setdefault(
                fn, {"met": 0, "partial": 0, "not_met": 0, "not_assessed": 0, "not_applicable": 0}
            )
            by_function[fn][status] = by_function[fn].get(status, 0) + 1

            controls_out.append(
                {
                    "id": cid,
                    "function": fn,
                    "category_id": control.get("category_id"),
                    "text": control.get("text"),
                    "evidence_type": control.get("evidence_type"),
                    "coverage": static_coverage,
                    "modules": control.get("modules", []),
                    "trustworthiness": control.get("trustworthiness", []),
                    "status": status,
                    "evidence": evidence,
                    "detail": detail,
                    "notes": control.get("notes"),
                }
            )

        total = len(controls_out)
        automated = sum(1 for c in controls_out if c["status"] in ("met", "partial", "not_met"))
        score = round((summary["met"] + summary["partial"] * 0.5) / total * 100, 1) if total else 0.0

        return {
            "profile_id": self.framework.profile.get("id"),
            "profile_name": self.framework.profile.get("name"),
            "framework_version": self.framework.version,
            "evaluated_at": datetime.now(UTC).isoformat(),
            "alignment_score": score,
            "summary": {**summary, "total": total, "automated_evaluations": automated},
            "by_function": by_function,
            "controls": controls_out,
            "disclaimer": (
                "This profile shows operational alignment with NIST AI RMF outcomes based on "
                "ComplianceGuard telemetry. It is not NIST certification or conformance."
            ),
        }

    async def _ensure_cache(self) -> None:
        if self._cache is not None:
            return
        self._cache = {
            "org_has_enabled_rules": await self._eval_org_has_enabled_rules(),
            "org_has_active_controls": await self._eval_org_has_active_controls(),
            "org_has_audit_and_gaps": await self._eval_org_has_audit_and_gaps(),
            "roaia_inventory": await self._eval_roaia_inventory(),
            "rbac_roles_configured": await self._eval_rbac_roles_configured(),
            "gaira_leadership_decisions": await self._eval_gaira_leadership_decisions(),
            "gaira_documentation": await self._eval_gaira_leadership_decisions(),
            "gaira_context_documented": await self._eval_gaira_context_documented(),
            "gaira_risk_assessed": await self._eval_gaira_risk_assessed(),
            "no_unapproved_external_models": await self._eval_no_unapproved_external_models(),
            "execution_blocking": await self._eval_execution_blocking(),
            "models_registry_populated": await self._eval_roaia_inventory(),
            "production_monitoring": await self._eval_production_monitoring(),
            "security_controls_active": await self._eval_security_controls_active(),
            "privacy_scanning_active": await self._eval_privacy_scanning_active(),
            "gap_analysis_recent": await self._eval_gap_analysis_recent(),
            "risk_tracking_active": await self._eval_risk_tracking_active(),
            "incident_detection": await self._eval_incident_detection(),
        }

    async def _eval_org_has_enabled_rules(self) -> EvaluatorResult:
        count = await self.db.scalar(
            select(func.count()).select_from(ComplianceRule).where(ComplianceRule.is_enabled.is_(True))
        )
        count = int(count or 0)
        if count >= 3:
            return EvaluatorResult("met", [f"{count} compliance rules enabled"], {"enabled_rules": count})
        if count > 0:
            return EvaluatorResult("partial", [f"{count} compliance rules enabled"], {"enabled_rules": count})
        return EvaluatorResult("not_met", [], {"enabled_rules": 0})

    async def _eval_org_has_active_controls(self) -> EvaluatorResult:
        rules = await self._eval_org_has_enabled_rules()
        policies = await self.db.scalar(
            select(func.count())
            .select_from(CompliancePolicy)
            .where(CompliancePolicy.status == ACTIVE_POLICY_STATUS)
        )
        policies = int(policies or 0)
        evidence = list(rules.evidence)
        if policies > 0:
            evidence.append(f"{policies} active compliance policies")
        if rules.status == "met" and policies > 0:
            return EvaluatorResult(
                "met",
                evidence,
                {"enabled_rules": rules.detail.get("enabled_rules"), "active_policies": policies},
            )
        if rules.status in ("met", "partial") or policies > 0:
            return EvaluatorResult(
                "partial",
                evidence,
                {"enabled_rules": rules.detail.get("enabled_rules"), "active_policies": policies},
            )
        return EvaluatorResult("not_met", [], {"active_policies": policies})

    async def _eval_org_has_audit_and_gaps(self) -> EvaluatorResult:
        since = datetime.now(UTC) - timedelta(days=30)
        audit_count = await self.db.scalar(
            select(func.count()).select_from(AuditLog).where(AuditLog.created_at >= since)
        )
        audit_count = int(audit_count or 0)
        gap_repo = GapRepository(self.db)
        latest = await gap_repo.get_latest_run()
        evidence: list[str] = []
        if audit_count > 0:
            evidence.append(f"{audit_count} audit events in last 30 days")
        if latest and latest.completed_at:
            evidence.append(f"Latest gap analysis run {latest.completed_at.date().isoformat()}")
        if audit_count >= 10 and latest:
            return EvaluatorResult(
                "met",
                evidence,
                {"audit_events_30d": audit_count, "latest_gap_run": str(latest.id)},
            )
        if audit_count > 0 or latest:
            return EvaluatorResult(
                "partial",
                evidence,
                {"audit_events_30d": audit_count, "has_gap_run": latest is not None},
            )
        return EvaluatorResult("not_met", [], {"audit_events_30d": 0})

    async def _eval_roaia_inventory(self) -> EvaluatorResult:
        apps = await self.db.scalar(
            select(func.count()).select_from(AIApplication).where(AIApplication.is_active.is_(True))
        )
        models = await self.db.scalar(
            select(func.count()).select_from(ComplianceModel).where(ComplianceModel.is_active.is_(True))
        )
        apps = int(apps or 0)
        models = int(models or 0)
        evidence = []
        if apps > 0:
            evidence.append(f"{apps} active AI applications (ROAIA)")
        if models > 0:
            evidence.append(f"{models} active models in registry")
        if apps > 0 and models > 0:
            return EvaluatorResult("met", evidence, {"applications": apps, "models": models})
        if apps > 0 or models > 0:
            return EvaluatorResult("partial", evidence, {"applications": apps, "models": models})
        return EvaluatorResult("not_met", [], {"applications": 0, "models": 0})

    async def _eval_rbac_roles_configured(self) -> EvaluatorResult:
        count = await self.db.scalar(select(func.count()).select_from(UserRole))
        count = int(count or 0)
        if count >= 3:
            return EvaluatorResult("met", [f"{count} user-role assignments"], {"assignments": count})
        if count > 0:
            return EvaluatorResult("partial", [f"{count} user-role assignments"], {"assignments": count})
        return EvaluatorResult("not_met", [], {"assignments": 0})

    async def _eval_gaira_leadership_decisions(self) -> EvaluatorResult:
        submitted = await self.db.scalar(
            select(func.count())
            .select_from(GairaAssessment)
            .where(GairaAssessment.status == "submitted")
        )
        submitted = int(submitted or 0)
        with_decision = await self.db.scalar(
            select(func.count())
            .select_from(GairaAssessment)
            .where(
                GairaAssessment.status == "submitted",
                GairaAssessment.proceed_decision.isnot(None),
            )
        )
        with_decision = int(with_decision or 0)
        if submitted > 0 and with_decision == submitted:
            return EvaluatorResult(
                "met",
                [f"{submitted} submitted assessments with proceed/no-go decisions"],
                {"submitted": submitted, "with_decision": with_decision},
            )
        if submitted > 0:
            return EvaluatorResult(
                "partial",
                [f"{submitted} submitted assessments, {with_decision} with explicit decisions"],
                {"submitted": submitted, "with_decision": with_decision},
            )
        return EvaluatorResult("not_met", [], {"submitted": 0})

    async def _eval_gaira_context_documented(self) -> EvaluatorResult:
        total = await self.db.scalar(
            select(func.count()).select_from(AIApplication).where(AIApplication.is_active.is_(True))
        )
        documented = await self.db.scalar(
            select(func.count())
            .select_from(AIApplication)
            .where(
                AIApplication.is_active.is_(True),
                AIApplication.purpose.isnot(None),
                AIApplication.purpose != "",
            )
        )
        total = int(total or 0)
        documented = int(documented or 0)
        if total > 0 and documented == total:
            return EvaluatorResult(
                "met",
                [f"{documented}/{total} applications with documented purpose/context"],
                {"documented": documented, "total": total},
            )
        if documented > 0:
            return EvaluatorResult(
                "partial",
                [f"{documented}/{total} applications with documented purpose/context"],
                {"documented": documented, "total": total},
            )
        return EvaluatorResult("not_met", [], {"documented": 0, "total": total})

    async def _eval_gaira_risk_assessed(self) -> EvaluatorResult:
        apps = await self.db.scalar(
            select(func.count()).select_from(AIApplication).where(AIApplication.is_active.is_(True))
        )
        assessed = await self.db.scalar(
            select(func.count())
            .select_from(AIApplication)
            .where(AIApplication.is_active.is_(True), AIApplication.gaira_status == "done")
        )
        apps = int(apps or 0)
        assessed = int(assessed or 0)
        if apps > 0 and assessed == apps:
            return EvaluatorResult(
                "met",
                [f"{assessed}/{apps} applications with completed GAIRA status"],
                {"assessed": assessed, "total": apps},
            )
        if assessed > 0:
            return EvaluatorResult(
                "partial",
                [f"{assessed}/{apps} applications with completed GAIRA status"],
                {"assessed": assessed, "total": apps},
            )
        return EvaluatorResult("not_met", [], {"assessed": 0, "total": apps})

    async def _eval_no_unapproved_external_models(self) -> EvaluatorResult:
        total = await self.db.scalar(
            select(func.count())
            .select_from(ComplianceModel)
            .where(
                ComplianceModel.is_active.is_(True),
                ComplianceModel.model_type.in_(("external_api", "cloud_hosted")),
            )
        )
        unapproved = await self.db.scalar(
            select(func.count())
            .select_from(ComplianceModel)
            .where(
                ComplianceModel.is_active.is_(True),
                ComplianceModel.model_type.in_(("external_api", "cloud_hosted")),
                ComplianceModel.is_approved.is_(False),
            )
        )
        total = int(total or 0)
        unapproved = int(unapproved or 0)
        if total == 0:
            return EvaluatorResult("partial", ["No external/cloud models registered"], {"external_models": 0})
        if unapproved == 0:
            return EvaluatorResult(
                "met",
                [f"All {total} external/cloud models are approved"],
                {"external_models": total, "unapproved": 0},
            )
        return EvaluatorResult(
            "not_met",
            [f"{unapproved}/{total} external/cloud models are not approved"],
            {"external_models": total, "unapproved": unapproved},
        )

    async def _eval_execution_blocking(self) -> EvaluatorResult:
        blocked = await self.db.scalar(
            select(func.count())
            .select_from(ExecutionResult)
            .where(ExecutionResult.decision == "block")
        )
        total = await self.db.scalar(select(func.count()).select_from(ExecutionRequest))
        blocked = int(blocked or 0)
        total = int(total or 0)
        if total == 0:
            return EvaluatorResult(
                "partial",
                ["Execution validation available; no executions recorded yet"],
                {"executions": 0},
            )
        evidence = [f"{total} execution validations recorded"]
        if blocked > 0:
            evidence.append(f"{blocked} blocked by policy")
        return EvaluatorResult(
            "met" if blocked > 0 or total >= 5 else "partial",
            evidence,
            {"executions": total, "blocked": blocked},
        )

    async def _eval_production_monitoring(self) -> EvaluatorResult:
        monitored = await self.db.scalar(
            select(func.count())
            .select_from(ComplianceModel)
            .where(ComplianceModel.is_active.is_(True), ComplianceModel.logging_enabled.is_(True))
        )
        active = await self.db.scalar(
            select(func.count()).select_from(ComplianceModel).where(ComplianceModel.is_active.is_(True))
        )
        monitored = int(monitored or 0)
        active = int(active or 0)
        if active > 0 and monitored == active:
            return EvaluatorResult(
                "met",
                [f"Logging enabled on all {active} active models"],
                {"monitored": monitored, "active": active},
            )
        if monitored > 0:
            return EvaluatorResult(
                "partial",
                [f"Logging enabled on {monitored}/{active} active models"],
                {"monitored": monitored, "active": active},
            )
        return EvaluatorResult("not_met", [], {"monitored": 0, "active": active})

    async def _eval_security_controls_active(self) -> EvaluatorResult:
        rules = await self._eval_org_has_enabled_rules()
        scans = await self.db.scalar(select(func.count()).select_from(Scan))
        scans = int(scans or 0)
        evidence = list(rules.evidence)
        if scans > 0:
            evidence.append(f"{scans} dataset scans completed")
        if rules.status in ("met", "partial") and scans > 0:
            return EvaluatorResult("met", evidence, {"scans": scans})
        if rules.status != "not_met" or scans > 0:
            return EvaluatorResult("partial", evidence, {"scans": scans})
        return EvaluatorResult("not_met", [], {"scans": 0})

    async def _eval_privacy_scanning_active(self) -> EvaluatorResult:
        scans = await self.db.scalar(select(func.count()).select_from(Scan))
        scans = int(scans or 0)
        if scans >= 5:
            return EvaluatorResult("met", [f"{scans} scans with PII/sensitive-data detectors"], {"scans": scans})
        if scans > 0:
            return EvaluatorResult("partial", [f"{scans} scans completed"], {"scans": scans})
        return EvaluatorResult("not_met", [], {"scans": 0})

    async def _eval_gap_analysis_recent(self) -> EvaluatorResult:
        gap_repo = GapRepository(self.db)
        latest = await gap_repo.get_latest_run()
        if latest and latest.completed_at:
            age_days = (datetime.now(UTC) - latest.completed_at).days
            status = "met" if age_days <= 30 else "partial"
            return EvaluatorResult(
                status,
                [f"Gap analysis last run {latest.completed_at.date().isoformat()}"],
                {"latest_run_id": str(latest.id), "age_days": age_days, "gaps_found": latest.gaps_found},
            )
        return EvaluatorResult("not_met", [], {"has_run": False})

    async def _eval_risk_tracking_active(self) -> EvaluatorResult:
        gaps = await self._eval_gap_analysis_recent()
        scans = await self.db.scalar(select(func.count()).select_from(Scan))
        scans = int(scans or 0)
        evidence = list(gaps.evidence)
        if scans > 0:
            evidence.append(f"{scans} scans for trend analysis")
        if gaps.status == "met" and scans > 0:
            return EvaluatorResult("met", evidence, {**gaps.detail, "scans": scans})
        if gaps.status != "not_met" or scans > 0:
            return EvaluatorResult("partial", evidence, {**gaps.detail, "scans": scans})
        return EvaluatorResult("not_met", [], {"scans": 0})

    async def _eval_incident_detection(self) -> EvaluatorResult:
        since = datetime.now(UTC) - timedelta(days=90)
        audit_count = await self.db.scalar(
            select(func.count()).select_from(AuditLog).where(AuditLog.created_at >= since)
        )
        audit_count = int(audit_count or 0)
        if audit_count >= 5:
            return EvaluatorResult(
                "met",
                [f"{audit_count} audit events in 90 days (includes guard/threat activity)"],
                {"audit_events_90d": audit_count},
            )
        if audit_count > 0:
            return EvaluatorResult(
                "partial",
                [f"{audit_count} audit events in 90 days"],
                {"audit_events_90d": audit_count},
            )
        return EvaluatorResult("not_met", [], {"audit_events_90d": 0})
