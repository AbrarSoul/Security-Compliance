"""Compliance policy management APIs."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import AuthContext, require_permission
from app.core.permissions import POLICY_MANAGE, SCAN_READ
from app.db.session import get_db
from app.schemas.policies import (
    AttachPolicyRulesRequest,
    CompliancePolicyCreate,
    CompliancePolicyListResponse,
    CompliancePolicyResponse,
    CompliancePolicyUpdate,
    DetachPolicyRulesRequest,
    EvaluatePoliciesRequest,
    PoliciesEvaluationResponse,
)
from app.services.policy_service import PolicyService

router = APIRouter(prefix="/policies", tags=["compliance-policies"])


def get_policy_service(db: AsyncSession = Depends(get_db)) -> PolicyService:
    return PolicyService(db)


@router.get("/active", response_model=CompliancePolicyListResponse)
async def list_active_policies(
    _ctx: AuthContext = Depends(require_permission(SCAN_READ)),
    service: PolicyService = Depends(get_policy_service),
):
    """List all active compliance policies with their linked rules."""
    items = await service.list_active_policies()
    return CompliancePolicyListResponse(
        items=[service.to_policy_response(p) for p in items],
        total=len(items),
        limit=len(items),
        offset=0,
    )


@router.post("/evaluate", response_model=PoliciesEvaluationResponse)
async def evaluate_policies(
    body: EvaluatePoliciesRequest,
    _ctx: AuthContext = Depends(require_permission(SCAN_READ)),
    service: PolicyService = Depends(get_policy_service),
):
    """Evaluate active policies (rule engine + thresholds) against a context."""
    result = await service.evaluate(body)
    return service.to_evaluation_response(result)


@router.get("", response_model=CompliancePolicyListResponse)
async def list_policies(
    _ctx: AuthContext = Depends(require_permission(SCAN_READ)),
    status_filter: str | None = Query(default=None, alias="status"),
    policy_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: PolicyService = Depends(get_policy_service),
):
    """List compliance policies (all statuses)."""
    items, total = await service.list_policies(
        status=status_filter,
        policy_type=policy_type,
        limit=limit,
        offset=offset,
    )
    return CompliancePolicyListResponse(
        items=[service.to_policy_response(p) for p in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{policy_id}", response_model=CompliancePolicyResponse)
async def get_policy(
    policy_id: UUID,
    _ctx: AuthContext = Depends(require_permission(SCAN_READ)),
    service: PolicyService = Depends(get_policy_service),
):
    policy = await service.get_policy(policy_id)
    return service.to_policy_response(policy)


@router.post(
    "",
    response_model=CompliancePolicyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_policy(
    body: CompliancePolicyCreate,
    ctx: AuthContext = Depends(require_permission(POLICY_MANAGE)),
    service: PolicyService = Depends(get_policy_service),
):
    """Create a compliance policy (admin)."""
    policy = await service.create_policy(body, created_by_user_id=ctx.user.id)
    return service.to_policy_response(policy)


@router.patch("/{policy_id}", response_model=CompliancePolicyResponse)
async def update_policy(
    policy_id: UUID,
    body: CompliancePolicyUpdate,
    ctx: AuthContext = Depends(require_permission(POLICY_MANAGE)),
    service: PolicyService = Depends(get_policy_service),
):
    """Update a compliance policy (admin)."""
    policy = await service.update_policy(policy_id, body, actor_user_id=ctx.user.id)
    return service.to_policy_response(policy)


@router.post("/{policy_id}/activate", response_model=CompliancePolicyResponse)
async def activate_policy(
    policy_id: UUID,
    ctx: AuthContext = Depends(require_permission(POLICY_MANAGE)),
    service: PolicyService = Depends(get_policy_service),
):
    """Activate a policy (admin)."""
    policy = await service.activate_policy(policy_id, actor_user_id=ctx.user.id)
    return service.to_policy_response(policy)


@router.post("/{policy_id}/deactivate", response_model=CompliancePolicyResponse)
async def deactivate_policy(
    policy_id: UUID,
    ctx: AuthContext = Depends(require_permission(POLICY_MANAGE)),
    service: PolicyService = Depends(get_policy_service),
):
    """Deactivate a policy (admin)."""
    policy = await service.deactivate_policy(policy_id, actor_user_id=ctx.user.id)
    return service.to_policy_response(policy)


@router.post("/{policy_id}/archive", response_model=CompliancePolicyResponse)
async def archive_policy(
    policy_id: UUID,
    ctx: AuthContext = Depends(require_permission(POLICY_MANAGE)),
    service: PolicyService = Depends(get_policy_service),
):
    """Archive a policy (admin)."""
    policy = await service.archive_policy(policy_id, actor_user_id=ctx.user.id)
    return service.to_policy_response(policy)


@router.post("/{policy_id}/rules", response_model=CompliancePolicyResponse)
async def attach_rules_to_policy(
    policy_id: UUID,
    body: AttachPolicyRulesRequest,
    ctx: AuthContext = Depends(require_permission(POLICY_MANAGE)),
    service: PolicyService = Depends(get_policy_service),
):
    """Attach compliance rules to a policy (admin)."""
    policy = await service.attach_rules(policy_id, body, actor_user_id=ctx.user.id)
    return service.to_policy_response(policy)


@router.delete("/{policy_id}/rules", response_model=CompliancePolicyResponse)
async def detach_rules_from_policy(
    policy_id: UUID,
    body: DetachPolicyRulesRequest,
    ctx: AuthContext = Depends(require_permission(POLICY_MANAGE)),
    service: PolicyService = Depends(get_policy_service),
):
    """Remove compliance rules from a policy (admin)."""
    policy = await service.detach_rules(policy_id, body, actor_user_id=ctx.user.id)
    return service.to_policy_response(policy)
