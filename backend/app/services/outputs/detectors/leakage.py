from app.services.outputs import patterns
from app.services.outputs.constants import (
    DECISION_BLOCK,
    DECISION_WARN,
    FINDING_API_KEY,
    FINDING_BANK_ACCOUNT,
    FINDING_CREDIT_CARD,
    FINDING_EMAIL,
    FINDING_FINANCIAL,
    FINDING_HEALTHCARE,
    FINDING_PASSWORD,
    FINDING_PHONE,
    FINDING_SSN,
    MASK_API_KEY,
    MASK_EMAIL,
    MASK_PASSWORD,
    MASK_SSN,
)
from app.services.outputs.detectors.base import OutputDetector
from app.services.outputs.types import OutputFinding


class LeakageDetector(OutputDetector):
    name = "leakage"

    def detect(self, text: str) -> list[OutputFinding]:
        findings: list[OutputFinding] = []

        for match in patterns.AWS_SECRET_KEY_RE.finditer(text):
            findings.append(
                OutputFinding(
                    finding_type=FINDING_API_KEY,
                    severity="critical",
                    message="API secret leaked in model output",
                    matched_span=match.group(0)[:80],
                    masked_span=MASK_API_KEY,
                    suggested_decision=DECISION_BLOCK,
                    evidence={"provider": "aws"},
                )
            )

        for match in patterns.AWS_ACCESS_KEY_RE.finditer(text):
            findings.append(
                OutputFinding(
                    finding_type=FINDING_API_KEY,
                    severity="critical",
                    message="Cloud access key leaked in model output",
                    matched_span=match.group(0),
                    masked_span=MASK_API_KEY,
                    suggested_decision=DECISION_BLOCK,
                )
            )

        for match in patterns.API_KEY_ASSIGNMENT_RE.finditer(text):
            findings.append(
                OutputFinding(
                    finding_type=FINDING_API_KEY,
                    severity="critical",
                    message="API key assignment leaked in output",
                    matched_span=match.group(0)[:80],
                    masked_span=MASK_API_KEY,
                    suggested_decision=DECISION_BLOCK,
                )
            )

        for match in patterns.STANDALONE_API_KEY_RE.finditer(text):
            val = match.group(0)
            if patterns.AWS_ACCESS_KEY_RE.fullmatch(val):
                continue
            findings.append(
                OutputFinding(
                    finding_type=FINDING_API_KEY,
                    severity="critical",
                    message="Standalone API token leaked in output",
                    matched_span=val,
                    masked_span=MASK_API_KEY,
                    suggested_decision=DECISION_BLOCK,
                )
            )

        for match in patterns.PASSWORD_ASSIGN_RE.finditer(text):
            findings.append(
                OutputFinding(
                    finding_type=FINDING_PASSWORD,
                    severity="critical",
                    message="Password leaked in model output",
                    matched_span=match.group(0)[:60],
                    masked_span=MASK_PASSWORD,
                    suggested_decision=DECISION_BLOCK,
                )
            )

        if patterns.PASSWORD_RE.search(text) and not any(
            f.finding_type == FINDING_PASSWORD for f in findings
        ):
            findings.append(
                OutputFinding(
                    finding_type=FINDING_PASSWORD,
                    severity="high",
                    message="Password-like credential pattern in output",
                    masked_span=MASK_PASSWORD,
                    suggested_decision=DECISION_BLOCK,
                )
            )

        for match in patterns.SSN_RE.finditer(text):
            findings.append(
                OutputFinding(
                    finding_type=FINDING_SSN,
                    severity="critical",
                    message="Social Security Number leaked in output",
                    matched_span=match.group(0),
                    masked_span=MASK_SSN,
                    suggested_decision=DECISION_BLOCK,
                )
            )

        emails = list(patterns.EMAIL_IN_TEXT_RE.finditer(text))
        if emails:
            findings.append(
                OutputFinding(
                    finding_type=FINDING_EMAIL,
                    severity="medium",
                    message=f"Email address leaked ({len(emails)} occurrence(s))",
                    masked_span=MASK_EMAIL,
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
                OutputFinding(
                    finding_type=FINDING_PHONE,
                    severity="medium",
                    message=f"Phone number leaked ({len(phones)} occurrence(s))",
                    suggested_decision=DECISION_WARN,
                    evidence={"count": len(phones)},
                )
            )

        for match in patterns.CREDIT_CARD_RE.finditer(text):
            digits = "".join(c for c in match.group(0) if c.isdigit())
            if len(digits) >= 13:
                findings.append(
                    OutputFinding(
                        finding_type=FINDING_CREDIT_CARD,
                        severity="critical",
                        message="Credit card number leaked in output",
                        suggested_decision=DECISION_BLOCK,
                    )
                )
                break

        if patterns.BANK_CONTEXT_RE.search(text):
            findings.append(
                OutputFinding(
                    finding_type=FINDING_BANK_ACCOUNT,
                    severity="high",
                    message="Banking information leaked in output",
                    suggested_decision=DECISION_WARN,
                )
            )

        if patterns.FINANCIAL_KEYWORDS_RE.search(text):
            findings.append(
                OutputFinding(
                    finding_type=FINDING_FINANCIAL,
                    severity="medium",
                    message="Sensitive financial data in output",
                    suggested_decision=DECISION_WARN,
                )
            )

        if patterns.HEALTHCARE_KEYWORDS_RE.search(text):
            findings.append(
                OutputFinding(
                    finding_type=FINDING_HEALTHCARE,
                    severity="high",
                    message="Healthcare / PHI content in output",
                    suggested_decision=DECISION_WARN,
                )
            )

        return findings
