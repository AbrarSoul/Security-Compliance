from dataclasses import dataclass

from app.services.recommendations.templates import (
    FINDING_TEMPLATES,
    SEVERITY_PRIORITY_OVERRIDE,
    STATUS_RECOMMENDATIONS,
    RecommendationTemplate,
    render_description,
)
from app.services.recommendations.types import Priority, RecommendationResult
from app.services.scoring.types import ComplianceScoreResult, ComplianceStatus
from app.services.scanner.types import DetectionResult


@dataclass
class FindingContext:
    finding_type: str
    severity: str
    column_name: str | None
    sample_count: int
    match_rate: float


class RecommendationEngine:
    """Generate actionable recommendations from scan findings and compliance score."""

    def generate(
        self,
        findings: list[DetectionResult] | list[FindingContext],
        score_result: ComplianceScoreResult | None = None,
        *,
        compliance_status: ComplianceStatus | None = None,
        classification: str | None = None,
    ) -> list[RecommendationResult]:
        contexts = self._normalize_findings(findings)
        recommendations: list[RecommendationResult] = []
        seen_keys: set[str] = set()

        for ctx in contexts:
            rec = self._from_finding(ctx)
            if rec is None:
                continue
            key = f"{rec.action_type}:{rec.finding_type}:{rec.column_name}"
            if key in seen_keys:
                continue
            seen_keys.add(key)
            recommendations.append(rec)

        status = compliance_status or (score_result.compliance_status if score_result else None)
        if status:
            for rec in self._from_compliance_status(status, contexts):
                key = f"{rec.action_type}:{rec.title}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    recommendations.append(rec)

        if score_result and score_result.classification in ("confidential", "restricted"):
            rec = self._classification_recommendation(score_result.classification, contexts)
            key = f"{rec.action_type}:{rec.title}"
            if key not in seen_keys:
                recommendations.append(rec)

        if self._count_critical(contexts) >= 2:
            rec = self._multiple_critical_recommendation(contexts)
            key = f"{rec.action_type}:{rec.title}"
            if key not in seen_keys:
                recommendations.append(rec)

        return sorted(recommendations, key=self._sort_key)

    def _normalize_findings(
        self, findings: list[DetectionResult] | list[FindingContext]
    ) -> list[FindingContext]:
        result: list[FindingContext] = []
        for f in findings:
            if isinstance(f, FindingContext):
                result.append(f)
            else:
                result.append(
                    FindingContext(
                        finding_type=f.finding_type,
                        severity=f.severity,
                        column_name=f.column_name,
                        sample_count=f.sample_count,
                        match_rate=f.match_rate,
                    )
                )
        return result

    def _from_finding(self, ctx: FindingContext) -> RecommendationResult | None:
        template = FINDING_TEMPLATES.get(ctx.finding_type)
        if template is None:
            return None

        priority = SEVERITY_PRIORITY_OVERRIDE.get(ctx.severity, template.priority)
        if ctx.severity == "critical":
            priority = "high"

        return RecommendationResult(
            priority=priority,
            title=template.title,
            description=render_description(template, ctx.column_name),
            action_type=template.action_type,
            finding_type=ctx.finding_type,
            column_name=ctx.column_name,
            related_finding_types=[ctx.finding_type],
            metadata={
                "sample_count": ctx.sample_count,
                "match_rate": ctx.match_rate,
                "severity": ctx.severity,
            },
        )

    def _from_compliance_status(
        self, status: ComplianceStatus, contexts: list[FindingContext]
    ) -> list[RecommendationResult]:
        templates = STATUS_RECOMMENDATIONS.get(status, [])
        finding_types = list({c.finding_type for c in contexts})
        return [
            RecommendationResult(
                priority=priority,
                title=title,
                description=description,
                action_type=action_type,
                related_finding_types=finding_types,
                metadata={"compliance_status": status},
            )
            for priority, action_type, title, description in templates
        ]

    def _classification_recommendation(
        self, classification: str, contexts: list[FindingContext]
    ) -> RecommendationResult:
        return RecommendationResult(
            priority="high" if classification == "restricted" else "medium",
            title=f"Apply {classification} data controls",
            description=f"This dataset is classified as {classification}. "
            "Encrypt data at rest and in transit, enforce role-based access control, "
            "and prohibit export to unsecured locations.",
            action_type="encrypt",
            related_finding_types=list({c.finding_type for c in contexts}),
            metadata={"classification": classification},
        )

    def _multiple_critical_recommendation(
        self, contexts: list[FindingContext]
    ) -> RecommendationResult:
        critical_types = [c.finding_type for c in contexts if c.severity == "critical"]
        return RecommendationResult(
            priority="high",
            title="Remediate multiple critical exposures",
            description="Multiple critical findings were detected "
            f"({', '.join(sorted(set(critical_types)))}). "
            "Prioritize removal or encryption of affected columns before any production use.",
            action_type="review_policy",
            related_finding_types=critical_types,
            metadata={"critical_finding_count": len(critical_types)},
        )

    def _count_critical(self, contexts: list[FindingContext]) -> int:
        return sum(1 for c in contexts if c.severity == "critical")

    @staticmethod
    def _sort_key(rec: RecommendationResult) -> tuple[int, str]:
        order = {"high": 0, "medium": 1, "low": 2}
        return (order.get(rec.priority, 3), rec.title)
