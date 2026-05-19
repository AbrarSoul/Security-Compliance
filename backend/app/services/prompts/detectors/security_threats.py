from app.services.prompts import patterns
from app.services.prompts.constants import (
    DECISION_BLOCK,
    DECISION_WARN,
    FINDING_JAILBREAK,
    FINDING_PROMPT_INJECTION,
    FINDING_SUSPICIOUS_INSTRUCTION,
)
from app.services.prompts.detectors.base import PromptDetector
from app.services.prompts.types import PromptFinding


class SecurityThreatDetector(PromptDetector):
    name = "security_threats"

    def detect(self, text: str) -> list[PromptFinding]:
        findings: list[PromptFinding] = []

        for pattern in patterns.INJECTION_PATTERNS:
            match = pattern.search(text)
            if match:
                findings.append(
                    PromptFinding(
                        finding_type=FINDING_PROMPT_INJECTION,
                        severity="critical",
                        message="Prompt injection attempt detected",
                        matched_span=match.group(0)[:120],
                        suggested_decision=DECISION_BLOCK,
                        evidence={"pattern": pattern.pattern[:80]},
                    )
                )
                break

        for pattern in patterns.JAILBREAK_PATTERNS:
            match = pattern.search(text)
            if match:
                findings.append(
                    PromptFinding(
                        finding_type=FINDING_JAILBREAK,
                        severity="critical",
                        message="Jailbreak attempt detected",
                        matched_span=match.group(0)[:120],
                        suggested_decision=DECISION_BLOCK,
                        evidence={"pattern": pattern.pattern[:80]},
                    )
                )
                break

        for pattern in patterns.SUSPICIOUS_PATTERNS:
            match = pattern.search(text)
            if match:
                findings.append(
                    PromptFinding(
                        finding_type=FINDING_SUSPICIOUS_INSTRUCTION,
                        severity="high",
                        message="Suspicious or malicious instruction detected",
                        matched_span=match.group(0)[:120],
                        suggested_decision=DECISION_WARN,
                        evidence={"pattern": pattern.pattern[:80]},
                    )
                )
                break

        return findings
