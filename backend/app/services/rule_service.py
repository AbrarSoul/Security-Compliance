import uuid
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance_rule import ComplianceRule
from app.repositories.compliance_rule_repository import ComplianceRuleRepository
from app.schemas.rules import (
    ComplianceRuleCreate,
    ComplianceRuleUpdate,
    EvaluateRulesRequest,
    RuleEvaluationResponse,
    TriggeredRuleResponse,
)
from app.services.audit_service import AuditService
from app.services.rules import RuleEngine, RuleEvaluationContext, context_from_detections, context_from_scan
from app.services.rules.types import RuleEvaluationResult
from app.services.scanner.types import DetectionResult


class RuleService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.rules = ComplianceRuleRepository(db)
        self.engine = RuleEngine()
        self.audit = AuditService(db)

    async def list_rules(
        self,
        *,
        category: str | None = None,
        enabled_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ComplianceRule], int]:
        items = await self.rules.list_rules(
            category=category,
            enabled_only=enabled_only,
            limit=limit,
            offset=offset,
        )
        total = await self.rules.count_rules(
            category=category,
            enabled_only=enabled_only,
        )
        return items, total

    async def get_rule(self, rule_id: UUID) -> ComplianceRule:
        rule = await self.rules.get_by_id(rule_id)
        if rule is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
        return rule

    async def create_rule(
        self,
        payload: ComplianceRuleCreate,
        *,
        created_by_user_id: UUID,
    ) -> ComplianceRule:
        existing = await self.rules.get_by_code(payload.code)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Rule code already exists: {payload.code}",
            )

        rule = ComplianceRule(
            id=uuid.uuid4(),
            code=payload.code,
            name=payload.name,
            description=payload.description,
            category=payload.category,
            severity=payload.severity,
            action=payload.action,
            priority=payload.priority,
            condition_json=payload.condition,
            is_enabled=payload.is_enabled,
            created_by_user_id=created_by_user_id,
        )
        await self.rules.create(rule)
        await self.audit.log_rule_created(
            created_by_user_id,
            rule.id,
            metadata={"code": rule.code, "name": rule.name},
        )
        return rule

    async def update_rule(
        self,
        rule_id: UUID,
        payload: ComplianceRuleUpdate,
        *,
        actor_user_id: UUID,
    ) -> ComplianceRule:
        rule = await self.get_rule(rule_id)
        changes: dict[str, object] = {}

        if payload.name is not None:
            rule.name = payload.name
            changes["name"] = payload.name
        if payload.description is not None:
            rule.description = payload.description
            changes["description"] = payload.description
        if payload.category is not None:
            rule.category = payload.category
            changes["category"] = payload.category
        if payload.severity is not None:
            rule.severity = payload.severity
            changes["severity"] = payload.severity
        if payload.action is not None:
            rule.action = payload.action
            changes["action"] = payload.action
        if payload.priority is not None:
            rule.priority = payload.priority
            changes["priority"] = payload.priority
        if payload.condition is not None:
            rule.condition_json = payload.condition
            changes["condition"] = True
        if payload.is_enabled is not None:
            rule.is_enabled = payload.is_enabled
            changes["is_enabled"] = payload.is_enabled

        await self.rules.update(rule)
        await self.audit.log_rule_updated(
            actor_user_id,
            rule.id,
            metadata={"code": rule.code, "changes": changes},
        )
        return rule

    async def set_rule_enabled(
        self,
        rule_id: UUID,
        *,
        enabled: bool,
        actor_user_id: UUID,
    ) -> ComplianceRule:
        rule = await self.get_rule(rule_id)
        rule.is_enabled = enabled
        await self.rules.update(rule)
        if enabled:
            await self.audit.log_rule_updated(
                actor_user_id,
                rule.id,
                metadata={"code": rule.code, "enabled": True},
            )
        else:
            await self.audit.log_rule_disabled(
                actor_user_id,
                rule.id,
                metadata={"code": rule.code},
            )
        return rule

    async def evaluate_request(self, body: EvaluateRulesRequest) -> RuleEvaluationResult:
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
        rules = await self.rules.list_enabled_for_evaluation()
        return self.engine.evaluate(rules, ctx)

    async def evaluate_detections(
        self,
        detections: list[DetectionResult],
        *,
        risk_score: int | None = None,
        compliance_status: str | None = None,
        classification: str | None = None,
        model_is_external: bool = False,
        model_deployment: str | None = None,
        model_provider: str | None = None,
    ) -> RuleEvaluationResult:
        """Evaluate rules from in-memory scan results (avoids async lazy-load on scan.findings)."""
        ctx = context_from_detections(
            detections,
            risk_score=risk_score,
            compliance_status=compliance_status,
            classification=classification,
            model_is_external=model_is_external,
            model_deployment=model_deployment,
            model_provider=model_provider,
        )
        rules = await self.rules.list_enabled_for_evaluation()
        return self.engine.evaluate(rules, ctx)

    async def evaluate_scan(
        self,
        scan,
        *,
        model_is_external: bool = False,
        model_deployment: str | None = None,
        model_provider: str | None = None,
    ) -> RuleEvaluationResult:
        await self.db.refresh(scan, attribute_names=["findings"])
        ctx = context_from_scan(
            scan,
            model_is_external=model_is_external,
            model_deployment=model_deployment,
            model_provider=model_provider,
        )
        rules = await self.rules.list_enabled_for_evaluation()
        return self.engine.evaluate(rules, ctx)

    @staticmethod
    def to_evaluation_response(result: RuleEvaluationResult) -> RuleEvaluationResponse:
        return RuleEvaluationResponse(
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
            rules_evaluated=result.rules_evaluated,
            aggregated_risk_score=result.aggregated_risk_score,
            aggregated_severity=result.aggregated_severity,
            recommended_action=result.recommended_action,
            decision_reason=result.decision_reason,
        )
