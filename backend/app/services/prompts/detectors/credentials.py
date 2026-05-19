from app.services.prompts import patterns
from app.services.prompts.constants import (
    DECISION_BLOCK,
    FINDING_API_KEY,
    FINDING_PASSWORD,
)
from app.services.prompts.detectors.base import PromptDetector
from app.services.prompts.types import PromptFinding
from app.services.scanner.patterns import mask_value


class CredentialDetector(PromptDetector):
    name = "credentials"

    def detect(self, text: str) -> list[PromptFinding]:
        findings: list[PromptFinding] = []

        for match in patterns.AWS_ACCESS_KEY_RE.finditer(text):
            findings.append(
                PromptFinding(
                    finding_type=FINDING_API_KEY,
                    severity="critical",
                    message="AWS access key ID detected in prompt",
                    matched_span=match.group(0),
                    masked_span=mask_value(match.group(0), visible=4),
                    suggested_decision=DECISION_BLOCK,
                    evidence={"provider": "aws", "kind": "access_key_id"},
                )
            )

        for match in patterns.AWS_SECRET_KEY_RE.finditer(text):
            secret = match.group(1)
            findings.append(
                PromptFinding(
                    finding_type=FINDING_API_KEY,
                    severity="critical",
                    message="AWS secret access key detected in prompt",
                    matched_span=match.group(0)[:80],
                    masked_span="aws_secret_key=***",
                    suggested_decision=DECISION_BLOCK,
                    evidence={"provider": "aws", "kind": "secret_access_key"},
                )
            )

        for match in patterns.API_KEY_ASSIGNMENT_RE.finditer(text):
            findings.append(
                PromptFinding(
                    finding_type=FINDING_API_KEY,
                    severity="critical",
                    message="API key or secret assignment detected in prompt",
                    matched_span=match.group(0)[:80],
                    masked_span=mask_value(match.group(0), visible=6),
                    suggested_decision=DECISION_BLOCK,
                    evidence={"kind": "assignment"},
                )
            )

        for match in patterns.STANDALONE_API_KEY_RE.finditer(text):
            val = match.group(0)
            if patterns.AWS_ACCESS_KEY_RE.fullmatch(val):
                continue
            findings.append(
                PromptFinding(
                    finding_type=FINDING_API_KEY,
                    severity="critical",
                    message="Standalone API key or token detected",
                    matched_span=val,
                    masked_span=mask_value(val, visible=4),
                    suggested_decision=DECISION_BLOCK,
                )
            )

        if patterns.PASSWORD_RE.search(text):
            findings.append(
                PromptFinding(
                    finding_type=FINDING_PASSWORD,
                    severity="critical",
                    message="Password-like secret detected in prompt",
                    suggested_decision=DECISION_BLOCK,
                )
            )

        for match in patterns.PASSWORD_ASSIGN_RE.finditer(text):
            findings.append(
                PromptFinding(
                    finding_type=FINDING_PASSWORD,
                    severity="high",
                    message="Password assignment detected in prompt",
                    matched_span=match.group(0)[:60],
                    masked_span=f"{match.group(1)}=***",
                    suggested_decision=DECISION_BLOCK,
                )
            )

        return findings
