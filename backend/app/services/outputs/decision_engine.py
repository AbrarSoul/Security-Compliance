from app.services.outputs.constants import (
    DECISION_ALLOW,
    DECISION_BLOCK,
    DECISION_ORDER,
    DECISION_WARN,
    FINDING_DEFAULT_DECISION,
    RISK_SCORE_BLOCK_MIN,
    RISK_SCORE_WARN_MIN,
)
from app.services.outputs.types import OutputFinding, OutputScanOutcome


class OutputDecisionEngine:
    def decide(
        self,
        *,
        findings: list[OutputFinding],
        risk_score: int,
        risk_level: str,
        masked_output: str,
    ) -> OutputScanOutcome:
        decision = self._worst_decision(findings, risk_score)
        blocking, warnings, recommendations = self._build_reasons(findings, decision)

        redacted = "" if decision == DECISION_BLOCK else masked_output
        can_display = decision != DECISION_BLOCK

        return OutputScanOutcome(
            decision=decision,
            risk_score=risk_score,
            risk_level=risk_level,
            findings=findings,
            masked_output=masked_output,
            redacted_output=redacted,
            blocking_reasons=blocking,
            warning_reasons=warnings,
            recommendations=recommendations,
            can_display=can_display,
        )

    def _worst_decision(self, findings: list[OutputFinding], risk_score: int) -> str:
        decisions: list[str] = []
        for finding in findings:
            suggested = finding.suggested_decision or FINDING_DEFAULT_DECISION.get(
                finding.finding_type, DECISION_WARN
            )
            decisions.append(suggested)

        if risk_score >= RISK_SCORE_BLOCK_MIN:
            decisions.append(DECISION_BLOCK)
        elif risk_score >= RISK_SCORE_WARN_MIN:
            decisions.append(DECISION_WARN)

        if not decisions:
            return DECISION_ALLOW
        return max(decisions, key=lambda d: DECISION_ORDER.get(d, 0))

    def _build_reasons(
        self, findings: list[OutputFinding], decision: str
    ) -> tuple[list[str], list[str], list[str]]:
        blocking: list[str] = []
        warnings: list[str] = []
        recommendations: list[str] = []

        for f in findings:
            effective = f.suggested_decision or FINDING_DEFAULT_DECISION.get(
                f.finding_type, DECISION_WARN
            )
            if effective == DECISION_BLOCK:
                blocking.append(f.message)
            elif effective == DECISION_WARN:
                warnings.append(f.message)

        if decision == DECISION_BLOCK:
            recommendations.append(
                "Output withheld: regenerate without secrets or harmful content."
            )
        elif decision == DECISION_WARN:
            recommendations.append(
                "Review redacted output before displaying to end users."
            )
        else:
            recommendations.append("Output passed compliance checks and may be displayed.")

        return blocking, warnings, recommendations
