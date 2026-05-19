from app.services.outputs import patterns
from app.services.outputs.constants import (
    DECISION_BLOCK,
    FINDING_HARMFUL,
    FINDING_TOXIC,
    MASK_HARMFUL,
    MASK_TOXIC,
)
from app.services.outputs.detectors.base import OutputDetector
from app.services.outputs.types import OutputFinding


class HarmfulContentDetector(OutputDetector):
    name = "harmful"

    def detect(self, text: str) -> list[OutputFinding]:
        findings: list[OutputFinding] = []

        for pattern in patterns.HARMFUL_PATTERNS:
            match = pattern.search(text)
            if match:
                findings.append(
                    OutputFinding(
                        finding_type=FINDING_HARMFUL,
                        severity="critical",
                        message="Harmful or unsafe content detected in output",
                        matched_span=match.group(0)[:120],
                        masked_span=MASK_HARMFUL,
                        suggested_decision=DECISION_BLOCK,
                    )
                )
                break

        for pattern in patterns.TOXIC_PATTERNS:
            match = pattern.search(text)
            if match:
                findings.append(
                    OutputFinding(
                        finding_type=FINDING_TOXIC,
                        severity="high",
                        message="Toxic or abusive content detected in output",
                        matched_span=match.group(0)[:80],
                        masked_span=MASK_TOXIC,
                        suggested_decision=DECISION_BLOCK,
                    )
                )
                break

        return findings
