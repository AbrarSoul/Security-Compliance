"""Map prompt findings to allow / warn / block decisions."""

from app.services.prompts.constants import (
    DECISION_ALLOW,
    DECISION_BLOCK,
    DECISION_ORDER,
    DECISION_WARN,
    FINDING_DEFAULT_DECISION,
    RISK_SCORE_BLOCK_MIN,
    RISK_SCORE_WARN_MIN,
)
from app.services.prompts.types import PromptFinding, PromptScanOutcome


class PromptDecisionEngine:
    def decide(
        self,
        *,
        findings: list[PromptFinding],
        risk_score: int,
        risk_level: str,
        masked_prompt: str,
    ) -> PromptScanOutcome:
        decision = self._worst_decision(findings, risk_score)
        blocking, warnings, recommendations = self._build_reasons(findings, decision)

        return PromptScanOutcome(
            decision=decision,
            risk_score=risk_score,
            risk_level=risk_level,
            findings=findings,
            masked_prompt=masked_prompt,
            blocking_reasons=blocking,
            warning_reasons=warnings,
            recommendations=recommendations,
            can_proceed=decision != DECISION_BLOCK,
        )

    def _worst_decision(self, findings: list[PromptFinding], risk_score: int) -> str:
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
        self, findings: list[PromptFinding], decision: str
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
                "Remove secrets, credentials, and injection patterns before resubmitting."
            )
        elif decision == DECISION_WARN:
            recommendations.append(
                "Review sensitive content; proceed only if disclosure is authorized."
            )
        else:
            recommendations.append("No sensitive content detected; prompt may proceed.")

        return blocking, warnings, recommendations
