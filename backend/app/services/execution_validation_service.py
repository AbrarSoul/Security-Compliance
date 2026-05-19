import uuid
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.execution_request import ExecutionRequest
from app.models.execution_result import ExecutionResult
from app.models.model_validation import ModelValidation
from app.repositories.compliance_model_repository import ComplianceModelRepository
from app.repositories.compliance_policy_repository import CompliancePolicyRepository
from app.repositories.compliance_rule_repository import ComplianceRuleRepository
from app.repositories.execution_repository import ExecutionRepository
from app.repositories.file_repository import FileRepository
from app.repositories.scan_repository import ScanRepository
from app.schemas.executions import (
    ExecutionRequestDetailResponse,
    ExecutionRequestListResponse,
    ExecutionRequestSummary,
    ExecutionResultSummary,
    ModelRiskSummary,
    PolicyViolationSummary,
    TriggeredRuleSummary,
    ValidateExecutionRequest,
    ValidateExecutionResponse,
)
from app.services.audit_service import AuditService
from app.services.execution import PreExecutionValidator
from app.services.execution.blocking_engine import ExecutionBlockingEngine
from app.services.execution.constants import STATUS_VALIDATING
from app.services.execution.enforcement_helpers import reasons_from_outcome
from app.services.compliance import ComplianceEvaluationOrchestrator
from app.services.recommendations import RecommendationEngine
from app.services.recommendations.engine import FindingContext
from app.services.scoring.types import ComplianceScoreResult


class ExecutionValidationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.executions = ExecutionRepository(db)
        self.files = FileRepository(db)
        self.scans = ScanRepository(db)
        self.models = ComplianceModelRepository(db)
        self.policies = CompliancePolicyRepository(db)
        self.rules = ComplianceRuleRepository(db)
        self.evaluator = ComplianceEvaluationOrchestrator()
        self.recommendation_engine = RecommendationEngine()
        self.validator = PreExecutionValidator()
        self.blocking_engine = ExecutionBlockingEngine()
        self.audit = AuditService(db)

    async def validate_execution(
        self,
        payload: ValidateExecutionRequest,
        *,
        user_id: UUID,
        can_validate_any: bool = False,
    ) -> ValidateExecutionResponse:
        file_record, scan, model = await self._load_and_verify_inputs(
            payload, user_id, can_validate_any=can_validate_any
        )

        request = ExecutionRequest(
            id=uuid.uuid4(),
            user_id=user_id,
            file_id=file_record.id,
            scan_id=scan.id,
            compliance_model_id=model.id,
            execution_purpose=payload.execution_purpose,
            model_provider=model.provider,
            model_name=model.name,
            model_endpoint_url=model.endpoint_url,
            is_external_api=model.model_type in ("external_api", "cloud_hosted")
            or model.data_leaves_platform,
            status=STATUS_VALIDATING,
            notes=None,
        )
        await self.executions.create_request(request)

        await self.audit.log_execution_decision(
            user_id,
            request.id,
            "requested",
            metadata={
                "dataset_id": str(file_record.id),
                "scan_id": str(scan.id),
                "model_id": str(model.id),
                "execution_purpose": payload.execution_purpose,
            },
        )

        active_policies = await self.policies.list_active_policies()
        enabled_rules = await self.rules.list_enabled_for_evaluation()
        bundle = self.evaluator.evaluate(
            scan,
            model,
            active_policies=active_policies,
            enabled_rules=enabled_rules,
        )
        rule_result = bundle.rule_result
        policy_result = bundle.policy_result
        model_result = bundle.model_result

        recs = self._scan_recommendations(scan)
        outcome = self.validator.aggregate(
            scan_risk_score=scan.risk_score,
            scan_classification=scan.classification,
            rule_result=rule_result,
            policy_result=policy_result,
            model_result=model_result,
            recommendations=recs,
        )

        blocking_reasons, warning_reasons, recommendations = reasons_from_outcome(outcome)

        result = ExecutionResult(
            id=uuid.uuid4(),
            execution_request_id=request.id,
            decision=outcome.decision,
            risk_score=outcome.risk_score,
            risk_level=outcome.risk_level,
            reason_codes_json=outcome.reason_codes,
            evaluation_summary_json=outcome.to_summary_dict(),
            blocking_reasons_json=blocking_reasons or None,
            warning_reasons_json=warning_reasons or None,
            recommendations_json=recommendations or None,
            status="completed",
        )
        await self.executions.create_result(result)

        model_validation = ModelValidation(
            id=uuid.uuid4(),
            execution_request_id=request.id,
            user_id=user_id,
            scan_id=scan.id,
            compliance_model_id=model.id,
            status="completed",
            decision=model_result.decision,
            risk_level=model_result.risk_level,
            risk_score=model_result.risk_score,
            primary_reason=model_result.primary_reason,
            flags_json={"risk_checks": [c.to_dict() for c in model_result.risk_checks]},
            details_json=model_result.to_dict(),
            recommendations_json=model_result.recommendations,
            validated_at=datetime.now(UTC),
        )
        self.db.add(model_validation)
        await self.db.flush()

        request.status = self.blocking_engine.status_after_validation(outcome.decision)
        await self.executions.update_request(request)

        if outcome.decision == "block":
            await self.audit.log_execution_blocked(
                user_id,
                request.id,
                metadata={
                    "blocking_reasons": blocking_reasons,
                    "recommendations": recommendations,
                },
            )

        await self.audit.log_execution_decision(
            user_id,
            request.id,
            outcome.decision,
            metadata={
                "decision": outcome.decision,
                "risk_level": outcome.risk_level,
                "risk_score": outcome.risk_score,
                "scan_id": str(scan.id),
                "model_id": str(model.id),
            },
        )

        return ValidateExecutionResponse(
            execution_request_id=request.id,
            decision=outcome.decision,
            risk_score=outcome.risk_score,
            risk_level=outcome.risk_level,
            triggered_rules=[
                TriggeredRuleSummary(
                    rule_id=t["rule_id"],
                    rule_name=t["rule_name"],
                    severity=t["severity"],
                    action=t["action"],
                    reason=t["reason"],
                    rule_code=t.get("rule_code"),
                )
                for t in outcome.triggered_rules
            ],
            policy_violations=[
                PolicyViolationSummary(**v.to_dict()) for v in outcome.policy_violations
            ],
            model_risks=[ModelRiskSummary(**r) for r in outcome.model_risks],
            recommendations=outcome.recommendations,
            explanation=outcome.explanation,
            scan_id=scan.id,
            dataset_id=file_record.id,
            model_id=model.id,
            model_name=model.name,
            execution_purpose=payload.execution_purpose,
            validated_at=result.created_at,
        )

    async def get_execution(
        self,
        execution_id: UUID,
        *,
        user_id: UUID,
        can_read_all: bool,
    ) -> ExecutionRequest:
        if can_read_all:
            record = await self.executions.get_request_by_id(execution_id)
        else:
            record = await self.executions.get_request_for_user(execution_id, user_id)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Execution request not found",
            )
        return record

    async def list_executions(
        self,
        *,
        user_id: UUID,
        can_read_all: bool,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ExecutionRequest], int]:
        if can_read_all:
            items = await self.executions.list_all(limit=limit, offset=offset)
            total = await self.executions.count_all()
        else:
            items = await self.executions.list_by_user(
                user_id, limit=limit, offset=offset
            )
            total = await self.executions.count_by_user(user_id)
        return items, total

    async def _load_and_verify_inputs(
        self,
        payload: ValidateExecutionRequest,
        user_id: UUID,
        *,
        can_validate_any: bool = False,
    ):
        if can_validate_any:
            file_record = await self.files.get_by_id(payload.dataset_id)
        else:
            file_record = await self.files.get_by_id_for_user(
                payload.dataset_id, user_id
            )
        if file_record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
            )

        if can_validate_any:
            scan = await self.scans.get_by_id(payload.scan_id)
        else:
            scan = await self.scans.get_by_id_for_user(payload.scan_id, user_id)
        if scan is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scan result not found for this user",
            )
        if scan.file_id != file_record.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scan does not belong to the specified dataset",
            )
        if scan.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scan must be completed before pre-execution validation",
            )

        model = await self.models.get_by_id(payload.model_id)
        if model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Model not found"
            )
        if not model.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Model is not active",
            )

        return file_record, scan, model

    def _scan_recommendations(self, scan) -> list[str]:
        if not scan.findings:
            return []
        contexts = [
            FindingContext(
                finding_type=f.finding_type,
                severity=f.severity,
                column_name=f.column_name,
                sample_count=f.sample_count,
                match_rate=f.match_rate or 0.0,
            )
            for f in scan.findings
        ]
        score = ComplianceScoreResult(
            risk_score=scan.risk_score or 0,
            compliance_status=scan.compliance_status or "compliant",  # type: ignore[arg-type]
            classification=scan.classification or "public",  # type: ignore[arg-type]
            highest_severity=None,
            total_findings=len(scan.findings),
        )
        return [r.title for r in self.recommendation_engine.generate(contexts, score)]

    @staticmethod
    def to_summary(request: ExecutionRequest) -> ExecutionRequestSummary:
        result = request.execution_result
        return ExecutionRequestSummary(
            id=request.id,
            user_id=request.user_id,
            file_id=request.file_id,
            scan_id=request.scan_id,
            compliance_model_id=request.compliance_model_id,
            execution_purpose=request.execution_purpose,
            model_name=request.model_name,
            model_provider=request.model_provider,
            status=request.status,
            created_at=request.created_at,
            execution_result=(
                ExecutionResultSummary(
                    id=result.id,
                    decision=result.decision,
                    risk_score=result.risk_score,
                    risk_level=result.risk_level,
                    reason_codes=result.reason_codes_json or [],
                    status=result.status,
                    created_at=result.created_at,
                )
                if result
                else None
            ),
        )

    @classmethod
    def to_detail(cls, request: ExecutionRequest) -> ExecutionRequestDetailResponse:
        summary = cls.to_summary(request)
        eval_summary = None
        recommendations: list[str] = []
        if request.execution_result and request.execution_result.evaluation_summary_json:
            eval_summary = request.execution_result.evaluation_summary_json
            recommendations = eval_summary.get("recommendations", [])
        return ExecutionRequestDetailResponse(
            **summary.model_dump(),
            evaluation_summary=eval_summary,
            recommendations=recommendations,
        )

    @staticmethod
    def to_list_response(
        items: list[ExecutionRequest], *, total: int, limit: int, offset: int
    ) -> ExecutionRequestListResponse:
        return ExecutionRequestListResponse(
            items=[ExecutionValidationService.to_summary(r) for r in items],
            total=total,
            limit=limit,
            offset=offset,
        )
