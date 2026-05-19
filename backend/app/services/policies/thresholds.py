"""Map validation scores to allow / warn / block using policy thresholds."""

from typing import Any


class PolicyThresholdConfig:
    """Score thresholds (higher score = more compliant / safer)."""

    def __init__(
        self,
        *,
        block_below: int = 40,
        warn_below: int = 70,
    ):
        self.block_below = block_below
        self.warn_below = warn_below

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "PolicyThresholdConfig":
        if not data:
            return cls()
        return cls(
            block_below=int(data.get("block_below", 40)),
            warn_below=int(data.get("warn_below", 70)),
        )

    def to_dict(self) -> dict[str, int]:
        return {
            "block_below": self.block_below,
            "warn_below": self.warn_below,
        }


def resolve_validation_score(
    *,
    validation_score: int | None,
    risk_score: int | None,
) -> int | None:
    """Prefer explicit validation_score; otherwise derive from risk (100 - risk)."""
    if validation_score is not None:
        return validation_score
    if risk_score is not None:
        return max(0, min(100, 100 - risk_score))
    return None


def action_from_validation_score(
    score: int,
    thresholds: PolicyThresholdConfig,
) -> str:
    """
    Apply threshold bands:
    - score < block_below → block
    - block_below <= score < warn_below → warn
    - score >= warn_below → allow
    """
    if score < thresholds.block_below:
        return "block"
    if score < thresholds.warn_below:
        return "warn"
    return "allow"


def threshold_decision_reason(score: int, action: str, thresholds: PolicyThresholdConfig) -> str:
    if action == "block":
        return (
            f"Validation score {score} is below block threshold "
            f"({thresholds.block_below})"
        )
    if action == "warn":
        return (
            f"Validation score {score} is below warn threshold "
            f"({thresholds.warn_below})"
        )
    return f"Validation score {score} meets allow threshold ({thresholds.warn_below}+)"
