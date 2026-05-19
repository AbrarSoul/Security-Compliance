from app.services.prompts import patterns
from app.services.prompts.constants import (
    DECISION_BLOCK,
    DECISION_WARN,
    FINDING_BANK_ACCOUNT,
    FINDING_CREDIT_CARD,
    FINDING_FINANCIAL,
)
from app.services.prompts.detectors.base import PromptDetector
from app.services.prompts.types import PromptFinding
from app.services.scanner.patterns import mask_value


class FinancialDetector(PromptDetector):
    name = "financial"

    def detect(self, text: str) -> list[PromptFinding]:
        findings: list[PromptFinding] = []

        for match in patterns.CREDIT_CARD_RE.finditer(text):
            digits = "".join(c for c in match.group(0) if c.isdigit())
            if len(digits) < 13:
                continue
            findings.append(
                PromptFinding(
                    finding_type=FINDING_CREDIT_CARD,
                    severity="critical",
                    message="Credit card number pattern detected in prompt",
                    matched_span=match.group(0)[:24],
                    masked_span=mask_value(digits, visible=4),
                    suggested_decision=DECISION_BLOCK,
                )
            )
            break

        if patterns.CREDIT_CARD_CONTEXT_RE.search(text) and not any(
            f.finding_type == FINDING_CREDIT_CARD for f in findings
        ):
            findings.append(
                PromptFinding(
                    finding_type=FINDING_FINANCIAL,
                    severity="high",
                    message="Financial card-related context in prompt",
                    suggested_decision=DECISION_WARN,
                )
            )

        if patterns.BANK_CONTEXT_RE.search(text):
            for match in patterns.BANK_ACCOUNT_RE.finditer(text):
                if len(match.group(0)) >= 8:
                    findings.append(
                        PromptFinding(
                            finding_type=FINDING_BANK_ACCOUNT,
                            severity="high",
                            message="Bank account number pattern detected",
                            matched_span=match.group(0)[:20],
                            masked_span=mask_value(match.group(0), visible=2),
                            suggested_decision=DECISION_WARN,
                        )
                    )
                    break

        if patterns.FINANCIAL_KEYWORDS_RE.search(text):
            findings.append(
                PromptFinding(
                    finding_type=FINDING_FINANCIAL,
                    severity="medium",
                    message="Sensitive financial terminology in prompt",
                    suggested_decision=DECISION_WARN,
                )
            )

        return findings
