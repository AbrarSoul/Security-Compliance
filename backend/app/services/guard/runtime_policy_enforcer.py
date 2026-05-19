"""Runtime rule and policy evaluation during live execution."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.compliance_policy_repository import CompliancePolicyRepository
from app.repositories.compliance_rule_repository import ComplianceRuleRepository
from app.repositories.execution_repository import ExecutionRepository
from app.services.compliance.deployment import deployment_flags
from app.services.compliance.orchestrator import ComplianceEvaluationOrchestrator
from app.services.execution.constants import DECISION_ORDER
from app.services.guard.finding_mapper import findings_to_detected_types
from app.services.policies.types import PoliciesEvaluationResult
from app.services.rules.context import context_from_scan
from app.services.rules.types import RuleEvaluationContext, RuleEvaluationResult


class RuntimePolicyEnforcer:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.executions = ExecutionRepository(db)
        self.policies = CompliancePolicyRepository(db)
        self.rules = ComplianceRuleRepository(db)
        self.orchestrator = ComplianceEvaluationOrchestrator()

    async def evaluate(
        self,
        execution_request_id: UUID,
        *,
        runtime_finding_types: list[str],
        runtime_risk_score: int = 0,
    ) -> tuple[RuleEvaluationResult, PoliciesEvaluationResult, RuleEvaluationContext]:
        request = await self.executions.get_request_by_id(execution_request_id)
        if request is None or request.scan is None or request.compliance_model is None:
            empty_rules = RuleEvaluationResult()
            empty_policies = PoliciesEvaluationResult()
            return empty_rules, empty_policies, RuleEvaluationContext()

        scan = request.scan
        model = request.compliance_model
        deployment, is_external = deployment_flags(model)

        base_ctx = context_from_scan(
            scan,
            model_is_external=is_external,
            model_deployment=deployment,
            model_provider=model.provider,
        )
        runtime_types = findings_to_detected_types(runtime_finding_types)
        merged_types = set(base_ctx.detected_types) | runtime_types

        rule_ctx = RuleEvaluationContext(
            detected_types=merged_types,
            risk_score=max(base_ctx.risk_score or 0, runtime_risk_score),
            compliance_status=base_ctx.compliance_status,
            classification=base_ctx.classification,
            model_is_external=base_ctx.model_is_external,
            model_deployment=base_ctx.model_deployment,
            model_provider=base_ctx.model_provider,
            findings_count=base_ctx.findings_count + len(runtime_finding_types),
            extra={
                **base_ctx.extra,
                "runtime_guard": True,
                "runtime_finding_types": list(runtime_finding_types),
            },
        )

        enabled_rules = await self.rules.list_enabled_for_evaluation()
        active_policies = await self.policies.list_active_policies()
        rule_result, policy_result = self.orchestrator.evaluate_runtime(
            rule_ctx,
            active_policies=active_policies,
            enabled_rules=enabled_rules,
        )
        return rule_result, policy_result, rule_ctx

    @staticmethod
    def policy_violations(policy_result: PoliciesEvaluationResult) -> list[dict]:
        violations = []
        for pr in policy_result.policy_results:
            if pr.recommended_action in ("block", "warn"):
                violations.append(pr.to_dict())
        return violations

    @staticmethod
    def worst_policy_decision(policy_result: PoliciesEvaluationResult) -> str:
        decisions = [pr.recommended_action for pr in policy_result.policy_results]
        if not decisions:
            return "allow"
        return max(decisions, key=lambda d: DECISION_ORDER.get(d, 0))
