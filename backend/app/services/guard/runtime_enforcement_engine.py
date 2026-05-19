"""Real-time enforcement: worst-of scan, rule, and policy decisions."""

from app.services.execution.constants import DECISION_ORDER
from app.services.guard.types import GuardDecision


class RuntimeEnforcementEngine:
    def merge(
        self,
        *,
        scan_decision: str,
        scan_risk_score: int,
        scan_risk_level: str,
        scan_reasons: list[str],
        scan_source: str,
        rule_decision: str | None = None,
        rule_risk_score: int = 0,
        rule_reasons: list[str] | None = None,
        policy_decision: str | None = None,
        policy_risk_score: int = 0,
        policy_reasons: list[str] | None = None,
    ) -> tuple[str, int, str, list[str], list[str], list[str]]:
        decisions = [
            (scan_decision, scan_risk_score, scan_risk_level, scan_reasons, scan_source),
        ]
        if rule_decision:
            decisions.append(
                (
                    rule_decision,
                    rule_risk_score,
                    _level_from_score(rule_risk_score),
                    rule_reasons or [],
                    "runtime_rule",
                )
            )
        if policy_decision:
            decisions.append(
                (
                    policy_decision,
                    policy_risk_score,
                    _level_from_score(policy_risk_score),
                    policy_reasons or [],
                    "runtime_policy",
                )
            )

        final = max(decisions, key=lambda d: DECISION_ORDER.get(d[0], 0))
        final_decision, final_score, final_level, final_reasons, _ = final

        blocking: list[str] = []
        warnings: list[str] = []
        for dec, _, _, reasons, _ in decisions:
            if dec == "block":
                blocking.extend(reasons)
            elif dec == "warn":
                warnings.extend(reasons)

        recommendations: list[str] = []
        if final_decision == "block":
            recommendations.append("Execution halted: compliance guard blocked this operation.")
        elif final_decision == "warn":
            recommendations.append("Proceed with caution; review warnings before continuing.")
        else:
            recommendations.append("Guard checks passed.")

        risk_score = max(d[1] for d in decisions)
        risk_level = max((d[2] for d in decisions), key=lambda lv: _level_rank(lv))
        return final_decision, risk_score, risk_level, blocking, warnings, recommendations

    def to_guard_decision(
        self,
        decision: str,
        risk_score: int,
        risk_level: str,
        source: str,
        reasons: list[str],
    ) -> GuardDecision:
        return GuardDecision(
            decision=decision,
            risk_score=risk_score,
            risk_level=risk_level,
            source=source,
            reasons=reasons,
        )


def _level_from_score(score: int) -> str:
    if score >= 70:
        return "critical"
    if score >= 40:
        return "high"
    if score >= 20:
        return "medium"
    return "low"


def _level_rank(level: str) -> int:
    return {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(level, 0)
