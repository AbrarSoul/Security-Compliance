from app.services.prompts import patterns
from app.services.prompts.constants import DECISION_BLOCK, DECISION_WARN, FINDING_HEALTHCARE
from app.services.prompts.detectors.base import PromptDetector
from app.services.prompts.types import PromptFinding


class HealthcareDetector(PromptDetector):
    name = "healthcare"

    def detect(self, text: str) -> list[PromptFinding]:
        findings: list[PromptFinding] = []

        if patterns.HEALTHCARE_KEYWORDS_RE.search(text):
            severity = "high" if patterns.SSN_RE.search(text) else "medium"
            findings.append(
                PromptFinding(
                    finding_type=FINDING_HEALTHCARE,
                    severity=severity,
                    message="Protected health information context detected",
                    suggested_decision=DECISION_BLOCK if severity == "high" else DECISION_WARN,
                    evidence={"hipaa_relevant": True},
                )
            )

        if patterns.DOB_CONTEXT_RE.search(text):
            findings.append(
                PromptFinding(
                    finding_type=FINDING_HEALTHCARE,
                    severity="medium",
                    message="Date of birth / patient demographic context detected",
                    suggested_decision=DECISION_WARN,
                )
            )

        return findings
