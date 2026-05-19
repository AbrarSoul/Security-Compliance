from app.services.outputs import patterns
from app.services.outputs.constants import (
    DECISION_WARN,
    FINDING_BUSINESS,
    FINDING_CONFIDENTIAL,
    MASK_BUSINESS,
    MASK_CONFIDENTIAL,
)
from app.services.outputs.detectors.base import OutputDetector
from app.services.outputs.types import OutputFinding


class ConfidentialDetector(OutputDetector):
    name = "confidential"

    def detect(self, text: str) -> list[OutputFinding]:
        findings: list[OutputFinding] = []

        match = patterns.CONFIDENTIAL_RE.search(text)
        if match:
            findings.append(
                OutputFinding(
                    finding_type=FINDING_CONFIDENTIAL,
                    severity="medium",
                    message="Confidential company data marker in output",
                    matched_span=match.group(0),
                    masked_span=MASK_CONFIDENTIAL,
                    suggested_decision=DECISION_WARN,
                )
            )

        biz = patterns.BUSINESS_SENSITIVE_RE.search(text)
        if biz:
            findings.append(
                OutputFinding(
                    finding_type=FINDING_BUSINESS,
                    severity="high",
                    message="Sensitive business information in output",
                    matched_span=biz.group(0),
                    masked_span=MASK_BUSINESS,
                    suggested_decision=DECISION_WARN,
                )
            )

        return findings
