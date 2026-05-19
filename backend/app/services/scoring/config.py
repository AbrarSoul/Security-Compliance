from dataclasses import dataclass
from functools import lru_cache

from app.core.config import get_settings


def _parse_weight_map(raw: str, defaults: dict[str, int]) -> dict[str, int]:
    if not raw.strip():
        return defaults.copy()
    result = defaults.copy()
    for part in raw.split(","):
        part = part.strip()
        if not part or ":" not in part:
            continue
        key, value = part.split(":", 1)
        try:
            result[key.strip().lower()] = int(value.strip())
        except ValueError:
            continue
    return result


@dataclass(frozen=True)
class ScoringConfig:
    severity_weights: dict[str, int]
    finding_type_weights: dict[str, int]
    compliant_max: int
    risky_max: int
    score_max: int
    density_multiplier: int
    classification_restricted_min: int
    classification_confidential_min: int
    classification_internal_min: int
    critical_escalation_match_rate: float
    force_non_compliant_on_critical: bool

    @classmethod
    def from_settings(cls) -> "ScoringConfig":
        settings = get_settings()
        return cls(
            severity_weights=_parse_weight_map(
                settings.score_severity_weights,
                {"low": 5, "medium": 15, "high": 25, "critical": 40},
            ),
            finding_type_weights=_parse_weight_map(
                settings.score_finding_type_weights,
                {
                    "email": 10,
                    "phone": 10,
                    "password": 35,
                    "api_key": 40,
                    "name": 5,
                    "sensitive_field": 8,
                },
            ),
            compliant_max=settings.score_compliant_max,
            risky_max=settings.score_risky_max,
            score_max=settings.score_max,
            density_multiplier=settings.score_density_multiplier,
            classification_restricted_min=settings.score_classification_restricted_min,
            classification_confidential_min=settings.score_classification_confidential_min,
            classification_internal_min=settings.score_classification_internal_min,
            critical_escalation_match_rate=settings.score_critical_escalation_match_rate,
            force_non_compliant_on_critical=settings.score_force_non_compliant_on_critical,
        )

    def to_public_dict(self) -> dict:
        return {
            "severity_weights": self.severity_weights,
            "finding_type_weights": self.finding_type_weights,
            "compliance_thresholds": {
                "compliant_max": self.compliant_max,
                "risky_max": self.risky_max,
                "score_max": self.score_max,
            },
            "classification_thresholds": {
                "restricted_min": self.classification_restricted_min,
                "confidential_min": self.classification_confidential_min,
                "internal_min": self.classification_internal_min,
            },
            "rules": {
                "density_multiplier": self.density_multiplier,
                "critical_escalation_match_rate": self.critical_escalation_match_rate,
                "force_non_compliant_on_critical": self.force_non_compliant_on_critical,
            },
        }


@lru_cache
def get_scoring_config() -> ScoringConfig:
    return ScoringConfig.from_settings()
