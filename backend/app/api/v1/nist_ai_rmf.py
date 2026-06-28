"""NIST AI RMF profile and control catalog APIs."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import AuthContext, require_any_permission
from app.core.permissions import GAIRA_READ, GAIRA_READ_ALL, GAP_READ, GAP_READ_ALL
from app.db.session import get_db
from app.schemas.nist_ai_rmf import NistControlsCatalogResponse, NistCurrentProfileResponse
from app.services.nist_ai_rmf.profile_service import NistAiRmfProfileService

router = APIRouter(prefix="/nist-ai-rmf", tags=["nist-ai-rmf"])


def get_nist_service(db: AsyncSession = Depends(get_db)) -> NistAiRmfProfileService:
    return NistAiRmfProfileService(db)


@router.get("/controls", response_model=NistControlsCatalogResponse)
async def get_controls_catalog(
    auth: AuthContext = Depends(require_any_permission(GAP_READ, GAP_READ_ALL, GAIRA_READ, GAIRA_READ_ALL)),
    service: NistAiRmfProfileService = Depends(get_nist_service),
):
    """Return the NIST AI RMF control catalog with ComplianceGuard mapping metadata."""
    data = await service.get_controls_catalog()
    return NistControlsCatalogResponse.model_validate(data)


@router.get("/profile/current", response_model=NistCurrentProfileResponse)
async def get_current_profile(
    auth: AuthContext = Depends(require_any_permission(GAP_READ, GAP_READ_ALL, GAIRA_READ, GAIRA_READ_ALL)),
    service: NistAiRmfProfileService = Depends(get_nist_service),
):
    """Evaluate the ComplianceGuard operational profile against live platform evidence."""
    data = await service.get_current_profile()
    return NistCurrentProfileResponse.model_validate(data)
