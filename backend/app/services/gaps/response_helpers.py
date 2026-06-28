"""Helpers for enriching gap API responses."""

from app.models.compliance_gap import ComplianceGap
from app.schemas.gaps import ComplianceGapResponse, FrameworkRefResponse
from app.services.compliance.framework_mappings import resolve_framework_refs


def gap_to_response(gap: ComplianceGap) -> ComplianceGapResponse:
    data = ComplianceGapResponse.model_validate(gap).model_dump()
    data["framework_refs"] = [
        FrameworkRefResponse.model_validate(ref) for ref in resolve_framework_refs(gap)
    ]
    return ComplianceGapResponse(**data)
