"""Unified compliance posture API."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import AuthContext, require_any_permission
from app.core.permissions import GAIRA_READ, GAIRA_READ_ALL, GAP_READ, GAP_READ_ALL
from app.db.session import get_db
from app.schemas.compliance_posture import CompliancePostureResponse
from app.services.compliance.posture_service import CompliancePostureService

router = APIRouter(prefix="/compliance", tags=["compliance-posture"])


def get_posture_service(db: AsyncSession = Depends(get_db)) -> CompliancePostureService:
    return CompliancePostureService(db)


@router.get("/posture", response_model=CompliancePostureResponse)
async def get_compliance_posture(
    auth: AuthContext = Depends(require_any_permission(GAP_READ, GAP_READ_ALL, GAIRA_READ, GAIRA_READ_ALL)),
    service: CompliancePostureService = Depends(get_posture_service),
):
    """Per-framework compliance posture with open issues and remediations."""
    data = await service.get_posture()
    return CompliancePostureResponse.model_validate(data)
