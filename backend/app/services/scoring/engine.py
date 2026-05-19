from app.services.scanner.types import DetectionResult
from app.services.scoring.config import ScoringConfig, get_scoring_config
from app.services.scoring.types import (
    ComplianceScoreResult,
    ComplianceStatus,
    DataClassification,
    FindingContribution,
    RiskLevel,
)

_SEVERITY_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


class ComplianceScoringEngine:
    """Configurable compliance scoring with risk levels and status classification."""

    def __init__(self, config: ScoringConfig | None = None):
        self.config = config or get_scoring_config()

    def score(self, findings: list[DetectionResult]) -> ComplianceScoreResult:
        if not findings:
            return ComplianceScoreResult(
                risk_score=0,
                compliance_status="compliant",
                classification="public",
                highest_severity=None,
                total_findings=0,
                thresholds_applied=self._thresholds_snapshot(),
            )

        contributions = [self._score_finding(f) for f in findings]
        raw_score = sum(c.total_points for c in contributions)
        risk_score = min(raw_score, self.config.score_max)

        highest = self._highest_severity(findings)
        adjustments: list[dict] = []

        compliance_status = self._classify_compliance(risk_score, findings, adjustments)
        classification = self._classify_data(findings, risk_score)

        return ComplianceScoreResult(
            risk_score=risk_score,
            compliance_status=compliance_status,
            classification=classification,
            highest_severity=highest,
            total_findings=len(findings),
            contributions=contributions,
            adjustments=adjustments,
            thresholds_applied=self._thresholds_snapshot(),
        )

    def _score_finding(self, finding: DetectionResult) -> FindingContribution:
        severity = finding.severity if finding.severity in _SEVERITY_ORDER else "medium"
        base = self.config.severity_weights.get(severity, 10)
        density = int(finding.match_rate * self.config.density_multiplier)
        type_weight = self.config.finding_type_weights.get(finding.finding_type, 0)
        total = base + density + type_weight

        return FindingContribution(
            finding_type=finding.finding_type,
            severity=severity,  # type: ignore[arg-type]
            column_name=finding.column_name,
            base_points=base,
            density_points=density,
            type_weight_points=type_weight,
            total_points=total,
            match_rate=finding.match_rate,
        )

    def _classify_compliance(
        self,
        risk_score: int,
        findings: list[DetectionResult],
        adjustments: list[dict],
    ) -> ComplianceStatus:
        if self.config.force_non_compliant_on_critical:
            for f in findings:
                if f.severity == "critical" and f.match_rate >= self.config.critical_escalation_match_rate:
                    adjustments.append({
                        "type": "critical_escalation",
                        "reason": f"Critical finding '{f.finding_type}' exceeded match rate threshold",
                        "forced_status": "non_compliant",
                    })
                    return "non_compliant"

        if risk_score <= self.config.compliant_max:
            return "compliant"
        if risk_score <= self.config.risky_max:
            return "risky"
        return "non_compliant"

    def _classify_data(
        self, findings: list[DetectionResult], risk_score: int
    ) -> DataClassification:
        types = {f.finding_type for f in findings}

        if (
            "password" in types
            or "api_key" in types
            or risk_score >= self.config.classification_restricted_min
        ):
            return "restricted"
        if (
            "email" in types
            or "phone" in types
            or risk_score >= self.config.classification_confidential_min
        ):
            return "confidential"
        if (
            "name" in types
            or "sensitive_field" in types
            or risk_score >= self.config.classification_internal_min
        ):
            return "internal"
        return "public"

    def _highest_severity(self, findings: list[DetectionResult]) -> RiskLevel | None:
        if not findings:
            return None
        return max(
            (f.severity for f in findings if f.severity in _SEVERITY_ORDER),
            key=lambda s: _SEVERITY_ORDER[s],
            default="low",
        )  # type: ignore[return-value]

    def _thresholds_snapshot(self) -> dict[str, int]:
        return {
            "compliant_max": self.config.compliant_max,
            "risky_max": self.config.risky_max,
            "score_max": self.config.score_max,
            "classification_restricted_min": self.config.classification_restricted_min,
            "classification_confidential_min": self.config.classification_confidential_min,
            "classification_internal_min": self.config.classification_internal_min,
        }
