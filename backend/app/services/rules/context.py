"""Build rule evaluation context from scan results and optional model metadata."""

from app.models.scan import Scan
from app.models.scan_finding import ScanFinding
from app.services.rules.types import RuleEvaluationContext
from app.services.scanner.types import DetectionResult


def context_from_detections(
    detections: list[DetectionResult],
    *,
    risk_score: int | None = None,
    compliance_status: str | None = None,
    classification: str | None = None,
    model_is_external: bool = False,
    model_deployment: str | None = None,
    model_provider: str | None = None,
) -> RuleEvaluationContext:
    detected = {d.finding_type for d in detections}
    return RuleEvaluationContext(
        detected_types=detected,
        risk_score=risk_score,
        compliance_status=compliance_status,
        classification=classification,
        model_is_external=model_is_external,
        model_deployment=model_deployment,
        model_provider=model_provider,
        findings_count=len(detections),
    )


def context_from_scan(
    scan: Scan,
    *,
    model_is_external: bool = False,
    model_deployment: str | None = None,
    model_provider: str | None = None,
) -> RuleEvaluationContext:
    findings: list[ScanFinding] = list(scan.findings or [])
    detected = {f.finding_type for f in findings}
    return RuleEvaluationContext(
        detected_types=detected,
        risk_score=scan.risk_score,
        compliance_status=scan.compliance_status,
        classification=scan.classification,
        model_is_external=model_is_external,
        model_deployment=model_deployment,
        model_provider=model_provider,
        findings_count=len(findings),
    )
