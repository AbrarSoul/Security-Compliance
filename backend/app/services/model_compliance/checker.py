"""Model compliance checker integrating built-in checks, rules, and policies."""

from typing import Any

from app.models.compliance_model import ComplianceModel
from app.services.model_compliance.checks import build_model_context, run_model_risk_checks
from app.services.model_compliance.constants import (
    DECISION_ORDER,
    RISK_LEVEL_ORDER,
    RISK_POINTS,
)
from app.services.model_compliance.types import (
    DatasetContext,
    ModelComplianceCheckResult,
    ModelRiskCheck,
)
from app.services.policies.evaluation import PolicyEvaluationEngine
from app.services.rules.context import context_from_scan
from app.services.rules.engine import RuleEngine
from app.services.rules.types import RuleEvaluationContext


class ModelComplianceChecker:
    def __init__(
        self,
        rule_engine: RuleEngine | None = None,
        policy_engine: PolicyEvaluationEngine | None = None,
    ):
        self.rule_engine = rule_engine or RuleEngine()
        self.policy_engine = policy_engine or PolicyEvaluationEngine(self.rule_engine)

    def check(
        self,
        dataset: DatasetContext,
        model: ComplianceModel,
        *,
        scan=None,
        active_policies=None,
        enabled_rules: list | None = None,
    ) -> ModelComplianceCheckResult:
        model_ctx = build_model_context(model)
        risk_checks = run_model_risk_checks(dataset, model_ctx)

        rule_ctx = self._build_rule_context(dataset, model, scan=scan)
        rule_eval = None
        policy_eval = None

        if enabled_rules is not None:
            rule_result = self.rule_engine.evaluate(enabled_rules, rule_ctx)
            rule_eval = rule_result.to_dict()

        if active_policies is not None:
            policy_result = self.policy_engine.evaluate_policies(
                active_policies,
                rule_ctx,
            )
            policy_eval = policy_result.to_dict()

        decision, risk_level, risk_score, primary_reason = self._aggregate(
            risk_checks=risk_checks,
            rule_eval=rule_eval,
            policy_eval=policy_eval,
            dataset=dataset,
            model_ctx=model_ctx,
        )
        recommendations = self._recommendations(
            decision=decision,
            dataset=dataset,
            model_ctx=model_ctx,
            risk_checks=risk_checks,
        )

        return ModelComplianceCheckResult(
            risk_checks=risk_checks,
            risk_level=risk_level,
            risk_score=risk_score,
            decision=decision,
            primary_reason=primary_reason,
            recommendations=recommendations,
            rule_evaluation=rule_eval,
            policy_evaluation=policy_eval,
        )

    def _build_rule_context(
        self,
        dataset: DatasetContext,
        model: ComplianceModel,
        *,
        scan=None,
    ) -> RuleEvaluationContext:
        if scan is not None:
            deployment, is_external = self._deployment_flags(model)
            return context_from_scan(
                scan,
                model_is_external=is_external,
                model_deployment=deployment,
                model_provider=model.provider,
            )

        deployment, is_external = self._deployment_flags(model)
        return RuleEvaluationContext(
            detected_types=set(dataset.detected_types),
            risk_score=dataset.risk_score,
            compliance_status=dataset.compliance_status,
            classification=dataset.classification,
            model_is_external=is_external,
            model_deployment=deployment,
            model_provider=model.provider,
            findings_count=len(dataset.detected_types),
        )

    @staticmethod
    def _deployment_flags(model: ComplianceModel) -> tuple[str | None, bool]:
        mapping = {
            "local_model": ("local", False),
            "external_api": ("external", True),
            "cloud_hosted": ("cloud", True),
            "open_source": ("local", False),
            "proprietary": ("cloud", True),
        }
        deployment, is_external = mapping.get(
            model.model_type, ("external", model.data_leaves_platform)
        )
        if model.data_leaves_platform:
            is_external = True
        return deployment, is_external

    def _aggregate(
        self,
        *,
        risk_checks: list[ModelRiskCheck],
        rule_eval: dict[str, Any] | None,
        policy_eval: dict[str, Any] | None,
        dataset: DatasetContext,
        model_ctx,
    ) -> tuple[str, str, int, str]:
        decisions: list[tuple[str, str, str]] = []

        for check in risk_checks:
            decisions.append(
                (check.suggested_action, check.risk_level, check.description)
            )

        if rule_eval and rule_eval.get("triggered_rules"):
            decisions.append(
                (
                    rule_eval["recommended_action"],
                    rule_eval.get("aggregated_severity") or "medium",
                    rule_eval["decision_reason"],
                )
            )

        if policy_eval and policy_eval.get("policy_results"):
            decisions.append(
                (
                    policy_eval["recommended_action"],
                    self._policy_worst_severity(policy_eval),
                    policy_eval["decision_reason"],
                )
            )

        if not decisions:
            return "allow", "low", 0, "No significant model compliance risks detected"

        worst_decision = max(decisions, key=lambda d: DECISION_ORDER.get(d[0], 0))
        worst_level = max(
            (d[1] for d in decisions),
            key=lambda level: RISK_LEVEL_ORDER.get(level, 0),
        )
        risk_score = min(
            100,
            sum(RISK_POINTS.get(c.risk_level, 10) for c in risk_checks)
            + (rule_eval or {}).get("aggregated_risk_score", 0) // 2,
        )

        primary_reason = worst_decision[2]
        if dataset.is_high_risk_classification and model_ctx.is_external:
            primary_reason = (
                "Confidential or restricted data is being sent to an external model"
            )

        return worst_decision[0], worst_level, risk_score, primary_reason

    @staticmethod
    def _policy_worst_severity(policy_eval: dict[str, Any]) -> str:
        severities = []
        for result in policy_eval.get("policy_results", []):
            sev = result.get("rule_evaluation", {}).get("aggregated_severity")
            if sev:
                severities.append(sev)
            if result.get("threshold_action") == "block":
                severities.append("critical")
        if not severities:
            return "medium"
        return max(severities, key=lambda s: {"low": 0, "medium": 1, "high": 2, "critical": 3}.get(s, 0))

    @staticmethod
    def _recommendations(
        *,
        decision: str,
        dataset: DatasetContext,
        model_ctx,
        risk_checks: list[ModelRiskCheck],
    ) -> list[str]:
        recs: list[str] = []
        codes = {c.code for c in risk_checks}

        if dataset.is_high_risk_classification and model_ctx.is_external:
            recs.append("Anonymize or de-identify the dataset before using an external model")
            recs.append("Use an approved local model instead of an external API")

        if "external_api_sensitive_data" in codes or "confidential_data_external" in codes:
            if "Anonymize or de-identify the dataset before using an external model" not in recs:
                recs.append(
                    "Anonymize or de-identify the dataset before using an external model"
                )
            recs.append("Use a local or on-premise model that keeps data within your platform")

        if "unapproved_endpoint" in codes:
            recs.append("Register and approve this model endpoint before production use")

        if "unknown_provider" in codes:
            recs.append("Verify the model provider and document data handling practices")

        if "model_logs_prompts" in codes:
            recs.append("Disable prompt logging or remove sensitive fields from the dataset")

        if "lacks_privacy_metadata" in codes:
            recs.append("Document data retention policy and logging settings for this model")

        if decision == "allow" and not recs:
            recs.append("Model and dataset pairing appears compliant under current policies")

        return list(dict.fromkeys(recs))
