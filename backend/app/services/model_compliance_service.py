import uuid
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import audit_severity
from app.models.compliance_model import ComplianceModel
from app.models.model_validation import ModelValidation
from app.repositories.compliance_model_repository import ComplianceModelRepository
from app.repositories.compliance_policy_repository import CompliancePolicyRepository
from app.repositories.compliance_rule_repository import ComplianceRuleRepository
from app.repositories.model_validation_repository import ModelValidationRepository
from app.repositories.scan_repository import ScanRepository
from app.schemas.compliance_models import (
    ComplianceModelCreate,
    ComplianceModelResponse,
    ComplianceModelUpdate,
    ModelComplianceValidationResponse,
    ModelRiskCheckResponse,
    ValidateModelRequest,
)
from app.schemas.policies import PoliciesEvaluationResponse
from app.schemas.rules import RuleEvaluationResponse
from app.services.audit_service import AuditService
from app.services.compliance import ComplianceEvaluationOrchestrator


class ModelComplianceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.models = ComplianceModelRepository(db)
        self.validations = ModelValidationRepository(db)
        self.scans = ScanRepository(db)
        self.policies = CompliancePolicyRepository(db)
        self.rules = ComplianceRuleRepository(db)
        self.evaluator = ComplianceEvaluationOrchestrator()
        self.audit = AuditService(db)

    async def register_model(
        self,
        payload: ComplianceModelCreate,
        *,
        created_by_user_id: UUID,
    ) -> ComplianceModel:
        existing = await self.models.get_by_code(payload.code)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Model code already exists: {payload.code}",
            )

        model = ComplianceModel(
            id=uuid.uuid4(),
            code=payload.code,
            name=payload.name,
            provider=payload.provider,
            model_type=payload.model_type,
            endpoint_url=payload.endpoint_url,
            data_retention_policy=payload.data_retention_policy,
            logging_enabled=payload.logging_enabled,
            data_leaves_platform=payload.data_leaves_platform,
            is_approved=payload.is_approved,
            is_active=payload.is_active,
            metadata_json=payload.metadata or None,
            created_by_user_id=created_by_user_id,
        )
        await self.models.create(model)
        await self.audit.log_model_registered(
            created_by_user_id,
            model.id,
            metadata={"code": model.code, "name": model.name, "model_type": model.model_type},
        )
        return model

    async def update_model(
        self,
        model_id: UUID,
        payload: ComplianceModelUpdate,
        *,
        actor_user_id: UUID,
    ) -> ComplianceModel:
        model = await self._get_model(model_id)
        changes: dict[str, object] = {}

        for field_name, attr in (
            ("name", "name"),
            ("provider", "provider"),
            ("model_type", "model_type"),
            ("endpoint_url", "endpoint_url"),
            ("data_retention_policy", "data_retention_policy"),
            ("logging_enabled", "logging_enabled"),
            ("data_leaves_platform", "data_leaves_platform"),
            ("is_approved", "is_approved"),
            ("is_active", "is_active"),
        ):
            value = getattr(payload, field_name)
            if value is not None:
                setattr(model, attr, value)
                changes[field_name] = value

        if payload.metadata is not None:
            model.metadata_json = payload.metadata
            changes["metadata"] = True

        await self.models.update(model)
        await self.audit.log_model_updated(
            actor_user_id, model.id, metadata={"code": model.code, "changes": changes}
        )
        return model

    async def list_models(
        self,
        *,
        active_only: bool = True,
        approved_only: bool = False,
        model_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ComplianceModel], int]:
        items = await self.models.list_models(
            active_only=active_only,
            approved_only=approved_only,
            model_type=model_type,
            limit=limit,
            offset=offset,
        )
        total = await self.models.count_models(
            active_only=active_only,
            approved_only=approved_only,
            model_type=model_type,
        )
        return items, total

    async def get_model(self, model_id: UUID) -> ComplianceModel:
        return await self._get_model(model_id)

    async def validate_dataset_model(
        self,
        payload: ValidateModelRequest,
        *,
        user_id: UUID,
    ) -> ModelValidation:
        scan = await self.scans.get_by_id_for_user(payload.scan_id, user_id)
        if scan is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
        if scan.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scan must be completed before model validation",
            )

        model = await self._resolve_model(payload)
        if not model.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Model is not active",
            )

        active_policies = await self.policies.list_active_policies()
        enabled_rules = await self.rules.list_enabled_for_evaluation()
        bundle = self.evaluator.evaluate(
            scan,
            model,
            active_policies=active_policies,
            enabled_rules=enabled_rules,
        )
        check_result = bundle.model_result

        validation = ModelValidation(
            id=uuid.uuid4(),
            user_id=user_id,
            scan_id=scan.id,
            compliance_model_id=model.id,
            status="completed",
            decision=check_result.decision,
            risk_level=check_result.risk_level,
            risk_score=check_result.risk_score,
            primary_reason=check_result.primary_reason,
            flags_json={"risk_checks": [c.to_dict() for c in check_result.risk_checks]},
            details_json=check_result.to_dict(),
            recommendations_json=check_result.recommendations,
            validated_at=datetime.now(UTC),
        )
        await self.validations.create(validation)
        await self._audit_validation(user_id, validation, model)
        reloaded = await self.validations.get_by_id(validation.id)
        return reloaded if reloaded is not None else validation

    async def get_validation(
        self, validation_id: UUID, *, user_id: UUID
    ) -> ModelValidation:
        validation = await self.validations.get_by_id(validation_id)
        if validation is None or validation.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Validation not found"
            )
        return validation

    async def _resolve_model(self, payload: ValidateModelRequest) -> ComplianceModel:
        if payload.model_id is not None:
            return await self._get_model(payload.model_id)
        assert payload.model_code is not None
        model = await self.models.get_by_code(payload.model_code)
        if model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model not found: {payload.model_code}",
            )
        return model

    async def _get_model(self, model_id: UUID) -> ComplianceModel:
        model = await self.models.get_by_id(model_id)
        if model is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Model not found"
            )
        return model

    async def _audit_validation(
        self, user_id: UUID, validation: ModelValidation, model: ComplianceModel
    ) -> None:
        metadata = {
            "scan_id": str(validation.scan_id),
            "model_id": str(model.id),
            "model_code": model.code,
            "decision": validation.decision,
            "risk_level": validation.risk_level,
        }
        if validation.decision == "block":
            await self.audit.log_model_validation_blocked(
                user_id, validation.id, metadata=metadata
            )
        else:
            await self.audit.log_model_validated(user_id, validation.id, metadata=metadata)

    @staticmethod
    def to_model_response(model: ComplianceModel) -> ComplianceModelResponse:
        return ComplianceModelResponse.model_validate(model)

    @classmethod
    def to_validation_response(
        cls, validation: ModelValidation
    ) -> ModelComplianceValidationResponse:
        model = validation.compliance_model
        details = validation.details_json or {}
        scan = validation.scan

        rule_eval = None
        if details.get("rule_evaluation"):
            rule_eval = RuleEvaluationResponse.model_validate(details["rule_evaluation"])

        policy_eval = None
        if details.get("policy_evaluation"):
            policy_eval = PoliciesEvaluationResponse.model_validate(
                details["policy_evaluation"]
            )

        detected = []
        if scan and scan.findings:
            detected = sorted({f.finding_type for f in scan.findings})

        return ModelComplianceValidationResponse(
            id=validation.id,
            scan_id=validation.scan_id,
            model_id=model.id if model else validation.compliance_model_id,
            model_name=model.name if model else "Unknown",
            model_type=model.model_type if model else "unknown",
            provider=model.provider if model else None,
            decision=validation.decision or "allow",
            risk_level=validation.risk_level or "low",
            risk_score=validation.risk_score or 0,
            primary_reason=validation.primary_reason or "",
            recommendations=validation.recommendations_json or [],
            risk_checks=[
                ModelRiskCheckResponse.model_validate(c)
                for c in (validation.flags_json or {}).get("risk_checks", [])
            ],
            rule_evaluation=rule_eval,
            policy_evaluation=policy_eval,
            dataset_classification=scan.classification if scan else None,
            detected_types=detected,
            validated_at=validation.validated_at,
            created_at=validation.created_at,
        )
