"""Scan prompt text for sensitive data and security threats."""

from app.services.prompts.decision_engine import PromptDecisionEngine
from app.services.prompts.detectors import ALL_PROMPT_DETECTORS
from app.services.prompts.masking import mask_prompt
from app.services.prompts.scoring import score_findings
from app.services.prompts.types import PromptFinding, PromptScanOutcome


class PromptScanningEngine:
    def __init__(self, detectors=None, decision_engine: PromptDecisionEngine | None = None):
        self.detectors = detectors or ALL_PROMPT_DETECTORS
        self.decision_engine = decision_engine or PromptDecisionEngine()

    def scan(self, prompt: str) -> PromptScanOutcome:
        text = prompt.strip()
        findings = self._run_detectors(text)
        findings = self._dedupe(findings)
        risk_score, risk_level = score_findings(findings)
        masked = mask_prompt(text)
        return self.decision_engine.decide(
            findings=findings,
            risk_score=risk_score,
            risk_level=risk_level,
            masked_prompt=masked,
        )

    def _run_detectors(self, text: str) -> list[PromptFinding]:
        results: list[PromptFinding] = []
        for detector in self.detectors:
            results.extend(detector.detect(text))
        return results

    @staticmethod
    def _dedupe(findings: list[PromptFinding]) -> list[PromptFinding]:
        seen: set[str] = set()
        unique: list[PromptFinding] = []
        for f in findings:
            key = f"{f.finding_type}:{f.message}"
            if key in seen:
                continue
            seen.add(key)
            unique.append(f)
        return unique
