"""Compliance rule engine APIs (database-configurable rules)."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import AuthContext, require_permission
from app.core.permissions import RULE_MANAGE, SCAN_READ
from app.db.session import get_db
from app.schemas.rules import (
    ComplianceRuleCreate,
    ComplianceRuleListResponse,
    ComplianceRuleResponse,
    ComplianceRuleUpdate,
    EvaluateRulesRequest,
    RuleEvaluationResponse,
)
from app.services.rule_service import RuleService

router = APIRouter(prefix="/rules", tags=["compliance-rules"])


def get_rule_service(db: AsyncSession = Depends(get_db)) -> RuleService:
    return RuleService(db)


@router.get("", response_model=ComplianceRuleListResponse)
async def list_rules(
    _ctx: AuthContext = Depends(require_permission(SCAN_READ)),
    category: str | None = Query(default=None),
    enabled_only: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    service: RuleService = Depends(get_rule_service),
):
    """List compliance rules (configurable in database)."""
    items, total = await service.list_rules(
        category=category,
        enabled_only=enabled_only,
        limit=limit,
        offset=offset,
    )
    return ComplianceRuleListResponse(
        items=[ComplianceRuleResponse.model_validate(r) for r in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/evaluate",
    response_model=RuleEvaluationResponse,
    summary="Evaluate enabled rules against a context",
)
async def evaluate_rules(
    body: EvaluateRulesRequest,
    _ctx: AuthContext = Depends(require_permission(SCAN_READ)),
    service: RuleService = Depends(get_rule_service),
):
    """Evaluate all enabled rules (priority-ordered) against supplied facts."""
    result = await service.evaluate_request(body)
    return service.to_evaluation_response(result)


@router.get("/{rule_id}", response_model=ComplianceRuleResponse)
async def get_rule(
    rule_id: UUID,
    _ctx: AuthContext = Depends(require_permission(SCAN_READ)),
    service: RuleService = Depends(get_rule_service),
):
    rule = await service.get_rule(rule_id)
    return ComplianceRuleResponse.model_validate(rule)


@router.post(
    "",
    response_model=ComplianceRuleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_rule(
    body: ComplianceRuleCreate,
    ctx: AuthContext = Depends(require_permission(RULE_MANAGE)),
    service: RuleService = Depends(get_rule_service),
):
    """Create a compliance rule (admin)."""
    rule = await service.create_rule(body, created_by_user_id=ctx.user.id)
    return ComplianceRuleResponse.model_validate(rule)


@router.patch("/{rule_id}", response_model=ComplianceRuleResponse)
async def update_rule(
    rule_id: UUID,
    body: ComplianceRuleUpdate,
    ctx: AuthContext = Depends(require_permission(RULE_MANAGE)),
    service: RuleService = Depends(get_rule_service),
):
    """Update a compliance rule (admin)."""
    rule = await service.update_rule(rule_id, body, actor_user_id=ctx.user.id)
    return ComplianceRuleResponse.model_validate(rule)


@router.post("/{rule_id}/enable", response_model=ComplianceRuleResponse)
async def enable_rule(
    rule_id: UUID,
    ctx: AuthContext = Depends(require_permission(RULE_MANAGE)),
    service: RuleService = Depends(get_rule_service),
):
    """Enable a compliance rule (admin)."""
    rule = await service.set_rule_enabled(
        rule_id, enabled=True, actor_user_id=ctx.user.id
    )
    return ComplianceRuleResponse.model_validate(rule)


@router.post("/{rule_id}/disable", response_model=ComplianceRuleResponse)
async def disable_rule(
    rule_id: UUID,
    ctx: AuthContext = Depends(require_permission(RULE_MANAGE)),
    service: RuleService = Depends(get_rule_service),
):
    """Disable a compliance rule (admin)."""
    rule = await service.set_rule_enabled(
        rule_id, enabled=False, actor_user_id=ctx.user.id
    )
    return ComplianceRuleResponse.model_validate(rule)
