import uuid
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance_policy import CompliancePolicy
from app.models.compliance_rule import ComplianceRule
from app.repositories.compliance_policy_repository import CompliancePolicyRepository
from app.schemas.policies import (
    AttachPolicyRulesRequest,
    CompliancePolicyCreate,
    CompliancePolicyResponse,
    CompliancePolicyUpdate,
    DetachPolicyRulesRequest,
    EvaluatePoliciesRequest,
    PoliciesEvaluationResponse,
    PolicyEvaluationResponse,
    PolicyThresholdsSchema,
)
from app.schemas.rules import RuleEvaluationResponse, TriggeredRuleResponse
from app.services.audit_service import AuditService
from app.services.policies.constants import ACTIVE_POLICY_STATUS, POLICY_STATUSES
from app.services.policies.evaluation import PolicyEvaluationEngine
from app.services.policies.thresholds import PolicyThresholdConfig
from app.services.policies.types import PoliciesEvaluationResult, PolicyEvaluationResult
from app.services.rules.types import RuleEvaluationContext


class PolicyService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.policies = CompliancePolicyRepository(db)
        self.evaluation_engine = PolicyEvaluationEngine()
        self.audit = AuditService(db)

    async def list_policies(
        self,
        *,
        status: str | None = None,
        policy_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[CompliancePolicy], int]:
        items = await self.policies.list_policies(
            status=status,
            policy_type=policy_type,
            limit=limit,
            offset=offset,
        )
        total = await self.policies.count_policies(
            status=status,
            policy_type=policy_type,
        )
        return items, total

    async def list_active_policies(self) -> list[CompliancePolicy]:
        return await self.policies.list_active_policies()

    async def get_policy(self, policy_id: UUID) -> CompliancePolicy:
        policy = await self.policies.get_by_id(policy_id)
        if policy is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found"
            )
        return policy

    async def create_policy(
        self,
        payload: CompliancePolicyCreate,
        *,
        created_by_user_id: UUID,
    ) -> CompliancePolicy:
        if payload.status not in POLICY_STATUSES:
            raise HTTPException(status_code=400, detail="Invalid policy status")

        policy = CompliancePolicy(
            id=uuid.uuid4(),
            name=payload.name,
            description=payload.description,
            policy_type=payload.policy_type,
            status=payload.status,
            priority=payload.priority,
            definition_json=self._definition_from_thresholds(payload.thresholds),
            is_active=payload.status == ACTIVE_POLICY_STATUS,
            created_by_user_id=created_by_user_id,
        )
        await self.policies.create(policy)

        if payload.rule_ids:
            await self._attach_rules_internal(
                policy.id,
                payload.rule_ids,
                sort_order=0,
                actor_user_id=created_by_user_id,
                audit_attach=False,
            )

        await self.audit.log_policy_created(
            created_by_user_id,
            policy.id,
            metadata={"name": policy.name, "policy_type": policy.policy_type},
        )
        return await self.get_policy(policy.id)

    async def update_policy(
        self,
        policy_id: UUID,
        payload: CompliancePolicyUpdate,
        *,
        actor_user_id: UUID,
    ) -> CompliancePolicy:
        policy = await self.get_policy(policy_id)
        if policy.status == "archived":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Archived policies cannot be updated",
            )

        changes: dict[str, object] = {}
        if payload.name is not None:
            policy.name = payload.name
            changes["name"] = payload.name
        if payload.description is not None:
            policy.description = payload.description
            changes["description"] = payload.description
        if payload.policy_type is not None:
            policy.policy_type = payload.policy_type
            changes["policy_type"] = payload.policy_type
        if payload.priority is not None:
            policy.priority = payload.priority
            changes["priority"] = payload.priority
        if payload.thresholds is not None:
            definition = dict(policy.definition_json or {})
            definition["thresholds"] = payload.thresholds.model_dump()
            policy.definition_json = definition
            changes["thresholds"] = True

        await self.policies.update(policy)
        await self.audit.log_policy_updated(
            actor_user_id,
            policy.id,
            metadata={"name": policy.name, "changes": changes},
        )
        return await self.get_policy(policy.id)

    async def activate_policy(self, policy_id: UUID, *, actor_user_id: UUID) -> CompliancePolicy:
        return await self._set_status(policy_id, "active", actor_user_id=actor_user_id)

    async def deactivate_policy(
        self, policy_id: UUID, *, actor_user_id: UUID
    ) -> CompliancePolicy:
        return await self._set_status(policy_id, "inactive", actor_user_id=actor_user_id)

    async def archive_policy(self, policy_id: UUID, *, actor_user_id: UUID) -> CompliancePolicy:
        return await self._set_status(policy_id, "archived", actor_user_id=actor_user_id)

    async def attach_rules(
        self,
        policy_id: UUID,
        payload: AttachPolicyRulesRequest,
        *,
        actor_user_id: UUID,
    ) -> CompliancePolicy:
        await self._attach_rules_internal(
            policy_id,
            payload.rule_ids,
            sort_order=payload.sort_order,
            actor_user_id=actor_user_id,
            audit_attach=True,
        )
        return await self.get_policy(policy_id)

    async def detach_rules(
        self,
        policy_id: UUID,
        payload: DetachPolicyRulesRequest,
        *,
        actor_user_id: UUID,
    ) -> CompliancePolicy:
        policy = await self.get_policy(policy_id)
        removed: list[str] = []
        for rule_id in payload.rule_ids:
            if await self.policies.detach_rule(policy.id, rule_id):
                removed.append(str(rule_id))
        if removed:
            await self.audit.log_policy_updated(
                actor_user_id,
                policy.id,
                metadata={"detached_rule_ids": removed},
            )
        return await self.get_policy(policy.id)

    async def evaluate(self, body: EvaluatePoliciesRequest) -> PoliciesEvaluationResult:
        ctx = RuleEvaluationContext(
            detected_types=set(body.detected_types),
            risk_score=body.risk_score,
            compliance_status=body.compliance_status,
            classification=body.classification,
            model_is_external=body.model_is_external,
            model_deployment=body.model_deployment,
            model_provider=body.model_provider,
            findings_count=len(body.detected_types),
        )

        if body.policy_id is not None:
            policy = await self.get_policy(body.policy_id)
            if policy.status != ACTIVE_POLICY_STATUS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Policy is not active",
                )
            result = self.evaluation_engine.evaluate_policy(
                policy,
                ctx,
                validation_score=body.validation_score,
            )
            return PoliciesEvaluationResult(
                policy_results=[result],
                policies_evaluated=1,
                recommended_action=result.recommended_action,
                decision_reason=result.decision_reason,
            )

        policies = await self.policies.list_active_policies()
        return self.evaluation_engine.evaluate_policies(
            policies,
            ctx,
            validation_score=body.validation_score,
        )

    async def _attach_rules_internal(
        self,
        policy_id: UUID,
        rule_ids: list[UUID],
        *,
        sort_order: int,
        actor_user_id: UUID,
        audit_attach: bool,
    ) -> None:
        policy = await self.get_policy(policy_id)
        if policy.status == "archived":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot modify rules on archived policy",
            )

        rules = await self.policies.get_rules_by_ids(rule_ids)
        found_ids = {r.id for r in rules}
        missing = [str(rid) for rid in rule_ids if rid not in found_ids]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rules not found: {', '.join(missing)}",
            )

        attached: list[str] = []
        order = sort_order
        for rule in rules:
            if await self.policies.has_rule_link(policy.id, rule.id):
                continue
            await self.policies.attach_rule(policy.id, rule.id, sort_order=order)
            attached.append(str(rule.id))
            order += 1

        if audit_attach and attached:
            await self.audit.log_policy_updated(
                actor_user_id,
                policy.id,
                metadata={"attached_rule_ids": attached},
            )

    async def _set_status(
        self,
        policy_id: UUID,
        new_status: str,
        *,
        actor_user_id: UUID,
    ) -> CompliancePolicy:
        if new_status not in POLICY_STATUSES:
            raise HTTPException(status_code=400, detail="Invalid policy status")

        policy = await self.get_policy(policy_id)
        old_status = policy.status
        policy.status = new_status
        policy.is_active = new_status == ACTIVE_POLICY_STATUS
        await self.policies.update(policy)

        if new_status == "archived":
            await self.audit.log_policy_archived(
                actor_user_id,
                policy.id,
                metadata={"from_status": old_status, "name": policy.name},
            )
        elif new_status == "active":
            await self.audit.log_policy_activation(
                actor_user_id,
                policy.id,
                is_active=True,
                metadata={"from_status": old_status},
            )
        elif old_status == "active" and new_status in ("inactive", "draft"):
            await self.audit.log_policy_activation(
                actor_user_id,
                policy.id,
                is_active=False,
                metadata={"to_status": new_status},
            )
        else:
            await self.audit.log_policy_updated(
                actor_user_id,
                policy.id,
                metadata={"from_status": old_status, "to_status": new_status},
            )

        return await self.get_policy(policy.id)

    @staticmethod
    def _definition_from_thresholds(thresholds: PolicyThresholdsSchema) -> dict:
        return {"thresholds": thresholds.model_dump()}

    @staticmethod
    def thresholds_from_policy(policy: CompliancePolicy) -> PolicyThresholdsSchema:
        raw = (policy.definition_json or {}).get("thresholds", {})
        return PolicyThresholdsSchema.model_validate(raw)

    @classmethod
    def to_policy_response(cls, policy: CompliancePolicy) -> CompliancePolicyResponse:
        rules = [
            link.rule
            for link in sorted(
                policy.policy_rule_links or [],
                key=lambda link: (link.sort_order, link.rule.name if link.rule else ""),
            )
            if link.rule is not None
        ]
        from app.schemas.rules import ComplianceRuleResponse

        return CompliancePolicyResponse(
            id=policy.id,
            name=policy.name,
            description=policy.description,
            policy_type=policy.policy_type,
            status=policy.status,
            priority=policy.priority,
            thresholds=cls.thresholds_from_policy(policy),
            is_active=policy.is_active,
            severity_default=policy.severity_default,
            created_by_user_id=policy.created_by_user_id,
            created_at=policy.created_at,
            updated_at=policy.updated_at,
            rules=[ComplianceRuleResponse.model_validate(r) for r in rules],
        )

    @staticmethod
    def to_evaluation_response(
        result: PoliciesEvaluationResult,
    ) -> PoliciesEvaluationResponse:
        return PoliciesEvaluationResponse(
            policy_results=[
                PolicyService._policy_eval_to_response(p) for p in result.policy_results
            ],
            policies_evaluated=result.policies_evaluated,
            recommended_action=result.recommended_action,
            decision_reason=result.decision_reason,
        )

    @staticmethod
    def _policy_eval_to_response(result: PolicyEvaluationResult) -> PolicyEvaluationResponse:
        rule_eval = result.rule_evaluation
        return PolicyEvaluationResponse(
            policy_id=result.policy_id,
            policy_name=result.policy_name,
            policy_type=result.policy_type,
            status=result.status,
            priority=result.priority,
            validation_score=result.validation_score,
            threshold_action=result.threshold_action,
            rule_evaluation=RuleEvaluationResponse(
                triggered_rules=[
                    TriggeredRuleResponse(
                        rule_id=t.rule_id,
                        rule_name=t.rule_name,
                        rule_code=t.rule_code,
                        category=t.category,
                        severity=t.severity,
                        action=t.action,
                        priority=t.priority,
                        reason=t.reason,
                    )
                    for t in rule_eval.triggered_rules
                ],
                rules_evaluated=rule_eval.rules_evaluated,
                aggregated_risk_score=rule_eval.aggregated_risk_score,
                aggregated_severity=rule_eval.aggregated_severity,
                recommended_action=rule_eval.recommended_action,
                decision_reason=rule_eval.decision_reason,
            ),
            recommended_action=result.recommended_action,
            decision_reason=result.decision_reason,
            triggered_rules=[
                TriggeredRuleResponse(
                    rule_id=t.rule_id,
                    rule_name=t.rule_name,
                    rule_code=t.rule_code,
                    category=t.category,
                    severity=t.severity,
                    action=t.action,
                    priority=t.priority,
                    reason=t.reason,
                )
                for t in result.triggered_rules
            ],
        )
