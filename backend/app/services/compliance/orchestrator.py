"""Orchestrates rule, policy, and model compliance evaluation (single evaluation pass)."""

from dataclasses import dataclass

from app.models.compliance_model import ComplianceModel
from app.services.compliance.deployment import deployment_flags
from app.services.model_compliance import DatasetContext, ModelComplianceChecker
from app.services.model_compliance.types import ModelComplianceCheckResult
from app.services.policies.evaluation import PolicyEvaluationEngine
from app.services.policies.types import PoliciesEvaluationResult
from app.services.rules.context import context_from_scan
from app.services.rules.engine import RuleEngine
from app.services.rules.types import RuleEvaluationContext, RuleEvaluationResult


@dataclass(frozen=True)
class ComplianceEvaluationBundle:
    rule_result: RuleEvaluationResult
    policy_result: PoliciesEvaluationResult
    model_result: ModelComplianceCheckResult
    rule_context: RuleEvaluationContext


class ComplianceEvaluationOrchestrator:
    """
    Shared evaluation pipeline for execution validation and model compliance.

    Rules and policies are evaluated once; model built-in risk checks run separately
    to avoid duplicate rule/policy evaluation inside ModelComplianceChecker.
    """

    def __init__(
        self,
        rule_engine: RuleEngine | None = None,
        policy_engine: PolicyEvaluationEngine | None = None,
        model_checker: ModelComplianceChecker | None = None,
    ):
        self.rule_engine = rule_engine or RuleEngine()
        self.policy_engine = policy_engine or PolicyEvaluationEngine(self.rule_engine)
        self.model_checker = model_checker or ModelComplianceChecker(
            self.rule_engine, self.policy_engine
        )

    @staticmethod
    def dataset_from_scan(scan) -> DatasetContext:
        return DatasetContext(
            detected_types={f.finding_type for f in (scan.findings or [])},
            classification=scan.classification,
            risk_score=scan.risk_score,
            compliance_status=scan.compliance_status,
        )

    @staticmethod
    def rule_context_from_scan(scan, model: ComplianceModel) -> RuleEvaluationContext:
        deployment, is_external = deployment_flags(model)
        return context_from_scan(
            scan,
            model_is_external=is_external,
            model_deployment=deployment,
            model_provider=model.provider,
        )

    def evaluate(
        self,
        scan,
        model: ComplianceModel,
        *,
        active_policies: list,
        enabled_rules: list,
    ) -> ComplianceEvaluationBundle:
        dataset = self.dataset_from_scan(scan)
        rule_ctx = self.rule_context_from_scan(scan, model)

        rule_result = self.rule_engine.evaluate(enabled_rules, rule_ctx)
        policy_result = self.policy_engine.evaluate_policies(active_policies, rule_ctx)
        model_result = self.model_checker.check(dataset, model, scan=scan)

        return ComplianceEvaluationBundle(
            rule_result=rule_result,
            policy_result=policy_result,
            model_result=model_result,
            rule_context=rule_ctx,
        )

    def evaluate_runtime(
        self,
        rule_ctx: RuleEvaluationContext,
        *,
        active_policies: list,
        enabled_rules: list,
    ) -> tuple[RuleEvaluationResult, PoliciesEvaluationResult]:
        """Rules + policies only (no model re-check) for live guard enforcement."""
        rule_result = self.rule_engine.evaluate(enabled_rules, rule_ctx)
        policy_result = self.policy_engine.evaluate_policies(active_policies, rule_ctx)
        return rule_result, policy_result
