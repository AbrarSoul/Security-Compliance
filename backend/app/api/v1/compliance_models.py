"""AI model registry and dataset+model compliance validation APIs."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import AuthContext, require_permission
from app.core.permissions import EXECUTION_REQUEST, POLICY_MANAGE, SCAN_READ
from app.db.session import get_db
from app.schemas.compliance_models import (
    ComplianceModelCreate,
    ComplianceModelListResponse,
    ComplianceModelResponse,
    ComplianceModelUpdate,
    GptLabSyncResponse,
    ModelComplianceValidationResponse,
    ValidateModelRequest,
)
from app.services.gptlab_model_sync_service import GptLabModelSyncService
from app.services.model_compliance_service import ModelComplianceService

router = APIRouter(prefix="/models", tags=["model-compliance"])


def get_model_compliance_service(
    db: AsyncSession = Depends(get_db),
) -> ModelComplianceService:
    return ModelComplianceService(db)


@router.get("", response_model=ComplianceModelListResponse)
async def list_models(
    _ctx: AuthContext = Depends(require_permission(SCAN_READ)),
    active_only: bool = Query(default=True),
    approved_only: bool = Query(default=False),
    model_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: ModelComplianceService = Depends(get_model_compliance_service),
):
    """List registered AI models available for compliance validation."""
    items, total = await service.list_models(
        active_only=active_only,
        approved_only=approved_only,
        model_type=model_type,
        limit=limit,
        offset=offset,
    )
    return ComplianceModelListResponse(
        items=[service.to_model_response(m) for m in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=ComplianceModelResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_model(
    body: ComplianceModelCreate,
    ctx: AuthContext = Depends(require_permission(POLICY_MANAGE)),
    service: ModelComplianceService = Depends(get_model_compliance_service),
):
    """Register model metadata (admin)."""
    model = await service.register_model(body, created_by_user_id=ctx.user.id)
    return service.to_model_response(model)


@router.post("/sync-gptlab", response_model=GptLabSyncResponse)
async def sync_gptlab_models(
    approve_new: bool = Query(default=True),
    deactivate_demos: bool = Query(default=False),
    deactivate_missing: bool = Query(default=True),
    ctx: AuthContext = Depends(require_permission(POLICY_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    """
    Pull chat models from GPT-Lab and upsert them into the compliance registry.

    Requires GPTLAB_API_KEY in server environment. API keys are never stored in the registry.
    """
    sync_service = GptLabModelSyncService(db)
    result = await sync_service.sync(
        actor_user_id=ctx.user.id,
        approve_new=approve_new,
        deactivate_demos=deactivate_demos,
        deactivate_missing=deactivate_missing,
    )
    return GptLabSyncResponse(
        created=result.created,
        updated=result.updated,
        deactivated=result.deactivated,
        demos_deactivated=result.demos_deactivated,
        models_synced=result.models_synced,
        skipped=result.skipped,
    )


@router.post(
    "/validate",
    response_model=ModelComplianceValidationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def validate_dataset_model(
    body: ValidateModelRequest,
    ctx: AuthContext = Depends(require_permission(EXECUTION_REQUEST)),
    service: ModelComplianceService = Depends(get_model_compliance_service),
):
    """
    Validate whether a registered AI model is safe to use with a scanned dataset.

    Integrates built-in risk checks, the rule engine, and active policies.
    """
    validation = await service.validate_dataset_model(body, user_id=ctx.user.id)
    return service.to_validation_response(validation)


@router.get(
    "/validations/{validation_id}",
    response_model=ModelComplianceValidationResponse,
)
async def get_validation(
    validation_id: UUID,
    ctx: AuthContext = Depends(require_permission(SCAN_READ)),
    service: ModelComplianceService = Depends(get_model_compliance_service),
):
    validation = await service.get_validation(validation_id, user_id=ctx.user.id)
    return service.to_validation_response(validation)


@router.get("/{model_id}", response_model=ComplianceModelResponse)
async def get_model(
    model_id: UUID,
    _ctx: AuthContext = Depends(require_permission(SCAN_READ)),
    service: ModelComplianceService = Depends(get_model_compliance_service),
):
    model = await service.get_model(model_id)
    return service.to_model_response(model)


@router.patch("/{model_id}", response_model=ComplianceModelResponse)
async def update_model(
    model_id: UUID,
    body: ComplianceModelUpdate,
    ctx: AuthContext = Depends(require_permission(POLICY_MANAGE)),
    service: ModelComplianceService = Depends(get_model_compliance_service),
):
    """Update model metadata (admin)."""
    model = await service.update_model(model_id, body, actor_user_id=ctx.user.id)
    return service.to_model_response(model)
