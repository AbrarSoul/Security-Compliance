from app.services.prompts import patterns
from app.services.prompts.constants import DECISION_WARN, FINDING_CONFIDENTIAL
from app.services.prompts.detectors.base import PromptDetector
from app.services.prompts.types import PromptFinding


class ConfidentialDetector(PromptDetector):
    name = "confidential"

    def detect(self, text: str) -> list[PromptFinding]:
        match = patterns.CONFIDENTIAL_RE.search(text)
        if not match:
            return []
        return [
            PromptFinding(
                finding_type=FINDING_CONFIDENTIAL,
                severity="medium",
                message="Confidential or proprietary company data marker detected",
                matched_span=match.group(0),
                suggested_decision=DECISION_WARN,
            )
        ]
