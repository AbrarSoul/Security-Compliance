from app.services.prompts import patterns
from app.services.prompts.constants import DECISION_BLOCK, DECISION_WARN, FINDING_EMAIL, FINDING_PHONE, FINDING_PII, FINDING_SSN
from app.services.prompts.detectors.base import PromptDetector
from app.services.prompts.types import PromptFinding
from app.services.scanner.patterns import mask_value


class PiiDetector(PromptDetector):
    name = "pii"

    def detect(self, text: str) -> list[PromptFinding]:
        findings: list[PromptFinding] = []

        for match in patterns.SSN_RE.finditer(text):
            findings.append(
                PromptFinding(
                    finding_type=FINDING_SSN,
                    severity="critical",
                    message="Social Security Number detected in prompt",
                    matched_span=match.group(0),
                    masked_span="***-**-****",
                    suggested_decision=DECISION_BLOCK,
                )
            )

        if patterns.SSN_CONTEXT_RE.search(text) and not findings:
            findings.append(
                PromptFinding(
                    finding_type=FINDING_PII,
                    severity="high",
                    message="SSN-related context in prompt",
                    suggested_decision=DECISION_WARN,
                )
            )

        emails = [m.group(0) for m in patterns.EMAIL_IN_TEXT_RE.finditer(text)]
        if emails:
            findings.append(
                PromptFinding(
                    finding_type=FINDING_EMAIL,
                    severity="medium",
                    message=f"Email address detected ({len(emails)} occurrence(s))",
                    masked_span=mask_value(emails[0], visible=2),
                    suggested_decision=DECISION_WARN,
                    evidence={"count": len(emails)},
                )
            )

        phones = [
            m.group(0)
            for m in patterns.PHONE_IN_TEXT_RE.finditer(text)
            if len(m.group(0).strip()) >= 10
        ]
        if phones:
            findings.append(
                PromptFinding(
                    finding_type=FINDING_PHONE,
                    severity="medium",
                    message=f"Phone number detected ({len(phones)} occurrence(s))",
                    masked_span=mask_value(phones[0], visible=3),
                    suggested_decision=DECISION_WARN,
                    evidence={"count": len(phones)},
                )
            )

        return findings
