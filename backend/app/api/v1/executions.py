"""Pre-execution compliance validation APIs."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import AuthContext, require_any_permission, require_permission
from app.core.permissions import (
    EXECUTION_READ,
    EXECUTION_READ_ALL,
    EXECUTION_REQUEST,
)
from app.db.session import get_db
from app.schemas.executions import (
    AcknowledgeWarningRequest,
    AcknowledgeWarningResponse,
    ExecutionRequestDetailResponse,
    ExecutionRequestListResponse,
    ExecutionStatusResponse,
    StartExecutionResponse,
    ValidateExecutionRequest,
    ValidateExecutionResponse,
)
from app.services.execution_blocking_service import ExecutionBlockingService
from app.services.execution_validation_service import ExecutionValidationService

router = APIRouter(prefix="/executions", tags=["pre-execution-validation"])


def get_execution_service(
    db: AsyncSession = Depends(get_db),
) -> ExecutionValidationService:
    return ExecutionValidationService(db)


def get_blocking_service(
    db: AsyncSession = Depends(get_db),
) -> ExecutionBlockingService:
    return ExecutionBlockingService(db)


@router.post(
    "/validate",
    response_model=ValidateExecutionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def validate_execution(
    body: ValidateExecutionRequest,
    ctx: AuthContext = Depends(require_permission(EXECUTION_REQUEST)),
    service: ExecutionValidationService = Depends(get_execution_service),
):
    """Pre-execution validation: dataset → scan → model → rules → policies → decision."""
    can_validate_any = ctx.has_permission(EXECUTION_READ_ALL)
    return await service.validate_execution(
        body, user_id=ctx.user.id, can_validate_any=can_validate_any
    )


@router.get("", response_model=ExecutionRequestListResponse)
async def list_executions(
    ctx: AuthContext = Depends(
        require_any_permission(EXECUTION_REQUEST, EXECUTION_READ, EXECUTION_READ_ALL)
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: ExecutionValidationService = Depends(get_execution_service),
):
    """
    List execution validation history.

    Users see their own requests; admins and auditors see all (read-only for auditors).
    """
    can_read_all = ctx.has_permission(EXECUTION_READ_ALL) or ctx.has_permission(
        EXECUTION_READ
    )

    items, total = await service.list_executions(
        user_id=ctx.user.id,
        can_read_all=can_read_all,
        limit=limit,
        offset=offset,
    )
    return service.to_list_response(items, total=total, limit=limit, offset=offset)


@router.get("/{execution_id}/status", response_model=ExecutionStatusResponse)
async def get_execution_status(
    execution_id: UUID,
    ctx: AuthContext = Depends(
        require_any_permission(EXECUTION_REQUEST, EXECUTION_READ, EXECUTION_READ_ALL)
    ),
    service: ExecutionBlockingService = Depends(get_blocking_service),
):
    """Get enforcement status: whether execution can start, warnings, blocks."""
    can_read_all = ExecutionBlockingService.can_read_all(ctx.permissions)
    return await service.get_status(
        execution_id,
        user_id=ctx.user.id,
        can_read_all=can_read_all,
    )


@router.post("/{execution_id}/start", response_model=StartExecutionResponse)
async def start_execution(
    execution_id: UUID,
    ctx: AuthContext = Depends(require_permission(EXECUTION_REQUEST)),
    service: ExecutionBlockingService = Depends(get_blocking_service),
):
    """
    Start execution after validation (enforcement only — no experiment runner).

    Requires allow or acknowledged warn. Blocked executions cannot start.
    """
    is_auditor = ExecutionBlockingService.is_auditor_readonly(ctx.permissions)
    can_start_any = ExecutionBlockingService.can_start_any(ctx.permissions)
    return await service.start_execution(
        execution_id,
        user_id=ctx.user.id,
        can_start_any=can_start_any,
        is_auditor_readonly=is_auditor,
    )


@router.post(
    "/{execution_id}/acknowledge-warning",
    response_model=AcknowledgeWarningResponse,
)
async def acknowledge_warning(
    execution_id: UUID,
    body: AcknowledgeWarningRequest,
    ctx: AuthContext = Depends(require_permission(EXECUTION_REQUEST)),
    service: ExecutionBlockingService = Depends(get_blocking_service),
):
    """Acknowledge compliance warnings before starting execution."""
    is_auditor = ExecutionBlockingService.is_auditor_readonly(ctx.permissions)
    can_ack_any = ExecutionBlockingService.can_start_any(ctx.permissions)
    return await service.acknowledge_warning(
        execution_id,
        body,
        user_id=ctx.user.id,
        can_ack_any=can_ack_any,
        is_auditor_readonly=is_auditor,
    )


@router.get("/{execution_id}", response_model=ExecutionRequestDetailResponse)
async def get_execution(
    execution_id: UUID,
    ctx: AuthContext = Depends(
        require_any_permission(EXECUTION_REQUEST, EXECUTION_READ, EXECUTION_READ_ALL)
    ),
    service: ExecutionValidationService = Depends(get_execution_service),
):
    can_read_all = ctx.has_permission(EXECUTION_READ_ALL) or ctx.has_permission(
        EXECUTION_READ
    )

    record = await service.get_execution(
        execution_id,
        user_id=ctx.user.id,
        can_read_all=can_read_all,
    )
    return service.to_detail(record)
