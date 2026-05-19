from fastapi import APIRouter, Depends

from app.auth.rbac import AuthContext, require_permission
from app.core.permissions import SCAN_READ
from app.schemas.scoring import (
    ClassificationThresholdsResponse,
    ComplianceThresholdsResponse,
    ScoringConfigResponse,
    ScoringRulesResponse,
)
from app.services.scoring.config import get_scoring_config

router = APIRouter(prefix="/scoring", tags=["compliance-scoring"])


@router.get("/config", response_model=ScoringConfigResponse)
async def get_scoring_config(_ctx: AuthContext = Depends(require_permission(SCAN_READ))):
    """Return active compliance scoring thresholds and weights."""
    config = get_scoring_config()
    public = config.to_public_dict()
    return ScoringConfigResponse(
        severity_weights=public["severity_weights"],
        finding_type_weights=public["finding_type_weights"],
        compliance_thresholds=ComplianceThresholdsResponse(**public["compliance_thresholds"]),
        classification_thresholds=ClassificationThresholdsResponse(
            **public["classification_thresholds"]
        ),
        rules=ScoringRulesResponse(**public["rules"]),
    )
